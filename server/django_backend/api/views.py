import json
from datetime import datetime
import os
import urllib.request
import uuid
import csv
import sqlite3
import re
from io import StringIO
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import bcrypt

from .authz import ROLE_PERMISSIONS, require_auth, require_role
from .db import fetch_one, fetch_all, execute, get_conn


def _json_body(request):
    if not request.body:
        return {}
    return json.loads(request.body.decode("utf-8"))


ALLOWED_URGENCY = {"紧急", "一般", "常规"}
ALLOWED_STATUS = {"待接单", "已接单", "出发中", "已到达", "处置中", "已完成"}


def _new_event_id():
    return f"evt_{uuid.uuid4().hex[:16]}"


def _ensure_column(table_name, column_name, column_def):
    cols = fetch_all(f"PRAGMA table_info({table_name})")
    names = {c.get("name") for c in cols}
    if column_name not in names:
        try:
            execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
        except sqlite3.OperationalError as e:
            # Django 自动重载下可能并发执行到这里，重复加列时忽略即可
            if "duplicate column name" not in str(e).lower():
                raise


def _ensure_ops_tables():
    execute(
        """
        CREATE TABLE IF NOT EXISTS notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT,
            channel TEXT,
            recipient TEXT,
            content TEXT,
            status TEXT DEFAULT 'queued',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    execute(
        """
        CREATE TABLE IF NOT EXISTS event_traces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            module TEXT NOT NULL,
            action TEXT NOT NULL,
            payload_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    _ensure_column("alerts", "event_id", "TEXT")
    _ensure_column("orders", "event_id", "TEXT")


def _ensure_elderly_contact_tables():
    execute(
        """
        CREATE TABLE IF NOT EXISTS elderly_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            elderly_id INTEGER NOT NULL,
            relation TEXT,
            name TEXT NOT NULL,
            phone TEXT,
            is_primary INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    execute("CREATE INDEX IF NOT EXISTS idx_elderly_contacts_elderly ON elderly_contacts(elderly_id)")
    execute(
        """
        CREATE TABLE IF NOT EXISTS family_communication (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            elderly_id INTEGER NOT NULL,
            contact_id INTEGER,
            contact_name TEXT,
            contact_phone TEXT,
            communication_type TEXT,
            content TEXT,
            result TEXT,
            next_follow_up TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    _ensure_column("family_communication", "contact_id", "INTEGER")
    _ensure_column("family_communication", "contact_phone", "TEXT")
    _ensure_column("family_communication", "result", "TEXT")
    _ensure_column("family_communication", "next_follow_up", "TEXT")
    _ensure_column("family_communication", "communication_type", "TEXT")


def _trace_event(event_id, module, action, payload=None):
    _ensure_ops_tables()
    execute(
        "INSERT INTO event_traces (event_id, module, action, payload_json) VALUES (?, ?, ?, ?)",
        (event_id, module, action, json.dumps(payload or {}, ensure_ascii=False)),
    )


def _notify(event_id, channel, recipient, content, status="queued"):
    _ensure_ops_tables()
    execute(
        "INSERT INTO notification_logs (event_id, channel, recipient, content, status) VALUES (?, ?, ?, ?, ?)",
        (event_id, channel, recipient, content, status),
    )


def _ensure_elderly_governance_columns():
    _ensure_column("elderly", "grid_area", "TEXT")
    _ensure_column("elderly", "focus_tags", "TEXT")


def _ensure_alert_workflow_columns():
    _ensure_column("alerts", "status", "TEXT DEFAULT '待处理'")
    _ensure_column("alerts", "workflow_stage", "TEXT")
    _ensure_column("alerts", "rectify_measures", "TEXT")
    _ensure_column("alerts", "rectify_at", "TEXT")
    _ensure_column("alerts", "revisit_plan_at", "TEXT")
    _ensure_column("alerts", "revisit_result", "TEXT")
    _ensure_column("alerts", "revisit_at", "TEXT")
    _ensure_column("alerts", "closed_at", "TEXT")
    _ensure_column("alerts", "ai_level", "TEXT")
    _ensure_column("alerts", "ai_confidence", "INTEGER")
    _ensure_column("alerts", "ai_reasons", "TEXT")
    _ensure_column("alerts", "ai_source", "TEXT")
    execute(
        "UPDATE alerts SET workflow_stage = '已完结' WHERE status = '已处理' AND (workflow_stage IS NULL OR TRIM(workflow_stage) = '')"
    )
    execute(
        "UPDATE alerts SET workflow_stage = '待响应' WHERE workflow_stage IS NULL OR TRIM(workflow_stage) = ''"
    )


def _alert_workflow_effective_stage(row):
    if not row:
        return "待响应"
    ws = (row.get("workflow_stage") or "").strip()
    if ws:
        return ws
    return "已完结" if (row.get("status") or "") == "已处理" else "待响应"


def _triage_level_weight(level_text):
    return {"紧急": 3, "警告": 2, "提示": 1}.get(level_text, 1)


def _rule_triage_decision(inputs):
    hr = float(inputs.get("heart_rate") or 0)
    bp_high = float(inputs.get("blood_pressure_high") or 0)
    bp_low = float(inputs.get("blood_pressure_low") or 0)
    spo2 = float(inputs.get("blood_oxygen") or 0)
    risk_level = str(inputs.get("risk_level") or "")
    active_alerts = int(inputs.get("active_alerts") or 0)
    symptoms = inputs.get("symptoms") or []

    reasons = []
    if hr >= 120:
        reasons.append("心率>=120")
    elif hr >= 105:
        reasons.append("心率>=105")
    if bp_high >= 170 or bp_low >= 105:
        reasons.append("血压重度异常")
    elif bp_high >= 150 or bp_low >= 95:
        reasons.append("血压偏高")
    if spo2 and spo2 < 90:
        reasons.append("血氧<90%")
    elif spo2 and spo2 < 94:
        reasons.append("血氧偏低")
    if active_alerts >= 2:
        reasons.append("存在多条未闭环预警")
    if "高" in risk_level:
        reasons.append("档案高风险人群")
    if symptoms:
        reasons.append(f"症状提示:{'、'.join([str(x) for x in symptoms[:3]])}")

    if hr >= 120 or bp_high >= 170 or bp_low >= 105 or (spo2 and spo2 < 90):
        level = "紧急"
        confidence = 88
    elif hr >= 105 or bp_high >= 150 or bp_low >= 95 or (spo2 and spo2 < 94) or active_alerts >= 2:
        level = "警告"
        confidence = 76
    else:
        level = "提示"
        confidence = 63
    return {"level": level, "confidence": confidence, "reasons": reasons[:5], "source": "rule"}


def _ai_triage_decision(inputs):
    rule = _rule_triage_decision(inputs)
    llm = _call_llm_json(
        "你是社区健康告警分级助手。仅输出JSON。",
        (
            "请根据输入做告警分级。"
            "输出JSON格式:"
            "{\"level\":\"紧急|警告|提示\",\"confidence\":1-99,\"reasons\":[\"...\"],\"summary\":\"...\"}\n"
            f"输入:{json.dumps(inputs, ensure_ascii=False)}\n"
            f"规则建议:{json.dumps(rule, ensure_ascii=False)}"
        ),
    )
    if isinstance(llm, dict):
        level = str(llm.get("level") or "")
        if level not in ["紧急", "警告", "提示"]:
            level = rule["level"]
        try:
            confidence = int(llm.get("confidence"))
        except Exception:
            confidence = int(rule["confidence"])
        confidence = max(1, min(99, confidence))
        reasons = llm.get("reasons")
        if not isinstance(reasons, list) or not reasons:
            reasons = rule["reasons"]
        else:
            reasons = [str(x) for x in reasons[:5]]
        return {"level": level, "confidence": confidence, "reasons": reasons, "source": "llm"}
    return rule


def _vitals_auto_alert(elderly_id, hr, bp_high, bp_low, spo2, source_label="", shared_event_id=None, alert_type="体征异常"):
    """体征阈值自动告警。返回 (alert_id 或 None, event_id)。"""
    _ensure_alert_workflow_columns()
    elderly = fetch_one("SELECT name, address, risk_level FROM elderly WHERE id = ?", (elderly_id,))
    if not elderly:
        return None, shared_event_id
    active_row = fetch_one(
        "SELECT COUNT(*) AS c FROM alerts WHERE elderly_id = ? AND IFNULL(TRIM(workflow_stage),'') NOT IN ('已完结','')",
        (elderly_id,),
    )
    triage_inputs = {
        "elderly_id": elderly_id,
        "risk_level": elderly.get("risk_level"),
        "heart_rate": hr,
        "blood_pressure_high": bp_high,
        "blood_pressure_low": bp_low,
        "blood_oxygen": spo2,
        "active_alerts": int((active_row or {}).get("c") or 0),
        "source_label": source_label,
    }
    triage = _ai_triage_decision(triage_inputs)
    level_text = triage.get("level") or "提示"
    alert_level = 1 if level_text == "紧急" else (2 if level_text == "警告" else 3)
    if _triage_level_weight(level_text) < 2:
        return None, shared_event_id

    event_id = shared_event_id or _new_event_id()
    prefix = source_label or "体征监测"
    title = f"{elderly.get('name', '老人')} {prefix}-{level_text}告警"
    reasons = triage.get("reasons") or []
    reason_text = "；".join(reasons) if reasons else "体征异常"
    content = f"{prefix}触发分级：{reason_text}。HR={hr}, BP={bp_high}/{bp_low}, SpO2={spo2}"
    last_id, _ = execute(
        """
        INSERT INTO alerts
        (elderly_id, alert_type, alert_level, title, content, location, event_id, status, workflow_stage, ai_level, ai_confidence, ai_reasons, ai_source)
        VALUES (?, ?, ?, ?, ?, ?, ?, '待处理', '待响应', ?, ?, ?, ?)
        """,
        (
            elderly_id,
            alert_type,
            alert_level,
            title,
            content,
            elderly.get("address"),
            event_id,
            level_text,
            int(triage.get("confidence") or 0),
            json.dumps(reasons, ensure_ascii=False),
            triage.get("source") or "rule",
        ),
    )
    _notify(event_id, "system", "dispatch-center", f"自动告警已触发，alert_id={last_id}", "queued")
    _trace_event(event_id, "alerts", "auto_threshold", {"alert_id": last_id, "elderly_id": elderly_id})
    return last_id, event_id


@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    payload = _json_body(request)
    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        return JsonResponse({"success": False, "message": "用户名和密码不能为空"}, status=400)

    user = fetch_one("SELECT * FROM users WHERE username = ? AND status = 1", (username,))
    if not user:
        return JsonResponse({"success": False, "message": "用户名或密码错误"}, status=401)

    if not bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
        return JsonResponse({"success": False, "message": "用户名或密码错误"}, status=401)

    session_user = {
        "id": user["id"],
        "username": user["username"],
        "realName": user["real_name"],
        "role": user["role"],
        "phone": user.get("phone"),
        "email": user.get("email"),
        "permissions": ROLE_PERMISSIONS.get(user["role"], []),
    }
    request.session["user"] = session_user
    return JsonResponse({"success": True, "message": "登录成功", "data": session_user})


@csrf_exempt
def logout(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    request.session.flush()
    return JsonResponse({"success": True, "message": "已退出登录"})


def current_user(request):
    user = request.session.get("user")
    if not user:
        return JsonResponse({"success": False, "message": "未登录"}, status=401)
    return JsonResponse({"success": True, "data": user})


def permissions(_request):
    return JsonResponse({"success": True, "data": ROLE_PERMISSIONS})


def _resolve_doctor_id_for_user(user):
    if not user:
        return None
    by_user_id = fetch_one(
        "SELECT id FROM doctors WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user.get("id"),),
    )
    if by_user_id and by_user_id.get("id"):
        return by_user_id["id"]
    by_name = fetch_one(
        "SELECT id FROM doctors WHERE name = ? ORDER BY id DESC LIMIT 1",
        (user.get("realName", ""),),
    )
    return by_name.get("id") if by_name else None


@require_auth
def elderly_list(request):
    _ensure_elderly_governance_columns()
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("pageSize", 10))
    keyword = request.GET.get("keyword")
    status = request.GET.get("status")
    risk_level = request.GET.get("riskLevel")
    offset = (page - 1) * page_size

    where_parts = ["1=1"]
    params = []

    if keyword:
        where_parts.append(
            "(name LIKE ? OR phone LIKE ? OR address LIKE ? OR IFNULL(grid_area,'') LIKE ? OR IFNULL(focus_tags,'') LIKE ?)"
        )
        q = f"%{keyword}%"
        params.extend([q, q, q, q, q])

    if status:
        status_map = {
            "健康良好": ["良好", "健康", "健康良好"],
            "需要关注": ["一般", "需要关注"],
            "危重状态": ["较差", "危重状态"],
        }
        values = status_map.get(status, [status])
        where_parts.append(f"health_status IN ({','.join(['?'] * len(values))})")
        params.extend(values)

    if risk_level:
        where_parts.append("risk_level = ?")
        params.append(risk_level)

    where_sql = " AND ".join(where_parts)
    count_row = fetch_one(f"SELECT COUNT(*) AS total FROM elderly WHERE {where_sql}", tuple(params))
    total = count_row["total"] if count_row else 0

    list_sql = f"""
        SELECT * FROM elderly
        WHERE {where_sql}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    rows = fetch_all(list_sql, tuple(params + [page_size, offset]))
    return JsonResponse(
        {
            "success": True,
            "data": {"list": rows, "total": total, "page": page, "pageSize": page_size},
        }
    )


def _elderly_detail(elderly_id):
    _ensure_elderly_contact_tables()
    elderly = fetch_one("SELECT * FROM elderly WHERE id = ?", (elderly_id,))
    if not elderly:
        return JsonResponse({"success": False, "message": "未找到该老人信息"}, status=404)

    health_data = fetch_all(
        "SELECT * FROM health_data WHERE elderly_id = ? ORDER BY recorded_at DESC LIMIT 10",
        (elderly_id,),
    )
    devices = fetch_all("SELECT * FROM devices WHERE elderly_id = ?", (elderly_id,))
    contacts = fetch_all(
        "SELECT id, relation, name, phone, is_primary, created_at FROM elderly_contacts WHERE elderly_id = ? ORDER BY is_primary DESC, id ASC",
        (elderly_id,),
    )
    if not contacts and (elderly.get("emergency_contact") or elderly.get("emergency_phone")):
        contacts = [
            {
                "id": None,
                "relation": "紧急联系人",
                "name": elderly.get("emergency_contact") or "紧急联系人",
                "phone": elderly.get("emergency_phone") or "",
                "is_primary": 1,
                "created_at": None,
            }
        ]
    communications = fetch_all(
        "SELECT * FROM family_communication WHERE elderly_id = ? ORDER BY created_at DESC LIMIT 20",
        (elderly_id,),
    )
    elderly["healthData"] = health_data
    elderly["devices"] = devices
    elderly["contacts"] = contacts
    elderly["communications"] = communications
    return JsonResponse({"success": True, "data": elderly})


@csrf_exempt
@require_auth
@require_role("admin", "service")
def elderly_create(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    payload = _json_body(request)
    _ensure_elderly_contact_tables()
    _ensure_elderly_governance_columns()
    last_id, _ = execute(
        """
        INSERT INTO elderly
        (name, gender, birth_date, id_card, phone, address, emergency_contact, emergency_phone,
         health_status, risk_level, chronic_diseases, allergies, medications, device_id,
         grid_area, focus_tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.get("name"),
            payload.get("gender"),
            payload.get("birth_date"),
            payload.get("id_card"),
            payload.get("phone"),
            payload.get("address"),
            payload.get("emergency_contact"),
            payload.get("emergency_phone"),
            payload.get("health_status", "良好"),
            payload.get("risk_level", "低风险"),
            payload.get("chronic_diseases"),
            payload.get("allergies"),
            payload.get("medications"),
            payload.get("device_id"),
            payload.get("grid_area"),
            payload.get("focus_tags"),
        ),
    )
    contacts = payload.get("contacts") if isinstance(payload.get("contacts"), list) else []
    for idx, item in enumerate(contacts):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        execute(
            "INSERT INTO elderly_contacts (elderly_id, relation, name, phone, is_primary) VALUES (?, ?, ?, ?, ?)",
            (
                last_id,
                str(item.get("relation") or "").strip() or "家属",
                name,
                str(item.get("phone") or "").strip(),
                1 if idx == 0 else 0,
            ),
        )
    return JsonResponse({"success": True, "message": "添加成功", "data": {"id": last_id}})


def _elderly_update(payload, elderly_id):
    _ensure_elderly_contact_tables()
    _ensure_elderly_governance_columns()
    execute(
        """
        UPDATE elderly SET
            name = ?, gender = ?, birth_date = ?, id_card = ?, phone = ?, address = ?,
            emergency_contact = ?, emergency_phone = ?, health_status = ?,
            risk_level = ?, chronic_diseases = ?, allergies = ?, medications = ?,
            grid_area = ?, focus_tags = ?
        WHERE id = ?
        """,
        (
            payload.get("name"),
            payload.get("gender"),
            payload.get("birth_date"),
            payload.get("id_card"),
            payload.get("phone"),
            payload.get("address"),
            payload.get("emergency_contact"),
            payload.get("emergency_phone"),
            payload.get("health_status"),
            payload.get("risk_level"),
            payload.get("chronic_diseases"),
            payload.get("allergies"),
            payload.get("medications"),
            payload.get("grid_area"),
            payload.get("focus_tags"),
            elderly_id,
        ),
    )
    if isinstance(payload.get("contacts"), list):
        execute("DELETE FROM elderly_contacts WHERE elderly_id = ?", (elderly_id,))
        for idx, item in enumerate(payload.get("contacts") or []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            execute(
                "INSERT INTO elderly_contacts (elderly_id, relation, name, phone, is_primary) VALUES (?, ?, ?, ?, ?)",
                (
                    elderly_id,
                    str(item.get("relation") or "").strip() or "家属",
                    name,
                    str(item.get("phone") or "").strip(),
                    1 if idx == 0 else 0,
                ),
            )
    return JsonResponse({"success": True, "message": "更新成功"})


def _elderly_delete(elderly_id):
    execute("DELETE FROM elderly WHERE id = ?", (elderly_id,))
    return JsonResponse({"success": True, "message": "删除成功"})


@csrf_exempt
@require_auth
def elderly_item(request, elderly_id):
    if request.method == "GET":
        return _elderly_detail(elderly_id)
    if request.method == "PUT":
        user = request.session.get("user") or {}
        if user.get("role") not in ["admin", "service"]:
            return JsonResponse({"success": False, "message": "权限不足"}, status=403)
        return _elderly_update(_json_body(request), elderly_id)
    if request.method == "DELETE":
        user = request.session.get("user") or {}
        if user.get("role") != "admin":
            return JsonResponse({"success": False, "message": "权限不足"}, status=403)
        return _elderly_delete(elderly_id)
    return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)


@csrf_exempt
@require_auth
def elderly_contacts(request, elderly_id):
    _ensure_elderly_contact_tables()
    if request.method == "GET":
        rows = fetch_all(
            "SELECT id, relation, name, phone, is_primary, created_at FROM elderly_contacts WHERE elderly_id = ? ORDER BY is_primary DESC, id ASC",
            (elderly_id,),
        )
        return JsonResponse({"success": True, "data": rows})
    if request.method == "POST":
        user = request.session.get("user") or {}
        if user.get("role") not in ["admin", "service", "nurse"]:
            return JsonResponse({"success": False, "message": "权限不足"}, status=403)
        p = _json_body(request)
        name = str(p.get("name") or "").strip()
        if not name:
            return JsonResponse({"success": False, "message": "联系人姓名不能为空"}, status=400)
        contact_id, _ = execute(
            "INSERT INTO elderly_contacts (elderly_id, relation, name, phone, is_primary) VALUES (?, ?, ?, ?, ?)",
            (
                elderly_id,
                str(p.get("relation") or "").strip() or "家属",
                name,
                str(p.get("phone") or "").strip(),
                1 if bool(p.get("is_primary")) else 0,
            ),
        )
        return JsonResponse({"success": True, "message": "联系人已添加", "data": {"id": contact_id}})
    return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)


@csrf_exempt
@require_auth
@require_role("admin", "service", "doctor", "nurse")
def elderly_communications(request, elderly_id):
    _ensure_elderly_contact_tables()
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    p = _json_body(request)
    contact_id = p.get("contact_id")
    contact = None
    if contact_id:
        contact = fetch_one(
            "SELECT id, relation, name, phone FROM elderly_contacts WHERE id = ? AND elderly_id = ?",
            (contact_id, elderly_id),
        )
        if not contact:
            return JsonResponse({"success": False, "message": "联系人不存在"}, status=404)
    contact_name = (contact or {}).get("name") or str(p.get("contact_name") or "").strip()
    if not contact_name:
        return JsonResponse({"success": False, "message": "请选择或填写沟通对象"}, status=400)
    communication_id, _ = execute(
        """
        INSERT INTO family_communication
        (elderly_id, contact_id, contact_name, contact_phone, communication_type, content, result, next_follow_up)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            elderly_id,
            (contact or {}).get("id"),
            contact_name,
            (contact or {}).get("phone") or str(p.get("contact_phone") or "").strip(),
            str(p.get("communication_type") or "电话沟通").strip(),
            str(p.get("content") or "").strip(),
            str(p.get("result") or "待跟进").strip(),
            str(p.get("next_follow_up") or "").strip(),
        ),
    )
    return JsonResponse({"success": True, "message": "沟通记录已保存", "data": {"id": communication_id}})


@csrf_exempt
@require_auth
@require_role("admin", "doctor", "nurse")
def create_health_data(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    payload = _json_body(request)
    execute(
        """
        INSERT INTO health_data
        (elderly_id, heart_rate, blood_pressure_high, blood_pressure_low, blood_oxygen, temperature, steps, sleep_hours)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.get("elderly_id"),
            payload.get("heart_rate"),
            payload.get("blood_pressure_high"),
            payload.get("blood_pressure_low"),
            payload.get("blood_oxygen"),
            payload.get("temperature"),
            payload.get("steps", 0),
            payload.get("sleep_hours"),
        ),
    )
    auto_id, evt = _vitals_auto_alert(
        payload.get("elderly_id"),
        payload.get("heart_rate"),
        payload.get("blood_pressure_high"),
        payload.get("blood_pressure_low"),
        payload.get("blood_oxygen"),
        source_label="手动录入体征",
        shared_event_id=None,
    )
    return JsonResponse(
        {
            "success": True,
            "message": "健康数据记录成功",
            "data": {"auto_alert_id": auto_id, "event_id": evt},
        }
    )


@require_auth
def alerts_list(request):
    _ensure_alert_workflow_columns()
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("pageSize", 10))
    status = request.GET.get("status")
    alert_type = request.GET.get("alertType")
    workflow_stage = request.GET.get("workflowStage")
    offset = (page - 1) * page_size

    sql = """
        SELECT a.*, e.name AS elderly_name, e.address, e.phone AS elderly_phone
        FROM alerts a
        LEFT JOIN elderly e ON a.elderly_id = e.id
        WHERE 1=1
    """
    params = []
    if status:
        sql += " AND a.status = ?"
        params.append(status)
    if alert_type:
        sql += " AND a.alert_type = ?"
        params.append(alert_type)
    if workflow_stage:
        sql += " AND IFNULL(TRIM(a.workflow_stage), '') = ?"
        params.append(workflow_stage)

    count_row = fetch_one(sql.replace("SELECT a.*", "SELECT COUNT(*) AS total"), tuple(params))
    total = count_row["total"] if count_row else 0
    sql += " ORDER BY a.created_at DESC LIMIT ? OFFSET ?"
    rows = fetch_all(sql, tuple(params + [page_size, offset]))
    return JsonResponse({"success": True, "data": {"list": rows, "total": total, "page": page, "pageSize": page_size}})


@require_auth
def alerts_statistics(_request):
    _ensure_alert_workflow_columns()
    status_count = fetch_all("SELECT status, COUNT(*) AS count FROM alerts GROUP BY status")
    workflow_count = fetch_all("SELECT workflow_stage AS workflow_stage, COUNT(*) AS count FROM alerts GROUP BY workflow_stage")
    type_count = fetch_all(
        "SELECT alert_type, COUNT(*) AS count FROM alerts WHERE date(created_at) = date('now', 'localtime') GROUP BY alert_type"
    )
    avg_row = fetch_one(
        "SELECT AVG((julianday(handle_time) - julianday(created_at)) * 24 * 60) AS avg_time FROM alerts WHERE handle_time IS NOT NULL"
    )
    overdue_row = fetch_one(
        """
        SELECT COUNT(*) AS count FROM alerts
        WHERE IFNULL(TRIM(workflow_stage), '') NOT IN ('已完结','')
            AND datetime(created_at) < datetime('now', '-24 hours', 'localtime')
        """
    )
    return JsonResponse(
        {
            "success": True,
            "data": {
                "statusCount": status_count,
                "workflowCount": workflow_count,
                "typeCount": type_count,
                "avgResponseTime": (avg_row or {}).get("avg_time") or 0,
                "overdueUnclosed": (overdue_row or {}).get("count") or 0,
            },
        }
    )


@csrf_exempt
@require_auth
def alerts_create(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    _ensure_ops_tables()
    _ensure_alert_workflow_columns()
    p = _json_body(request)
    event_id = str(p.get("event_id") or _new_event_id())
    elderly_id = p.get("elderly_id")
    elderly = fetch_one("SELECT risk_level FROM elderly WHERE id = ?", (elderly_id,)) if elderly_id else {}
    latest_vital = fetch_one(
        "SELECT heart_rate, blood_pressure_high, blood_pressure_low, blood_oxygen FROM health_data WHERE elderly_id = ? ORDER BY recorded_at DESC LIMIT 1",
        (elderly_id,),
    ) if elderly_id else {}
    active_row = fetch_one(
        "SELECT COUNT(*) AS c FROM alerts WHERE elderly_id = ? AND IFNULL(TRIM(workflow_stage),'') NOT IN ('已完结','')",
        (elderly_id,),
    ) if elderly_id else {"c": 0}
    triage_inputs = {
        "elderly_id": elderly_id,
        "risk_level": (elderly or {}).get("risk_level"),
        "heart_rate": p.get("heart_rate", (latest_vital or {}).get("heart_rate")),
        "blood_pressure_high": p.get("blood_pressure_high", (latest_vital or {}).get("blood_pressure_high")),
        "blood_pressure_low": p.get("blood_pressure_low", (latest_vital or {}).get("blood_pressure_low")),
        "blood_oxygen": p.get("blood_oxygen", (latest_vital or {}).get("blood_oxygen")),
        "active_alerts": int((active_row or {}).get("c") or 0),
        "symptoms": p.get("symptoms") or [],
        "source_label": "手工创建告警",
    }
    triage = _ai_triage_decision(triage_inputs)
    ai_level = triage.get("level") or "提示"
    ai_confidence = int(triage.get("confidence") or 0)
    ai_reasons = json.dumps((triage.get("reasons") or [])[:5], ensure_ascii=False)
    ai_source = triage.get("source") or "rule"
    fallback_level = 1 if ai_level == "紧急" else (2 if ai_level == "警告" else 3)
    last_id, _ = execute(
        """
        INSERT INTO alerts
        (elderly_id, alert_type, alert_level, title, content, location, event_id, status, workflow_stage, ai_level, ai_confidence, ai_reasons, ai_source)
        VALUES (?, ?, ?, ?, ?, ?, ?, '待处理', '待响应', ?, ?, ?, ?)
        """,
        (
            elderly_id,
            p.get("alert_type"),
            p.get("alert_level", fallback_level),
            p.get("title"),
            p.get("content"),
            p.get("location"),
            event_id,
            ai_level,
            ai_confidence,
            ai_reasons,
            ai_source,
        ),
    )
    _trace_event(event_id, "alerts", "create", {"alert_id": last_id, "title": p.get("title")})
    _notify(event_id, "system", "dispatch-center", f"新告警：{p.get('title')}", "queued")
    return JsonResponse(
        {
            "success": True,
            "message": "警报创建成功",
            "data": {"id": last_id, "event_id": event_id, "ai_level": ai_level, "ai_confidence": ai_confidence},
        }
    )


@csrf_exempt
@require_auth
def alerts_triage(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    p = _json_body(request)
    elderly_id = p.get("elderly_id")
    elderly = fetch_one("SELECT risk_level FROM elderly WHERE id = ?", (elderly_id,)) if elderly_id else {}
    active_row = fetch_one(
        "SELECT COUNT(*) AS c FROM alerts WHERE elderly_id = ? AND IFNULL(TRIM(workflow_stage),'') NOT IN ('已完结','')",
        (elderly_id,),
    ) if elderly_id else {"c": 0}
    triage_inputs = {
        "elderly_id": elderly_id,
        "risk_level": p.get("risk_level", (elderly or {}).get("risk_level")),
        "heart_rate": p.get("heart_rate"),
        "blood_pressure_high": p.get("blood_pressure_high"),
        "blood_pressure_low": p.get("blood_pressure_low"),
        "blood_oxygen": p.get("blood_oxygen"),
        "active_alerts": int((active_row or {}).get("c") or 0),
        "symptoms": p.get("symptoms") or [],
        "source_label": p.get("source_label") or "外部请求",
    }
    triage = _ai_triage_decision(triage_inputs)
    return JsonResponse({"success": True, "data": triage})


@csrf_exempt
@require_auth
def alerts_handle(request, alert_id):
    if request.method != "PUT":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    p = _json_body(request)
    _ensure_alert_workflow_columns()
    current = fetch_one("SELECT event_id, title FROM alerts WHERE id = ?", (alert_id,))
    res = str(p.get("handle_result") or "").strip() or "已现场处置"
    execute(
        """
        UPDATE alerts SET status = '已处理', workflow_stage = '已完结',
            handler_id = ?, handle_time = datetime('now', 'localtime'), handle_result = ?,
            revisit_result = ?, closed_at = datetime('now', 'localtime'), revisit_at = datetime('now', 'localtime')
        WHERE id = ?
        """,
        (request.session["user"]["id"], res, res, alert_id),
    )
    if current and current.get("event_id"):
        _trace_event(current["event_id"], "alerts", "handle", {"alert_id": alert_id, "result": p.get("handle_result")})
    return JsonResponse({"success": True, "message": "处理成功"})


@csrf_exempt
@require_auth
def alerts_workflow(request, alert_id):
    """闭环：接单→整改→回访完结。action: start | rectify | finish"""
    if request.method != "PUT":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    _ensure_alert_workflow_columns()
    user = request.session.get("user") or {}
    if user.get("role") not in ["admin", "service", "nurse", "doctor"]:
        return JsonResponse({"success": False, "message": "权限不足"}, status=403)
    p = _json_body(request)
    action = str(p.get("action") or "").strip()
    row = fetch_one("SELECT * FROM alerts WHERE id = ?", (alert_id,))
    if not row:
        return JsonResponse({"success": False, "message": "警报不存在"}, status=404)
    ws = _alert_workflow_effective_stage(row)

    if action == "start":
        if ws != "待响应":
            return JsonResponse({"success": False, "message": f"当前环节不可接单：{ws}"}, status=400)
        execute(
            """
            UPDATE alerts SET workflow_stage = '处置中', handler_id = ?, handle_time = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (user["id"], alert_id),
        )
        if row.get("event_id"):
            _trace_event(row["event_id"], "alerts", "workflow_start", {"alert_id": alert_id})
    elif action == "rectify":
        measures = str(p.get("rectify_measures") or "").strip()
        if not measures:
            return JsonResponse({"success": False, "message": "请填写整改措施"}, status=400)
        if ws not in ("待响应", "处置中"):
            return JsonResponse({"success": False, "message": f"当前环节不可提交整改：{ws}"}, status=400)
        revisit_plan = str(p.get("revisit_plan_at") or "").strip()
        execute(
            """
            UPDATE alerts SET workflow_stage = '待回访', rectify_measures = ?, rectify_at = datetime('now', 'localtime'),
                revisit_plan_at = ?
            WHERE id = ?
            """,
            (measures, revisit_plan or None, alert_id),
        )
        if row.get("event_id"):
            _trace_event(row["event_id"], "alerts", "workflow_rectify", {"alert_id": alert_id})
    elif action == "finish":
        revisit_result = str(p.get("revisit_result") or "").strip()
        if not revisit_result:
            return JsonResponse({"success": False, "message": "请填写回访结论"}, status=400)
        if ws != "待回访":
            return JsonResponse({"success": False, "message": f"当前环节不可完结：{ws}"}, status=400)
        execute(
            """
            UPDATE alerts SET workflow_stage = '已完结', status = '已处理',
                revisit_result = ?, revisit_at = datetime('now', 'localtime'), closed_at = datetime('now', 'localtime'),
                handler_id = ?, handle_time = datetime('now', 'localtime'), handle_result = ?
            WHERE id = ?
            """,
            (revisit_result, user["id"], revisit_result, alert_id),
        )
        if row.get("event_id"):
            _trace_event(row["event_id"], "alerts", "workflow_finish", {"alert_id": alert_id})
    else:
        return JsonResponse({"success": False, "message": "无效 action，支持 start / rectify / finish"}, status=400)
    return JsonResponse({"success": True, "message": "环节已更新"})


@require_auth
def orders_list(request):
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("pageSize", 10))
    status = request.GET.get("status")
    offset = (page - 1) * page_size
    user = request.session.get("user") or {}

    sql = """
        SELECT o.*, e.name AS elderly_name, e.address, e.phone AS elderly_phone,
               d.name AS doctor_name, d.phone AS doctor_phone
        FROM orders o
        LEFT JOIN elderly e ON o.elderly_id = e.id
        LEFT JOIN doctors d ON o.doctor_id = d.id
        WHERE 1=1
    """
    params = []
    if status:
        sql += " AND o.status = ?"
        params.append(status)
    if user.get("role") == "doctor":
        doctor_id = _resolve_doctor_id_for_user(user)
        if not doctor_id:
            return JsonResponse({"success": True, "data": {"list": [], "total": 0, "page": page, "pageSize": page_size}})
        sql += " AND o.doctor_id = ?"
        params.append(doctor_id)

    count_row = fetch_one(sql.replace("SELECT o.*", "SELECT COUNT(*) AS total"), tuple(params))
    total = count_row["total"] if count_row else 0
    sql += " ORDER BY o.created_at DESC LIMIT ? OFFSET ?"
    rows = fetch_all(sql, tuple(params + [page_size, offset]))
    return JsonResponse({"success": True, "data": {"list": rows, "total": total, "page": page, "pageSize": page_size}})


@csrf_exempt
@require_auth
def orders_create(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    user = request.session.get("user") or {}
    if user.get("role") not in ["admin", "service"]:
        return JsonResponse({"success": False, "message": "当前账号无派医权限"}, status=403)
    _ensure_ops_tables()
    p = _json_body(request)
    event_id = str(p.get("event_id") or _new_event_id())
    order_no = f"ORD{__import__('time').time_ns()}"
    execute(
        "INSERT INTO orders (order_no, elderly_id, alert_id, doctor_id, urgency, description, event_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            order_no,
            p.get("elderly_id"),
            p.get("alert_id"),
            p.get("doctor_id"),
            p.get("urgency") if p.get("urgency") in ALLOWED_URGENCY else "一般",
            p.get("description"),
            event_id,
        ),
    )
    inserted = fetch_one("SELECT id FROM orders WHERE order_no = ?", (order_no,))
    _trace_event(event_id, "orders", "create", {"order_id": (inserted or {}).get("id"), "order_no": order_no})
    _notify(event_id, "system", f"doctor:{p.get('doctor_id')}", f"新工单：{order_no}", "queued")
    return JsonResponse({"success": True, "message": "工单创建成功", "data": {"id": (inserted or {}).get("id"), "order_no": order_no, "event_id": event_id}})


@csrf_exempt
@require_auth
def orders_update_status(request, order_id):
    if request.method != "PUT":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    p = _json_body(request)
    status = p.get("status")
    current = fetch_one("SELECT * FROM orders WHERE id = ?", (order_id,))
    if not current:
        return JsonResponse({"success": False, "message": "工单不存在"}, status=404)
    user = request.session.get("user") or {}
    if user.get("role") == "doctor":
        doctor_id = _resolve_doctor_id_for_user(user)
        if not doctor_id or int(current.get("doctor_id") or 0) != int(doctor_id):
            return JsonResponse({"success": False, "message": "仅可操作本人负责工单"}, status=403)
        if status not in ["已接单", "出发中", "已到达", "处置中", "已完成"]:
            return JsonResponse({"success": False, "message": "当前账号无此状态操作权限"}, status=403)
    elif user.get("role") not in ["admin", "service"]:
        return JsonResponse({"success": False, "message": "当前账号无工单操作权限"}, status=403)
    if status not in ALLOWED_STATUS:
        return JsonResponse({"success": False, "message": "无效的工单状态"}, status=400)

    sql = "UPDATE orders SET status = ?"
    params = [status]
    if status == "已接单":
        sql += ", accept_time = datetime('now', 'localtime')"
    elif status == "已到达":
        sql += ", arrive_time = datetime('now', 'localtime')"
    elif status == "已完成":
        sql += ", complete_time = datetime('now', 'localtime')"
    sql += " WHERE id = ?"
    params.append(order_id)
    execute(sql, tuple(params))
    order_event = fetch_one("SELECT event_id FROM orders WHERE id = ?", (order_id,))
    if order_event and order_event.get("event_id"):
        _trace_event(order_event["event_id"], "orders", "status", {"order_id": order_id, "status": status})
    if status == "已完成":
        order = fetch_one("SELECT doctor_id FROM orders WHERE id = ?", (order_id,))
        if order and order.get("doctor_id"):
            execute("UPDATE doctors SET status = '在线' WHERE id = ?", (order["doctor_id"],))
    return JsonResponse({"success": True, "message": "状态更新成功"})


@csrf_exempt
@require_auth
def orders_complete(request, order_id):
    if request.method != "PUT":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    p = _json_body(request)
    current = fetch_one("SELECT * FROM orders WHERE id = ?", (order_id,))
    if not current:
        return JsonResponse({"success": False, "message": "工单不存在"}, status=404)
    user = request.session.get("user") or {}
    if user.get("role") == "doctor":
        doctor_id = _resolve_doctor_id_for_user(user)
        if not doctor_id or int(current.get("doctor_id") or 0) != int(doctor_id):
            return JsonResponse({"success": False, "message": "仅可完成本人负责工单"}, status=403)
    elif user.get("role") not in ["admin", "service"]:
        return JsonResponse({"success": False, "message": "当前账号无工单完成权限"}, status=403)

    execute(
        "UPDATE orders SET status = '已完成', complete_time = datetime('now', 'localtime'), result = ? WHERE id = ?",
        (p.get("result"), order_id),
    )
    order_event = fetch_one("SELECT event_id FROM orders WHERE id = ?", (order_id,))
    if order_event and order_event.get("event_id"):
        _trace_event(order_event["event_id"], "orders", "complete", {"order_id": order_id, "result": p.get("result")})
    order = fetch_one("SELECT doctor_id FROM orders WHERE id = ?", (order_id,))
    if order and order.get("doctor_id"):
        execute("UPDATE doctors SET status = '在线' WHERE id = ?", (order["doctor_id"],))
    return JsonResponse({"success": True, "message": "工单完成"})


@require_auth
def devices_list(request):
    status = request.GET.get("status")
    sql = """
        SELECT d.*, e.name AS elderly_name, e.address
        FROM devices d
        LEFT JOIN elderly e ON d.elderly_id = e.id
        WHERE 1=1
    """
    params = []
    if status:
        sql += " AND d.status = ?"
        params.append(status)
    sql += " ORDER BY d.last_online_at DESC"
    return JsonResponse({"success": True, "data": fetch_all(sql, tuple(params))})


@require_auth
def devices_detail(_request, device_id):
    row = fetch_one(
        "SELECT d.*, e.name AS elderly_name, e.address FROM devices d LEFT JOIN elderly e ON d.elderly_id = e.id WHERE d.id = ?",
        (device_id,),
    )
    if not row:
        return JsonResponse({"success": False, "message": "未找到设备信息"}, status=404)
    return JsonResponse({"success": True, "data": row})


@csrf_exempt
@require_auth
@require_role("admin", "nurse")
def devices_create(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    p = _json_body(request)
    execute(
        "INSERT INTO devices (device_id, elderly_id, device_type, status, battery_level, last_online_at) VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))",
        (p.get("device_id"), p.get("elderly_id"), p.get("device_type", "手表"), p.get("status", "离线"), p.get("battery_level", 100)),
    )
    inserted = fetch_one("SELECT id FROM devices WHERE device_id = ?", (p.get("device_id"),))
    return JsonResponse({"success": True, "message": "设备创建成功", "data": {"id": (inserted or {}).get("id")}})


@csrf_exempt
@require_auth
def devices_item(request, device_id):
    if request.method == "GET":
        return devices_detail(request, device_id)
    if request.method == "PUT":
        user = request.session.get("user") or {}
        if user.get("role") not in ["admin", "nurse"]:
            return JsonResponse({"success": False, "message": "权限不足"}, status=403)
        p = _json_body(request)
        execute(
            "UPDATE devices SET device_id = ?, elderly_id = ?, device_type = ?, status = ?, battery_level = ?, last_online_at = datetime('now', 'localtime') WHERE id = ?",
            (p.get("device_id"), p.get("elderly_id"), p.get("device_type", "手表"), p.get("status", "离线"), p.get("battery_level", 100), device_id),
        )
        return JsonResponse({"success": True, "message": "设备信息更新成功"})
    if request.method == "DELETE":
        user = request.session.get("user") or {}
        if user.get("role") != "admin":
            return JsonResponse({"success": False, "message": "权限不足"}, status=403)
        execute("DELETE FROM devices WHERE id = ?", (device_id,))
        return JsonResponse({"success": True, "message": "设备删除成功"})
    return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)


@require_auth
def devices_statistics(_request):
    status_count = fetch_all("SELECT status, COUNT(*) AS count FROM devices GROUP BY status")
    low_battery = fetch_one("SELECT COUNT(*) AS count FROM devices WHERE battery_level < 20")
    offline = fetch_one("SELECT COUNT(*) AS count FROM devices WHERE status = '离线' OR last_online_at < datetime('now', '-1 hour', 'localtime')")
    return JsonResponse(
        {
            "success": True,
            "data": {
                "statusCount": status_count,
                "lowBatteryCount": (low_battery or {}).get("count", 0),
                "offlineCount": (offline or {}).get("count", 0),
            },
        }
    )


@csrf_exempt
@require_auth
@require_role("admin", "nurse")
def devices_update_status(request, device_id):
    if request.method != "PUT":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    p = _json_body(request)
    sql = "UPDATE devices SET last_online_at = datetime('now', 'localtime')"
    params = []
    if "status" in p:
        sql += ", status = ?"
        params.append(p.get("status"))
    if "battery_level" in p:
        sql += ", battery_level = ?"
        params.append(p.get("battery_level"))
    sql += " WHERE id = ?"
    params.append(device_id)
    execute(sql, tuple(params))
    return JsonResponse({"success": True, "message": "设备状态更新成功"})


@csrf_exempt
@require_auth
@require_role("admin", "nurse", "doctor")
def devices_telemetry(request, device_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    p = _json_body(request)
    _ensure_ops_tables()
    device = fetch_one("SELECT * FROM devices WHERE id = ? OR device_id = ? LIMIT 1", (device_id, str(device_id)))
    if not device:
        return JsonResponse({"success": False, "message": "设备不存在"}, status=404)
    elderly_id = device.get("elderly_id")
    if not elderly_id:
        return JsonResponse({"success": False, "message": "设备未绑定老人"}, status=400)

    event_id = _new_event_id()
    execute(
        """
        INSERT INTO health_data (elderly_id, heart_rate, blood_pressure_high, blood_pressure_low, blood_oxygen, temperature, steps, sleep_hours)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            elderly_id,
            p.get("heart_rate"),
            p.get("blood_pressure_high"),
            p.get("blood_pressure_low"),
            p.get("blood_oxygen"),
            p.get("temperature"),
            p.get("steps", 0),
            p.get("sleep_hours"),
        ),
    )

    auto_alert_id, _ = _vitals_auto_alert(
        elderly_id,
        p.get("heart_rate"),
        p.get("blood_pressure_high"),
        p.get("blood_pressure_low"),
        p.get("blood_oxygen"),
        source_label=f"设备{device.get('device_id')}",
        shared_event_id=event_id,
        alert_type="设备异常",
    )

    _trace_event(event_id, "devices", "telemetry", {"device_id": device.get("device_id"), "elderly_id": elderly_id, "auto_alert_id": auto_alert_id})
    return JsonResponse(
        {
            "success": True,
            "message": "遥测数据已入库",
            "data": {"event_id": event_id, "auto_alert_id": auto_alert_id},
        }
    )


@require_auth
def doctors_list(request):
    status = request.GET.get("status")
    sql = """
        SELECT d.*
        FROM doctors d
        INNER JOIN (
            SELECT MAX(id) AS id FROM doctors GROUP BY name, phone
        ) latest ON latest.id = d.id
        WHERE 1=1
    """
    params = []
    if status:
        sql += " AND d.status = ?"
        params.append(status)
    sql += " ORDER BY d.rating DESC"
    return JsonResponse({"success": True, "data": fetch_all(sql, tuple(params))})


@require_auth
def doctors_detail(_request, doctor_id):
    row = fetch_one("SELECT * FROM doctors WHERE id = ?", (doctor_id,))
    if not row:
        return JsonResponse({"success": False, "message": "未找到医生信息"}, status=404)
    return JsonResponse({"success": True, "data": row})


@csrf_exempt
@require_auth
@require_role("admin")
def doctors_create(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    p = _json_body(request)
    execute(
        "INSERT INTO doctors (name, gender, phone, specialization, hospital, status, current_location, rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (p.get("name"), p.get("gender"), p.get("phone"), p.get("specialization"), p.get("hospital"), p.get("status", "离线"), p.get("current_location"), p.get("rating", 5)),
    )
    inserted = fetch_one("SELECT id FROM doctors WHERE name = ? AND phone = ? ORDER BY id DESC LIMIT 1", (p.get("name"), p.get("phone")))
    return JsonResponse({"success": True, "message": "医生创建成功", "data": {"id": (inserted or {}).get("id")}})


@csrf_exempt
@require_auth
def doctors_item(request, doctor_id):
    user = request.session.get("user") or {}
    if request.method == "GET":
        return doctors_detail(request, doctor_id)
    if request.method == "PUT":
        if user.get("role") != "admin":
            return JsonResponse({"success": False, "message": "权限不足"}, status=403)
        p = _json_body(request)
        execute(
            "UPDATE doctors SET name = ?, gender = ?, phone = ?, specialization = ?, hospital = ?, status = ?, current_location = ?, rating = ? WHERE id = ?",
            (p.get("name"), p.get("gender"), p.get("phone"), p.get("specialization"), p.get("hospital"), p.get("status", "离线"), p.get("current_location"), p.get("rating", 5), doctor_id),
        )
        return JsonResponse({"success": True, "message": "医生信息更新成功"})
    if request.method == "DELETE":
        if user.get("role") != "admin":
            return JsonResponse({"success": False, "message": "权限不足"}, status=403)
        execute("DELETE FROM doctors WHERE id = ?", (doctor_id,))
        return JsonResponse({"success": True, "message": "医生删除成功"})
    return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)


@csrf_exempt
@require_auth
@require_role("admin", "doctor")
def doctors_update_status(request, doctor_id):
    if request.method != "PUT":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    p = _json_body(request)
    sql = "UPDATE doctors SET status = ?"
    params = [p.get("status")]
    if p.get("current_location"):
        sql += ", current_location = ?"
        params.append(p.get("current_location"))
    sql += " WHERE id = ?"
    params.append(doctor_id)
    execute(sql, tuple(params))
    return JsonResponse({"success": True, "message": "医生状态更新成功"})


@require_auth
def visits_list(request):
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("pageSize", 10))
    status = request.GET.get("status")
    date = request.GET.get("date")
    offset = (page - 1) * page_size
    sql = """
        SELECT v.*, e.name AS elderly_name, e.address, e.phone AS elderly_phone, u.real_name AS nurse_name
        FROM visits v
        LEFT JOIN elderly e ON v.elderly_id = e.id
        LEFT JOIN users u ON v.nurse_id = u.id
        WHERE 1=1
    """
    params = []
    if status:
        sql += " AND v.status = ?"
        params.append(status)
    if date:
        sql += " AND v.plan_date = ?"
        params.append(date)
    count_row = fetch_one(sql.replace("SELECT v.*", "SELECT COUNT(*) AS total"), tuple(params))
    total = count_row["total"] if count_row else 0
    sql += " ORDER BY v.plan_date ASC, v.plan_time ASC LIMIT ? OFFSET ?"
    rows = fetch_all(sql, tuple(params + [page_size, offset]))
    return JsonResponse({"success": True, "data": {"list": rows, "total": total, "page": page, "pageSize": page_size}})


@csrf_exempt
@require_auth
@require_role("admin", "nurse")
def visits_create(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    p = _json_body(request)
    last_id, _ = execute(
        "INSERT INTO visits (elderly_id, nurse_id, plan_date, plan_time, visit_content) VALUES (?, ?, ?, ?, ?)",
        (p.get("elderly_id"), p.get("nurse_id") or (request.session.get("user") or {}).get("id"), p.get("plan_date"), p.get("plan_time"), p.get("visit_content")),
    )
    return JsonResponse({"success": True, "message": "巡访计划创建成功", "data": {"id": last_id}})


@csrf_exempt
@require_auth
@require_role("admin", "nurse")
def visits_complete(request, visit_id):
    if request.method != "PUT":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    p = _json_body(request)
    execute(
        """
        UPDATE visits SET status = '已完成', actual_time = datetime('now', 'localtime'),
            health_check = ?, medication_check = ?, needs_feedback = ?, next_visit_date = ?
        WHERE id = ?
        """,
        (p.get("health_check"), p.get("medication_check"), p.get("needs_feedback"), p.get("next_visit_date"), visit_id),
    )
    return JsonResponse({"success": True, "message": "巡访完成"})


@require_auth
def dashboard_overview(_request):
    _ensure_alert_workflow_columns()
    elderly_count = fetch_one("SELECT COUNT(*) AS count FROM elderly")
    alert_count = fetch_one(
        "SELECT COUNT(*) AS count FROM alerts WHERE IFNULL(TRIM(workflow_stage), '') NOT IN ('已完结', '')"
    )
    order_count = fetch_one("SELECT COUNT(*) AS count FROM orders WHERE status IN ('待接单', '已接单', '出发中', '已到达', '处置中')")
    doctor_online = fetch_one("SELECT COUNT(*) AS count FROM doctors WHERE status = '在线'")
    alerts_by_level = fetch_all("SELECT alert_type, COUNT(*) AS count FROM alerts WHERE date(created_at) = date('now', 'localtime') GROUP BY alert_type")
    recent_alerts = fetch_all(
        """
        SELECT a.*, e.name AS elderly_name FROM alerts a
        LEFT JOIN elderly e ON a.elderly_id = e.id
        WHERE IFNULL(TRIM(a.workflow_stage), '') NOT IN ('已完结', '')
        ORDER BY a.created_at DESC LIMIT 5
        """
    )
    pending_orders = fetch_all(
        "SELECT o.*, e.name AS elderly_name, e.address FROM orders o LEFT JOIN elderly e ON o.elderly_id = e.id WHERE o.status IN ('待接单', '已接单') ORDER BY o.created_at DESC LIMIT 5"
    )
    device_stats = fetch_one(
        "SELECT COUNT(*) AS total, SUM(CASE WHEN status = '在线' THEN 1 ELSE 0 END) AS online, SUM(CASE WHEN battery_level < 20 THEN 1 ELSE 0 END) AS low_battery FROM devices"
    )
    return JsonResponse(
        {
            "success": True,
            "data": {
                "elderlyCount": (elderly_count or {}).get("count", 0),
                "alertCount": (alert_count or {}).get("count", 0),
                "orderCount": (order_count or {}).get("count", 0),
                "doctorOnline": (doctor_online or {}).get("count", 0),
                "alertsByLevel": alerts_by_level,
                "recentAlerts": recent_alerts,
                "pendingOrders": pending_orders,
                "deviceStats": device_stats or {},
            },
        }
    )


@require_auth
def dashboard_trend(request):
    days = request.GET.get("days", 7)
    order_trend = fetch_all(
        "SELECT date(created_at) AS date, COUNT(*) AS count FROM orders WHERE created_at >= date('now', '-' || ? || ' days', 'localtime') GROUP BY date(created_at) ORDER BY date",
        (days,),
    )
    alert_trend = fetch_all(
        "SELECT date(created_at) AS date, COUNT(*) AS count FROM alerts WHERE created_at >= date('now', '-' || ? || ' days', 'localtime') GROUP BY date(created_at) ORDER BY date",
        (days,),
    )
    return JsonResponse({"success": True, "data": {"orderTrend": order_trend, "alertTrend": alert_trend}})


@require_auth
def reports_overview(request):
    _ensure_alert_workflow_columns()
    _ensure_elderly_governance_columns()
    days = int(request.GET.get("days", 30))
    orders = fetch_all(
        "SELECT id, status, created_at, elderly_id FROM orders WHERE created_at >= date('now', '-' || ? || ' days', 'localtime')",
        (days,),
    )
    alerts = fetch_all(
        "SELECT id, status, workflow_stage, alert_level, created_at, elderly_id FROM alerts WHERE created_at >= date('now', '-' || ? || ' days', 'localtime')",
        (days,),
    )
    doctors = fetch_all("SELECT id, status, name, rating FROM doctors")
    elderly = fetch_all(
        "SELECT id, name, gender, birth_date, risk_level, chronic_diseases, address, grid_area, focus_tags FROM elderly"
    )

    checks = len(orders)
    rescues = len([o for o in orders if o.get("status") in ["已到达", "处置中", "已完成"]])
    handled_alert = len(
        [
            a
            for a in alerts
            if (a.get("status") == "已处理") or ((a.get("workflow_stage") or "").strip() == "已完结")
        ]
    )
    alert_rate = round((handled_alert / len(alerts)) * 100) if alerts else 100
    complete_rate = round((len([o for o in orders if o.get("status") == "已完成"]) / checks) * 100) if checks else 0

    return JsonResponse(
        {
            "success": True,
            "data": {
                "days": days,
                "stats": {
                    "checks": checks,
                    "rescues": rescues,
                    "alertHandleRate": alert_rate,
                    "orderCompleteRate": complete_rate,
                },
                "orders": orders,
                "alerts": alerts,
                "doctors": doctors,
                "elderlyList": elderly,
            },
        }
    )


@require_auth
def reports_export_csv(request):
    days = int(request.GET.get("days", 30))
    overview = reports_overview(request)
    payload = json.loads(overview.content.decode("utf-8"))
    data = payload.get("data", {})
    elderly_list = data.get("elderlyList", [])
    alerts = data.get("alerts", [])

    pending_alert_by_id = {}
    for a in alerts:
        if (a.get("status") == "已处理") or ((a.get("workflow_stage") or "").strip() == "已完结"):
            continue
        e_id = a.get("elderly_id")
        if not e_id:
            continue
        pending_alert_by_id[e_id] = pending_alert_by_id.get(e_id, 0) + 1

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["姓名", "性别", "出生日期", "片区", "重点标签", "风险等级", "未闭环告警", "慢病", "地址"])
    for e in elderly_list:
        writer.writerow(
            [
                e.get("name", ""),
                e.get("gender", ""),
                e.get("birth_date", ""),
                e.get("grid_area", ""),
                e.get("focus_tags", ""),
                e.get("risk_level", ""),
                pending_alert_by_id.get(e.get("id"), 0),
                e.get("chronic_diseases", ""),
                e.get("address", ""),
            ]
        )
    content = output.getvalue()
    output.close()

    resp = HttpResponse(content, content_type="text/csv; charset=utf-8")
    resp.write("\ufeff")
    resp["Content-Disposition"] = f'attachment; filename="report_{days}d_{datetime.now().strftime("%Y%m%d")}.csv"'
    return resp


@require_auth
def reports_export_print(request):
    days = int(request.GET.get("days", 30))
    overview = reports_overview(request)
    payload = json.loads(overview.content.decode("utf-8"))
    data = payload.get("data", {})
    stats = data.get("stats", {})
    elderly_list = data.get("elderlyList", [])
    alerts = data.get("alerts", [])

    pending_alert_by_id = {}
    for a in alerts:
        if (a.get("status") == "已处理") or ((a.get("workflow_stage") or "").strip() == "已完结"):
            continue
        e_id = a.get("elderly_id")
        if not e_id:
            continue
        pending_alert_by_id[e_id] = pending_alert_by_id.get(e_id, 0) + 1

    rows = []
    for idx, e in enumerate(elderly_list[:30], start=1):
        rows.append(
            f"<tr><td>{idx}</td><td>{e.get('name','')}</td><td>{e.get('risk_level','')}</td>"
            f"<td>{pending_alert_by_id.get(e.get('id'),0)}</td><td>{e.get('chronic_diseases','')}</td></tr>"
        )
    html = f"""
    <html><head><meta charset="utf-8"><title>数据报告</title>
    <style>
    body{{font-family:Arial,'Microsoft YaHei';padding:24px;color:#222;}}
    h1{{margin:0 0 8px;}} .meta{{color:#666;margin-bottom:16px;}}
    .kpi{{display:grid;grid-template-columns:repeat(2,minmax(220px,1fr));gap:10px;margin-bottom:16px;}}
    .item{{padding:10px;border:1px solid #eee;border-radius:8px;}}
    table{{width:100%;border-collapse:collapse;margin-top:8px;}}
    th,td{{border:1px solid #eee;padding:8px;text-align:left;font-size:12px;}}
    th{{background:#f6f8fb;}}
    </style></head><body>
    <h1>社区老年人监护系统 - 数据报告</h1>
    <div class="meta">统计范围：近{days}天 ｜ 导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
    <div class="kpi">
      <div class="item">在管老人：<strong>{len(elderly_list)}</strong></div>
      <div class="item">高风险老人：<strong>{stats.get('rescues', 0)}</strong></div>
      <div class="item">告警处理率：<strong>{stats.get('alertHandleRate', 0)}%</strong></div>
      <div class="item">工单完成率：<strong>{stats.get('orderCompleteRate', 0)}%</strong></div>
    </div>
    <h3>重点关注老人（前30）</h3>
    <table>
      <thead><tr><th>排名</th><th>姓名</th><th>风险等级</th><th>未处理告警</th><th>主要风险</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    </body></html>
    """
    return HttpResponse(html, content_type="text/html; charset=utf-8")


@require_auth
def reports_community_ledger(request):
    """基层纸质台账样式：片区/重点人群一览，可浏览器打印。"""
    user = request.session.get("user") or {}
    if user.get("role") not in ["admin", "service", "nurse"]:
        return JsonResponse({"success": False, "message": "权限不足"}, status=403)
    _ensure_elderly_governance_columns()
    _ensure_alert_workflow_columns()
    grid = request.GET.get("grid", "").strip()
    sql = """
        SELECT e.id, e.name, e.gender, e.birth_date, e.phone, e.address, e.grid_area, e.focus_tags,
               e.risk_level, e.chronic_diseases, e.emergency_contact, e.emergency_phone,
               IFNULL(pa.n, 0) AS pending_alerts
        FROM elderly e
        LEFT JOIN (
            SELECT elderly_id, COUNT(*) AS n FROM alerts
            WHERE IFNULL(TRIM(workflow_stage), '') NOT IN ('已完结', '')
            GROUP BY elderly_id
        ) pa ON pa.elderly_id = e.id
        WHERE 1=1
    """
    params = []
    if grid:
        sql += " AND IFNULL(e.grid_area,'') LIKE ?"
        params.append(f"%{grid}%")
    sql += " ORDER BY IFNULL(e.grid_area,''), e.risk_level DESC, e.id DESC"
    rows_db = fetch_all(sql, tuple(params))

    visits_next = fetch_all(
        """
        SELECT elderly_id, MAX(plan_date || ' ' || IFNULL(plan_time,'')) AS plan_dt
        FROM visits WHERE IFNULL(status,'') != '已完成' GROUP BY elderly_id
        """
    )
    visit_map = {v["elderly_id"]: v.get("plan_dt") for v in visits_next}

    body_rows = []
    for idx, e in enumerate(rows_db, start=1):
        body_rows.append(
            f"<tr><td>{idx}</td><td>{e.get('grid_area') or '-'}</td><td>{e.get('name','')}</td>"
            f"<td>{e.get('risk_level') or '-'}</td><td>{e.get('focus_tags') or '-'}</td>"
            f"<td>{e.get('pending_alerts', 0)}</td><td>{visit_map.get(e['id']) or '-'}</td>"
            f"<td>{e.get('emergency_contact') or '-'} / {e.get('emergency_phone') or '-'}</td>"
            f"<td>{e.get('chronic_diseases') or '-'}</td></tr>"
        )

    title_grid = grid or "全部片区"
    html = f"""
    <html><head><meta charset="utf-8"><title>社区老年人管理台账</title>
    <style>
    body{{font-family:'Microsoft YaHei',Arial;padding:24px;color:#222;}}
    h1{{font-size:18px;margin:0 0 8px;}}
    .meta{{color:#666;font-size:13px;margin-bottom:16px;}}
    table{{width:100%;border-collapse:collapse;font-size:12px;}}
    th,td{{border:1px solid #ccc;padding:6px 8px;text-align:left;}}
    th{{background:#f0f4fb;}}
    @media print {{ body{{padding:12px;}} }}
    </style></head><body>
    <h1>社区重点人群健康管理台账（{title_grid}）</h1>
    <div class="meta">导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
     ｜ 总人数：{len(rows_db)}
     ｜ 说明：「未闭环告警」为仍处于整改/回访流程中的预警数量</div>
    <table>
      <thead><tr><th>序号</th><th>片区</th><th>姓名</th><th>风险等级</th><th>重点标签</th>
      <th>未闭环告警</th><th>近期巡访计划</th><th>紧急联系人</th><th>慢病情况</th></tr></thead>
      <tbody>{''.join(body_rows) if body_rows else '<tr><td colspan="9" style="text-align:center;color:#888;">暂无数据</td></tr>'}</tbody>
    </table>
    <p style="margin-top:14px;font-size:12px;color:#666;">填表说明：打印后由网格员签字存档；告警闭环请在「警报中心」完成接单→整改→回访。</p>
    </body></html>
    """
    return HttpResponse(html, content_type="text/html; charset=utf-8")


@require_auth
def notifications_list(request):
    event_id = request.GET.get("event_id")
    sql = "SELECT * FROM notification_logs WHERE 1=1"
    params = []
    if event_id:
        sql += " AND event_id = ?"
        params.append(event_id)
    sql += " ORDER BY created_at DESC LIMIT 200"
    return JsonResponse({"success": True, "data": fetch_all(sql, tuple(params))})


@require_auth
def events_trace(request):
    event_id = request.GET.get("event_id")
    if not event_id:
        return JsonResponse({"success": False, "message": "event_id 不能为空"}, status=400)
    rows = fetch_all("SELECT * FROM event_traces WHERE event_id = ? ORDER BY id ASC", (event_id,))
    return JsonResponse({"success": True, "data": rows})


def _db_table_name_ok(name):
    return bool(re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name or ""))


def _db_accessible_tables():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        return [str(r["name"]) for r in rows]


@require_auth
@require_role("admin")
def db_schema(request):
    tables = _db_accessible_tables()
    data = []
    with get_conn() as conn:
        for t in tables:
            try:
                count_row = conn.execute(f"SELECT COUNT(*) AS c FROM {t}").fetchone()
                count = int((count_row or {}).get("c") or 0)
            except Exception:
                count = 0
            cols = conn.execute(f"PRAGMA table_info({t})").fetchall()
            data.append(
                {
                    "table": t,
                    "rows": count,
                    "columns": [
                        {"name": c["name"], "type": c["type"], "pk": bool(c["pk"])} for c in cols
                    ],
                }
            )
    return JsonResponse({"success": True, "data": data})


@require_auth
@require_role("admin")
def db_table_preview(request):
    table = str(request.GET.get("table") or "").strip()
    limit = int(request.GET.get("limit", 50))
    offset = int(request.GET.get("offset", 0))
    limit = max(1, min(200, limit))
    offset = max(0, offset)
    if not _db_table_name_ok(table):
        return JsonResponse({"success": False, "message": "非法表名"}, status=400)
    tables = set(_db_accessible_tables())
    if table not in tables:
        return JsonResponse({"success": False, "message": "表不存在"}, status=404)

    with get_conn() as conn:
        cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
        col_names = [c["name"] for c in cols]
        count_row = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
        total = int((count_row or {}).get("c") or 0)
        rows = conn.execute(f"SELECT * FROM {table} LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        data = [{k: row[k] for k in col_names} for row in rows]

    return JsonResponse(
        {
            "success": True,
            "data": {
                "table": table,
                "columns": col_names,
                "rows": data,
                "total": total,
                "limit": limit,
                "offset": offset,
            },
        }
    )


def _settings_defaults():
    return {
        "thresholds": {"heartRateMin": 60, "heartRateMax": 100, "bpMin": 90, "bpMax": 140, "spo2Min": 95, "tempMin": 36.0, "tempMax": 37.5},
        "notifications": {"system": True, "sms": True, "email": False, "app": True, "contacts": "13800000001", "emailAddress": "admin@community.com"},
        "features": {"autoAlert": True, "dispatchSuggestion": True, "medicationReminder": True, "dataSync": True},
        "account": {"adminName": "管理员", "adminAccount": "admin", "adminCommunity": "阳光社区", "adminPhone": "010-****1234"},
    }


def _ensure_settings_table():
    execute(
        """
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            config_json TEXT NOT NULL,
            updated_by INTEGER,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _normalize_settings(input_data):
    d = _settings_defaults()
    s = input_data or {}
    return {
        "thresholds": {**d["thresholds"], **(s.get("thresholds") or {})},
        "notifications": {**d["notifications"], **(s.get("notifications") or {})},
        "features": {**d["features"], **(s.get("features") or {})},
        "account": {**d["account"], **(s.get("account") or {})},
    }


def _validate_settings(settings):
    t = settings.get("thresholds", {})
    if float(t.get("heartRateMin", 0)) < 30 or float(t.get("heartRateMax", 0)) > 220 or float(t.get("heartRateMin", 0)) >= float(t.get("heartRateMax", 0)):
        return "心率阈值不合法"
    if float(t.get("bpMin", 0)) < 60 or float(t.get("bpMax", 0)) > 240 or float(t.get("bpMin", 0)) >= float(t.get("bpMax", 0)):
        return "血压阈值不合法"
    if float(t.get("spo2Min", 0)) < 70 or float(t.get("spo2Min", 0)) > 100:
        return "血氧阈值不合法"
    if float(t.get("tempMin", 0)) < 34 or float(t.get("tempMax", 0)) > 42 or float(t.get("tempMin", 0)) >= float(t.get("tempMax", 0)):
        return "体温阈值不合法"

    contacts = str((settings.get("notifications") or {}).get("contacts", "")).strip()
    if contacts:
        for phone in [x.strip() for x in contacts.split(",") if x.strip()]:
            if not __import__("re").match(r"^1\d{10}$", phone):
                return f"紧急通知名单手机号格式错误: {phone}"
    if (settings.get("notifications") or {}).get("email"):
        email = str((settings.get("notifications") or {}).get("emailAddress", "")).strip()
        if not __import__("re").match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
            return "邮件通知已开启，但邮箱地址无效"
    return ""


@csrf_exempt
@require_auth
def settings_current(request):
    if request.method == "GET":
        _ensure_settings_table()
        row = fetch_one("SELECT config_json, updated_at FROM system_settings WHERE id = 1")
        if not row:
            return JsonResponse({"success": True, "data": {"settings": None, "updated_at": None}})
        try:
            raw_settings = json.loads(row.get("config_json") or "{}")
        except Exception:
            raw_settings = None
        return JsonResponse({"success": True, "data": {"settings": _normalize_settings(raw_settings), "updated_at": row.get("updated_at")}})
    if request.method == "PUT":
        user = request.session.get("user") or {}
        if user.get("role") != "admin":
            return JsonResponse({"success": False, "message": "权限不足"}, status=403)
        _ensure_settings_table()
        settings = _normalize_settings(_json_body(request))
        err = _validate_settings(settings)
        if err:
            return JsonResponse({"success": False, "message": err}, status=400)
        execute(
            """
            INSERT INTO system_settings (id, config_json, updated_by, updated_at)
            VALUES (1, ?, ?, datetime('now', 'localtime'))
            ON CONFLICT(id) DO UPDATE SET
                config_json = excluded.config_json,
                updated_by = excluded.updated_by,
                updated_at = datetime('now', 'localtime')
            """,
            (json.dumps(settings, ensure_ascii=False), user.get("id")),
        )
        return JsonResponse({"success": True, "message": "系统设置已更新", "data": {"settings": settings}})
    return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)


def _risk_level_text(level):
    if level == "high":
        return "高风险"
    if level == "medium":
        return "中风险"
    return "低风险"


def _llm_config():
    api_key = os.getenv("LLM_API_KEY", "").strip()
    api_base = os.getenv("LLM_API_BASE", "https://api.openai.com/v1").strip().rstrip("/")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
    return {"api_key": api_key, "api_base": api_base, "model": model}


def _call_llm_json(system_prompt, user_prompt):
    cfg = _llm_config()
    if not cfg["api_key"]:
        return None
    url = f"{cfg['api_base']}/chat/completions"
    payload = {
        "model": cfg["model"],
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg['api_key']}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            content = (((raw or {}).get("choices") or [{}])[0].get("message") or {}).get("content", "")
            content = str(content or "").strip()
            if content.startswith("```"):
                content = content.strip("`")
                if content.startswith("json"):
                    content = content[4:].strip()
            return json.loads(content)
    except Exception:
        return None


def _map_risk_level(elderly, active_alert_count, latest_vital):
    lv = str((elderly or {}).get("risk_level", "")).lower()
    heart_rate = float((latest_vital or {}).get("heart_rate") or 0)
    bp_high = float((latest_vital or {}).get("blood_pressure_high") or 0)
    spo2 = float((latest_vital or {}).get("blood_oxygen") or 0)
    if "高" in lv or active_alert_count >= 2 or heart_rate >= 110 or bp_high >= 160 or (spo2 and spo2 < 92):
        return "high"
    if "中" in lv or active_alert_count >= 1 or heart_rate >= 100 or bp_high >= 145 or (spo2 and spo2 < 95):
        return "medium"
    return "low"


def _risk_analysis_text(elderly_name, level, reasons):
    advise = {
        "high": "建议立即跟进并派医，必要时转诊",
        "medium": "建议24小时内复核并进行电话随访",
        "low": "建议持续观察并保持日常监测",
    }.get(level, "建议持续观察")
    reason_text = "，".join(reasons) if reasons else "近期生命体征波动较小"
    return f"AI分析：{elderly_name}当前为{_risk_level_text(level)}，主要依据：{reason_text}。{advise}。"


@csrf_exempt
@require_auth
def ai_risk(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    payload = _json_body(request)
    elderly_id = payload.get("elderly_id")
    if elderly_id:
        elderly_list = fetch_all("SELECT * FROM elderly WHERE id = ? LIMIT 1", (elderly_id,))
    else:
        elderly_list = fetch_all("SELECT * FROM elderly ORDER BY created_at DESC LIMIT 200")

    alerts = fetch_all("SELECT elderly_id, status FROM alerts")
    alert_map = {}
    for a in alerts:
        e_id = int(a.get("elderly_id") or 0)
        if not e_id:
            continue
        if e_id not in alert_map:
            alert_map[e_id] = {"total": 0, "active": 0}
        alert_map[e_id]["total"] += 1
        if a.get("status") != "已处理":
            alert_map[e_id]["active"] += 1

    risk_items = []
    for e in elderly_list:
        e_id = int(e.get("id"))
        agg = alert_map.get(e_id, {"total": 0, "active": 0})
        latest_vital = fetch_one(
            "SELECT heart_rate, blood_pressure_high, blood_pressure_low, blood_oxygen, temperature, recorded_at FROM health_data WHERE elderly_id = ? ORDER BY recorded_at DESC LIMIT 1",
            (e_id,),
        )
        level = _map_risk_level(e, agg["active"], latest_vital)
        reasons = []
        if agg["active"] > 0:
            reasons.append(f"存在{agg['active']}条未处理告警")
        if str(e.get("health_status") or "") in ["危重状态", "较差"]:
            reasons.append("健康状态提示异常")
        if latest_vital and float(latest_vital.get("heart_rate") or 0) >= 110:
            reasons.append("心率偏高")
        if latest_vital and float(latest_vital.get("blood_pressure_high") or 0) >= 160:
            reasons.append("收缩压偏高")
        analysis = _risk_analysis_text(e.get("name", "该老人"), level, reasons)
        llm_risk = _call_llm_json(
            "你是社区医疗风险评估助手。请仅输出 JSON，不要输出其他文字。",
            (
                "请基于以下信息给出一段简短中文风险分析。"
                "输出格式必须是 JSON：{\"analysis\":\"...\",\"reasons\":[\"...\"]}\n"
                f"老人姓名: {e.get('name')}\n"
                f"档案风险等级: {e.get('risk_level')}\n"
                f"健康状态: {e.get('health_status')}\n"
                f"慢病: {e.get('chronic_diseases')}\n"
                f"未处理告警数: {agg['active']}\n"
                f"最新体征: {json.dumps(latest_vital or {}, ensure_ascii=False)}\n"
                f"规则判定等级: {_risk_level_text(level)}"
            ),
        )
        if isinstance(llm_risk, dict):
            analysis = str(llm_risk.get("analysis") or analysis)
            llm_reasons = llm_risk.get("reasons")
            if isinstance(llm_reasons, list) and llm_reasons:
                reasons = [str(x) for x in llm_reasons[:4]]
        risk_items.append(
            {
                "id": e_id,
                "level": level,
                "levelText": _risk_level_text(level),
                "analysis": analysis,
                "reasons": reasons,
                "totalAlerts": agg["total"],
                "activeAlerts": agg["active"],
                "latestVital": latest_vital,
            }
        )

    risk_items.sort(key=lambda x: ({"high": 3, "medium": 2, "low": 1}[x["level"]], x["activeAlerts"]), reverse=True)
    return JsonResponse(
        {
            "success": True,
            "data": {
                "list": risk_items,
                "generatedAt": datetime.now().isoformat(),
            },
        }
    )


@csrf_exempt
@require_auth
def ai_diagnosis(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    payload = _json_body(request)
    elderly_id = payload.get("elderly_id")
    symptoms = payload.get("symptoms") or []
    symptom_text = "、".join([str(x).strip() for x in symptoms if str(x).strip()])
    narrative = str(payload.get("narrative") or "").strip()

    if not elderly_id:
        return JsonResponse({"success": False, "message": "elderly_id 不能为空"}, status=400)

    elderly = fetch_one("SELECT * FROM elderly WHERE id = ?", (elderly_id,))
    if not elderly:
        return JsonResponse({"success": False, "message": "老人不存在"}, status=404)
    vital = fetch_one(
        "SELECT heart_rate, blood_pressure_high, blood_pressure_low, blood_oxygen, temperature, recorded_at FROM health_data WHERE elderly_id = ? ORDER BY recorded_at DESC LIMIT 1",
        (elderly_id,),
    )

    heart_rate = float((vital or {}).get("heart_rate") or 0)
    bp_high = float((vital or {}).get("blood_pressure_high") or 0)
    bp_low = float((vital or {}).get("blood_pressure_low") or 0)
    spo2 = float((vital or {}).get("blood_oxygen") or 0)

    score = 0
    if heart_rate >= 110:
        score += 25
    elif heart_rate >= 100:
        score += 15
    if bp_high >= 160 or bp_low >= 100:
        score += 25
    elif bp_high >= 145 or bp_low >= 90:
        score += 15
    if spo2 and spo2 < 92:
        score += 25
    elif spo2 and spo2 < 95:
        score += 10
    score += min(20, len(symptoms) * 4)
    if "高" in str(elderly.get("risk_level") or ""):
        score += 10

    if score >= 60:
        risk = "高风险"
        title = "心脑血管并发风险（需立即复核）"
        confidence = min(92, 65 + score // 2)
    elif score >= 35:
        risk = "中风险"
        title = "慢病波动风险（建议当日干预）"
        confidence = min(85, 55 + score // 2)
    else:
        risk = "低风险"
        title = "轻度异常（建议持续观察）"
        confidence = min(78, 50 + score // 2)

    summary = (
        f"结合{elderly.get('name', '该老人')}当前生命体征"
        f"（心率{int(heart_rate) if heart_rate else '--'}，血压{int(bp_high) if bp_high else '--'}/{int(bp_low) if bp_low else '--'}，血氧{spo2 if spo2 else '--'}）"
        f"与症状（{symptom_text or '未提供'}），系统判定为{risk}。"
    )
    if narrative:
        summary += f" 补充描述：{narrative[:120]}"

    suggestions = [
        "现场复测心率、血压、血氧并记录",
        "结合既往病史评估是否需要升级处置",
        "与家属同步当前观察结果并安排随访",
    ]
    if risk == "高风险":
        suggestions.insert(0, "建议立即派医并准备转诊评估")
    elif risk == "中风险":
        suggestions.insert(0, "建议24小时内完成上门复核")

    recommended_doctor = fetch_one(
        "SELECT id, name, specialization, rating FROM doctors WHERE status = '在线' ORDER BY rating DESC LIMIT 1"
    )
    referral = "建议准备转诊评估" if risk == "高风险" else "暂不建议转诊，持续观察"

    llm_diag = _call_llm_json(
        "你是社区全科医生助手。请只输出 JSON，不要输出 markdown。",
        (
            "请根据病例信息输出结构化辅助诊断。JSON格式:\n"
            "{\"title\":\"...\",\"risk\":\"高风险|中风险|低风险\",\"confidence\":0-100,"
            "\"summary\":\"...\",\"suggestions\":[\"...\"],\"referral\":\"...\"}\n"
            f"老人信息: {json.dumps(elderly, ensure_ascii=False)}\n"
            f"最新体征: {json.dumps(vital or {}, ensure_ascii=False)}\n"
            f"症状: {symptom_text or '无'}\n"
            f"补充描述: {narrative or '无'}\n"
            f"规则结果: 风险={risk}, 置信度={int(confidence)}, 标题={title}, 概要={summary}"
        ),
    )
    if isinstance(llm_diag, dict):
        title = str(llm_diag.get("title") or title)
        risk = str(llm_diag.get("risk") or risk)
        if risk not in ["高风险", "中风险", "低风险"]:
            risk = "中风险"
        try:
            confidence = int(llm_diag.get("confidence"))
        except Exception:
            confidence = int(confidence)
        confidence = max(1, min(99, int(confidence)))
        summary = str(llm_diag.get("summary") or summary)
        llm_suggestions = llm_diag.get("suggestions")
        if isinstance(llm_suggestions, list) and llm_suggestions:
            suggestions = [str(x) for x in llm_suggestions[:6]]
        referral = str(llm_diag.get("referral") or referral)

    return JsonResponse(
        {
            "success": True,
            "data": {
                "title": title,
                "risk": risk,
                "confidence": int(confidence),
                "summary": summary,
                "suggestions": suggestions,
                "recommendedDoctor": recommended_doctor,
                "referral": referral,
                "generatedAt": datetime.now().isoformat(),
            },
        }
    )

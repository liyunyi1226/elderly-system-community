# Django 后端（Python）

该目录是把原后端从 Node.js/Express 迁移到 Python/Django 的版本。

## 已迁移接口

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/current`
- `GET /api/auth/permissions`
- `GET /api/elderly/list`
- `GET /api/elderly/<id>`
- `POST /api/elderly/create`
- `PUT /api/elderly/<id>`
- `DELETE /api/elderly/<id>`
- `POST /api/elderly/health-data`
- `GET /api/alerts/list`
- `GET /api/alerts/statistics`
- `POST /api/alerts/create`
- `PUT /api/alerts/<id>/handle`
- `GET /api/orders/list`
- `POST /api/orders/create`
- `PUT /api/orders/<id>/status`
- `PUT /api/orders/<id>/complete`
- `GET /api/devices/list`
- `GET /api/devices/statistics`
- `POST /api/devices/create`
- `GET/PUT/DELETE /api/devices/<id>`
- `PUT /api/devices/<id>/status`
- `GET /api/doctors/list`
- `POST /api/doctors/create`
- `GET/PUT/DELETE /api/doctors/<id>`
- `PUT /api/doctors/<id>/status`
- `GET /api/visits/list`
- `POST /api/visits/create`
- `PUT /api/visits/<id>/complete`
- `GET /api/dashboard/overview`
- `GET /api/dashboard/trend`
- `GET /api/reports/overview`
- `GET /api/reports/export/csv`
- `GET /api/reports/export/print`
- `GET/PUT /api/settings/current`
- `GET /api/notifications/list`
- `GET /api/events/trace`
- `POST /api/devices/<id>/telemetry`
- `POST /api/ai/risk`
- `POST /api/ai/diagnosis`

## 快速启动

```bash
cd server/django_backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:3000
```

## 数据库说明

- 业务数据复用原 SQLite：`server/data/elderly_monitoring.db`
- Django 自身 session 数据库：`server/django_backend/django.sqlite3`

## 说明

- 为了保持前端兼容，路由路径继续使用 `/api/*`。

## LLM 配置（可选）

若配置了以下环境变量，`/api/ai/risk` 与 `/api/ai/diagnosis` 会优先调用大模型；未配置时自动使用本地规则引擎。

- `LLM_API_KEY`：大模型 API Key
- `LLM_API_BASE`：OpenAI 兼容接口地址（默认 `https://api.openai.com/v1`）
- `LLM_MODEL`：模型名（默认 `gpt-4o-mini`）

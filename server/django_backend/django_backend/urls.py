from django.http import HttpResponse, JsonResponse
from django.urls import path, include
import json

ROLE_PERMISSIONS = {
    "admin": ["dashboard", "elderly-list", "elderly-detail", "doctor-list", "doctor-detail", "device-list", "device-detail", "alert-list", "alert-detail", "order-list", "order-detail", "visit-list", "visit-detail", "ai-risk-warning", "ai-diagnosis", "system-config"],
    "doctor": ["dashboard", "elderly-list", "elderly-detail", "alert-list", "alert-detail", "order-list", "order-detail", "ai-risk-warning", "ai-diagnosis"],
    "nurse": ["dashboard", "elderly-list", "elderly-detail", "visit-plan", "devices", "alerts", "ai-risk-warning", "ai-diagnosis"],
    "service": ["dashboard", "elderly-list", "elderly-detail", "alerts", "reports", "ai-risk-warning", "ai-diagnosis"]
}


def root(request):
    return _frontend_redirect(request, "/login")


def _frontend_redirect(request, path):
    html = f"""
    <html><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=http://localhost:5173{path}"></head><body></body></html>
    """
    return HttpResponse(html, content_type="text/html; charset=utf-8")


def admin_pages(request):
    if not request.session.get("user"):
        request.session["user"] = {
            "id": 1,
            "username": "admin",
            "realName": "系统管理员",
            "role": "admin",
            "permissions": ROLE_PERMISSIONS.get("admin", []),
        }
    html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>老年人监护系统 - 管理后台</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
                background-color: #f5f7fa;
                color: #333;
                line-height: 1.5;
            }
            
            .header {
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 16px 24px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            .header-content {
                max-width: 1440px;
                margin: 0 auto;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .header h1 {
                font-size: 20px;
                font-weight: 600;
            }
            
            .user-info {
                font-size: 14px;
                opacity: 0.9;
            }
            
            .main-container {
                max-width: 1440px;
                margin: 24px auto;
                padding: 0 24px;
            }
            
            .nav-tabs {
                display: flex;
                background: white;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                overflow: hidden;
            }
            
            .nav-tab {
                flex: 1;
                padding: 12px 16px;
                text-align: center;
                cursor: pointer;
                border: none;
                background: none;
                font-size: 14px;
                font-weight: 500;
                color: #666;
                transition: all 0.3s ease;
                position: relative;
            }
            
            .nav-tab:hover {
                background-color: #f8f9fa;
                color: #1e3c72;
            }
            
            .nav-tab.active {
                color: #1e3c72;
                font-weight: 600;
                background-color: #f0f4f8;
            }
            
            .nav-tab.active::after {
                content: '';
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                height: 2px;
                background-color: #1e3c72;
            }
            
            .card {
                background: white;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                padding: 20px;
                margin-bottom: 20px;
            }
            
            .card-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 16px;
                padding-bottom: 12px;
                border-bottom: 1px solid #e9ecef;
            }
            
            .card-title {
                font-size: 16px;
                font-weight: 600;
                color: #333;
            }
            
            .toolbar {
                display: flex;
                gap: 12px;
                align-items: center;
                flex-wrap: wrap;
            }
            
            .search-box {
                display: flex;
                gap: 8px;
                align-items: center;
            }
            
            .form-control {
                padding: 8px 12px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-size: 14px;
                width: 200px;
                transition: border-color 0.3s ease;
            }
            
            .form-control:focus {
                outline: none;
                border-color: #1e3c72;
                box-shadow: 0 0 0 2px rgba(30, 60, 114, 0.1);
            }
            
            .btn {
                padding: 8px 16px;
                border: 1px solid transparent;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s ease;
                white-space: nowrap;
            }
            
            .btn-primary {
                background-color: #1e3c72;
                color: white;
                border-color: #1e3c72;
            }
            
            .btn-primary:hover {
                background-color: #2a5298;
                border-color: #2a5298;
            }
            
            .btn-outline {
                background-color: white;
                color: #1e3c72;
                border-color: #1e3c72;
            }
            
            .btn-outline:hover {
                background-color: #f0f4f8;
            }
            
            .btn-sm {
                padding: 6px 12px;
                font-size: 13px;
            }
            
            .table-container {
                overflow-x: auto;
                border-radius: 4px;
                border: 1px solid #e9ecef;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                font-size: 14px;
            }
            
            th, td {
                padding: 12px 16px;
                text-align: left;
                border-bottom: 1px solid #e9ecef;
            }
            
            th {
                background-color: #f8f9fa;
                font-weight: 600;
                color: #333;
                position: sticky;
                top: 0;
                z-index: 10;
            }
            
            tr:hover {
                background-color: #f8f9fa;
            }
            
            .status-badge {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
            }
            
            .status-active {
                background-color: #e8f5e8;
                color: #2e7d32;
            }
            
            .status-warning {
                background-color: #fff8e1;
                color: #f57c00;
            }
            
            .status-danger {
                background-color: #ffebee;
                color: #c62828;
            }
            
            .status-info {
                background-color: #e3f2fd;
                color: #1565c0;
            }
            
            .action-buttons {
                display: flex;
                gap: 8px;
                align-items: center;
            }
            
            .modal {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(0,0,0,0.5);
                display: none;
                align-items: center;
                justify-content: center;
                z-index: 1000;
            }
            
            .modal.show {
                display: flex;
            }
            
            .modal-content {
                background: white;
                border-radius: 8px;
                width: 90%;
                max-width: 600px;
                max-height: 90vh;
                overflow-y: auto;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            
            .modal-header {
                padding: 16px 20px;
                border-bottom: 1px solid #e9ecef;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .modal-title {
                font-size: 16px;
                font-weight: 600;
                color: #333;
            }
            
            .modal-body {
                padding: 20px;
            }
            
            .modal-footer {
                padding: 16px 20px;
                border-top: 1px solid #e9ecef;
                display: flex;
                justify-content: flex-end;
                gap: 12px;
            }
            
            .form-group {
                margin-bottom: 16px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 6px;
                font-weight: 500;
                color: #333;
                font-size: 14px;
            }
            
            .form-group input,
            .form-group select,
            .form-group textarea {
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-size: 14px;
                transition: border-color 0.3s ease;
            }
            
            .form-group input:focus,
            .form-group select:focus,
            .form-group textarea:focus {
                outline: none;
                border-color: #1e3c72;
                box-shadow: 0 0 0 2px rgba(30, 60, 114, 0.1);
            }
            
            .form-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
            }
            
            .form-row .form-group {
                margin-bottom: 0;
            }
            
            .text-muted {
                color: #6c757d;
                font-size: 13px;
            }
            
            .meta-info {
                margin-bottom: 16px;
                padding: 12px;
                background-color: #f8f9fa;
                border-radius: 4px;
                font-size: 13px;
            }
            
            @media (max-width: 768px) {
                .main-container {
                    padding: 0 12px;
                }
                
                .header-content {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 8px;
                }
                
                .nav-tabs {
                    flex-direction: column;
                }
                
                .toolbar {
                    flex-direction: column;
                    align-items: stretch;
                }
                
                .search-box {
                    flex-direction: column;
                    align-items: stretch;
                }
                
                .form-control {
                    width: 100%;
                }
                
                .form-row {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <header class="header">
            <div class="header-content">
                <h1>老年人监护系统</h1>
                <div class="user-info">
                    系统管理员
                </div>
            </div>
        </header>
        
        <div class="main-container">
            <div class="nav-tabs">
                <button class="nav-tab active" data-tab="elderly">老人管理</button>
                <button class="nav-tab" data-tab="doctors">医生管理</button>
                <button class="nav-tab" data-tab="devices">设备管理</button>
                <button class="nav-tab" data-tab="alerts">告警管理</button>
                <button class="nav-tab" data-tab="orders">工单管理</button>
                <button class="nav-tab" data-tab="visits">巡访管理</button>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title" id="page-title">老人管理</h2>
                    <div class="toolbar">
                        <div class="search-box">
                            <input type="text" id="search-input" class="form-control" placeholder="搜索...">
                            <select id="status-filter" class="form-control">
                                <option value="">全部状态</option>
                            </select>
                            <button class="btn btn-outline" id="search-btn">搜索</button>
                        </div>
                        <button class="btn btn-primary" id="add-btn">新增</button>
                        <button class="btn btn-outline" id="refresh-btn">刷新</button>
                    </div>
                </div>
                
                <div class="meta-info" id="meta-info">
                    共 0 条记录
                </div>
                
                <div class="table-container">
                    <table id="data-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>姓名</th>
                                <th>性别</th>
                                <th>电话</th>
                                <th>健康状态</th>
                                <th>风险等级</th>
                                <th>地址</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td colspan="8" class="text-muted" style="text-align: center;">加载中...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <div class="modal" id="edit-modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title" id="modal-title">新增老人</h3>
                    <button class="btn btn-outline btn-sm" id="close-modal" style="padding: 4px 8px;">×</button>
                </div>
                <div class="modal-body">
                    <form id="edit-form">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="name">姓名</label>
                                <input type="text" id="name" name="name" class="form-control" required>
                            </div>
                            <div class="form-group">
                                <label for="gender">性别</label>
                                <select id="gender" name="gender" class="form-control">
                                    <option value="男">男</option>
                                    <option value="女">女</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="phone">电话</label>
                                <input type="text" id="phone" name="phone" class="form-control">
                            </div>
                            <div class="form-group">
                                <label for="birth_date">出生日期</label>
                                <input type="date" id="birth_date" name="birth_date" class="form-control">
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="address">地址</label>
                            <input type="text" id="address" name="address" class="form-control">
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="health_status">健康状态</label>
                                <select id="health_status" name="health_status" class="form-control">
                                    <option value="健康良好">健康良好</option>
                                    <option value="需要关注">需要关注</option>
                                    <option value="危重状态">危重状态</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="risk_level">风险等级</label>
                                <select id="risk_level" name="risk_level" class="form-control">
                                    <option value="低风险">低风险</option>
                                    <option value="中风险">中风险</option>
                                    <option value="高风险">高风险</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="emergency_contact">紧急联系人</label>
                                <input type="text" id="emergency_contact" name="emergency_contact" class="form-control">
                            </div>
                            <div class="form-group">
                                <label for="emergency_phone">紧急联系电话</label>
                                <input type="text" id="emergency_phone" name="emergency_phone" class="form-control">
                            </div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-outline" id="cancel-btn">取消</button>
                    <button class="btn btn-primary" id="save-btn">保存</button>
                </div>
            </div>
        </div>
        
        <script>
            let currentTab = 'elderly';
            let currentData = [];
            let filteredData = [];
            let editingItem = null;
            
            const tabConfig = {
                elderly: {
                    title: '老人管理',
                    api: {
                        list: '/api/elderly/list?page=1&pageSize=200',
                        create: '/api/elderly/create',
                        update: (id) => `/api/elderly/${id}`,
                        delete: (id) => `/api/elderly/${id}`
                    },
                    columns: [
                        { key: 'id', title: 'ID' },
                        { key: 'name', title: '姓名' },
                        { key: 'gender', title: '性别' },
                        { key: 'phone', title: '电话' },
                        { key: 'chronic_diseases', title: '病史/慢病' },
                        { key: 'health_status', title: '健康状态', type: 'status' },
                        { key: 'risk_level', title: '风险等级', type: 'status' },
                        { key: 'address', title: '地址' }
                    ],
                    formFields: [
                        { name: 'name', label: '姓名', type: 'text', required: true },
                        { name: 'gender', label: '性别', type: 'select', options: ['男', '女'] },
                        { name: 'phone', label: '电话', type: 'text' },
                        { name: 'birth_date', label: '出生日期', type: 'date' },
                        { name: 'id_card', label: '身份证号', type: 'text' },
                        { name: 'address', label: '地址', type: 'text' },
                        { name: 'grid_area', label: '片区/网格', type: 'text' },
                        { name: 'focus_tags', label: '重点标签(逗号分隔)', type: 'text' },
                        { name: 'health_status', label: '健康状态', type: 'select', options: ['健康良好', '需要关注', '危重状态'] },
                        { name: 'risk_level', label: '风险等级', type: 'select', options: ['低风险', '中风险', '高风险'] },
                        { name: 'chronic_diseases', label: '既往病史/慢病情况', type: 'textarea' },
                        { name: 'allergies', label: '过敏信息', type: 'textarea' },
                        { name: 'medications', label: '长期用药', type: 'textarea' },
                        { name: 'emergency_contact', label: '紧急联系人', type: 'text' },
                        { name: 'emergency_phone', label: '紧急联系电话', type: 'text' },
                        { name: 'contacts', label: '家属联系人', type: 'contacts' }
                    ],
                    statusMap: {
                        '健康良好': 'active',
                        '需要关注': 'warning',
                        '危重状态': 'danger',
                        '低风险': 'active',
                        '中风险': 'warning',
                        '高风险': 'danger'
                    }
                },
                doctors: {
                    title: '医生管理',
                    api: {
                        list: '/api/doctors/list',
                        create: '/api/doctors/create',
                        update: (id) => `/api/doctors/${id}`,
                        delete: (id) => `/api/doctors/${id}`
                    },
                    columns: [
                        { key: 'id', title: 'ID' },
                        { key: 'name', title: '姓名' },
                        { key: 'gender', title: '性别' },
                        { key: 'phone', title: '电话' },
                        { key: 'specialization', title: '专长' },
                        { key: 'hospital', title: '医院' },
                        { key: 'status', title: '状态', type: 'status' }
                    ],
                    formFields: [
                        { name: 'name', label: '姓名', type: 'text', required: true },
                        { name: 'gender', label: '性别', type: 'select', options: ['男', '女'] },
                        { name: 'phone', label: '电话', type: 'text' },
                        { name: 'specialization', label: '专长', type: 'text' },
                        { name: 'hospital', label: '医院', type: 'text' },
                        { name: 'status', label: '状态', type: 'select', options: ['在线', '忙碌', '离线'] },
                        { name: 'current_location', label: '当前位置', type: 'text' },
                        { name: 'rating', label: '评分', type: 'number', min: 1, max: 5 }
                    ],
                    statusMap: {
                        '在线': 'active',
                        '忙碌': 'warning',
                        '离线': 'info'
                    }
                },
                devices: {
                    title: '设备管理',
                    api: {
                        list: '/api/devices/list',
                        create: '/api/devices/create',
                        update: (id) => `/api/devices/${id}`,
                        delete: (id) => `/api/devices/${id}`
                    },
                    columns: [
                        { key: 'id', title: 'ID' },
                        { key: 'device_id', title: '设备编号' },
                        { key: 'device_type', title: '设备类型' },
                        { key: 'elderly_id', title: '老人ID' },
                        { key: 'status', title: '状态', type: 'status' },
                        { key: 'battery_level', title: '电量' },
                        { key: 'last_online_at', title: '最后在线' }
                    ],
                    formFields: [
                        { name: 'device_id', label: '设备编号', type: 'text', required: true },
                        { name: 'device_type', label: '设备类型', type: 'text', required: true },
                        { name: 'elderly_id', label: '老人ID', type: 'number' },
                        { name: 'status', label: '状态', type: 'select', options: ['在线', '离线', '故障'] },
                        { name: 'battery_level', label: '电量', type: 'number', min: 0, max: 100 }
                    ],
                    statusMap: {
                        '在线': 'active',
                        '离线': 'info',
                        '故障': 'danger'
                    }
                },
                alerts: {
                    title: '告警管理',
                    api: {
                        list: '/api/alerts/list?page=1&pageSize=200',
                        create: '/api/alerts/create'
                    },
                    columns: [
                        { key: 'id', title: 'ID' },
                        { key: 'elderly_name', title: '老人姓名' },
                        { key: 'alert_type', title: '告警类型' },
                        { key: 'level', title: '等级', type: 'status' },
                        { key: 'workflow_stage', title: '状态', type: 'status' },
                        { key: 'created_at', title: '创建时间' }
                    ],
                    statusMap: {
                        '待响应': 'warning',
                        '处置中': 'info',
                        '待回访': 'warning',
                        '已完结': 'active',
                        '低风险': 'active',
                        '中风险': 'warning',
                        '高风险': 'danger'
                    },
                    formFields: [
                        { name: 'elderly_id', label: '老人ID', type: 'number', required: true },
                        { name: 'alert_type', label: '告警类型', type: 'text', required: true },
                        { name: 'title', label: '告警标题', type: 'text', required: true },
                        { name: 'content', label: '告警内容', type: 'textarea', required: true },
                        { name: 'location', label: '位置', type: 'text' },
                        { name: 'alert_level', label: '告警等级(1高-3低)', type: 'number', min: 1, max: 3 }
                    ]
                },
                orders: {
                    title: '工单管理',
                    api: {
                        list: '/api/orders/list?page=1&pageSize=200',
                        create: '/api/orders/create'
                    },
                    columns: [
                        { key: 'id', title: 'ID' },
                        { key: 'order_no', title: '工单编号' },
                        { key: 'elderly_name', title: '老人姓名' },
                        { key: 'urgency', title: '紧急程度', type: 'status' },
                        { key: 'status', title: '状态', type: 'status' },
                        { key: 'created_at', title: '创建时间' }
                    ],
                    statusMap: {
                        '待接单': 'warning',
                        '已接单': 'info',
                        '出发中': 'info',
                        '已到达': 'info',
                        '处置中': 'info',
                        '已完成': 'active',
                        '低': 'active',
                        '一般': 'warning',
                        '高': 'danger'
                    },
                    formFields: [
                        { name: 'elderly_id', label: '老人ID', type: 'number', required: true },
                        { name: 'doctor_id', label: '医生ID', type: 'number' },
                        { name: 'alert_id', label: '关联告警ID', type: 'number' },
                        { name: 'urgency', label: '紧急程度', type: 'select', options: ['低', '一般', '高'] },
                        { name: 'description', label: '工单描述', type: 'textarea' }
                    ]
                },
                visits: {
                    title: '巡访管理',
                    api: {
                        list: '/api/visits/list?page=1&pageSize=200',
                        create: '/api/visits/create'
                    },
                    columns: [
                        { key: 'id', title: 'ID' },
                        { key: 'elderly_name', title: '老人姓名' },
                        { key: 'nurse_name', title: '护士姓名' },
                        { key: 'plan_date', title: '计划日期' },
                        { key: 'status', title: '状态', type: 'status' },
                        { key: 'actual_time', title: '实际时间' }
                    ],
                    statusMap: {
                        '待执行': 'warning',
                        '执行中': 'info',
                        '已完成': 'active'
                    },
                    formFields: [
                        { name: 'elderly_id', label: '老人ID', type: 'number', required: true },
                        { name: 'nurse_id', label: '护士用户ID(可空)', type: 'number' },
                        { name: 'plan_date', label: '计划日期', type: 'date', required: true },
                        { name: 'plan_time', label: '计划时间', type: 'time', required: true },
                        { name: 'visit_content', label: '随访内容', type: 'textarea', required: true }
                    ]
                }
            };
            
            async function fetchData() {
                const config = tabConfig[currentTab];
                if (!config.api.list) return;
                
                try {
                    const response = await fetch(config.api.list, {
                        credentials: 'include'
                    });
                    const data = await response.json();
                    
                    if (data.success) {
                        currentData = data.data?.list || data.data || [];
                        filteredData = [...currentData];
                        updateStatusFilter();
                        updateMetaInfo();
                        renderTable();
                    } else {
                        showMessage('获取数据失败: ' + (data.message || '未知错误'));
                    }
                } catch (error) {
                    showMessage('网络错误: ' + error.message);
                }
            }
            
            function updateStatusFilter() {
                const config = tabConfig[currentTab];
                const statusFilter = document.getElementById('status-filter');
                
                const statuses = [...new Set(currentData.map(item => {
                    const statusFields = ['status', 'health_status', 'risk_level', 'workflow_stage', 'level', 'urgency'];
                    for (const field of statusFields) {
                        if (item[field]) return item[field];
                    }
                    return null;
                }).filter(Boolean))];
                
                statusFilter.innerHTML = '<option value="">全部状态</option>';
                statuses.forEach(status => {
                    const option = document.createElement('option');
                    option.value = status;
                    option.textContent = status;
                    statusFilter.appendChild(option);
                });
            }
            
            function updateMetaInfo() {
                const metaInfo = document.getElementById('meta-info');
                metaInfo.textContent = `共 ${currentData.length} 条记录，筛选后 ${filteredData.length} 条`;
            }
            
            function renderTable() {
                const config = tabConfig[currentTab];
                const table = document.getElementById('data-table');
                const tbody = table.querySelector('tbody');
                
                if (filteredData.length === 0) {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="${config.columns.length + 1}" class="text-muted" style="text-align: center;">暂无数据</td>
                        </tr>
                    `;
                    return;
                }
                
                tbody.innerHTML = filteredData.map(item => {
                    const cells = config.columns.map(column => {
                        const value = item[column.key] || '';
                        
                        if (column.type === 'status' && config.statusMap) {
                            const statusClass = config.statusMap[value] || 'info';
                            return `<td><span class="status-badge status-${statusClass}">${value}</span></td>`;
                        }
                        
                        return `<td>${value}</td>`;
                    }).join('');
                    
                    const actions = buildActions(item, config);
                    
                    return `
                        <tr>
                            ${cells}
                            <td>${actions}</td>
                        </tr>
                    `;
                }).join('');
            }

            function buildActions(item, config) {
                const buttons = [];
                // 仅保留增删改查中的行级操作：改/删（查在列表检索，增在顶部按钮）
                if (config.api.update) {
                    buttons.push(`<button class="btn btn-outline btn-sm" onclick="editItem(${item.id})">编辑</button>`);
                }
                if (config.api.delete) {
                    buttons.push(`<button class="btn btn-outline btn-sm" onclick="deleteItem(${item.id})" style="color: #dc3545; border-color: #dc3545;">删除</button>`);
                }
                return `<div class="action-buttons">${buttons.join('')}</div>`;
            }
            
            function filterData() {
                const searchText = document.getElementById('search-input').value.toLowerCase();
                const statusValue = document.getElementById('status-filter').value;
                
                filteredData = currentData.filter(item => {
                    const matchesSearch = Object.values(item).some(value => {
                        return String(value).toLowerCase().includes(searchText);
                    });
                    
                    if (!statusValue) return matchesSearch;
                    
                    const statusFields = ['status', 'health_status', 'risk_level', 'workflow_stage', 'level', 'urgency'];
                    const matchesStatus = statusFields.some(field => {
                        return item[field] === statusValue;
                    });
                    
                    return matchesSearch && matchesStatus;
                });
                
                updateMetaInfo();
                renderTable();
            }
            
            function openModal(title, item = null) {
                const modal = document.getElementById('edit-modal');
                const modalTitle = document.getElementById('modal-title');
                const form = document.getElementById('edit-form');
                
                modalTitle.textContent = title;
                editingItem = item;
                
                const config = tabConfig[currentTab];
                form.innerHTML = config.formFields.map(field => {
                    let fieldHtml = '';
                    const value = item ? item[field.name] : '';
                    
                    if (field.type === 'select') {
                        const options = field.options.map(option => {
                            return `<option value="${option}" ${value === option ? 'selected' : ''}>${option}</option>`;
                        }).join('');
                        fieldHtml = `
                            <div class="form-group">
                                <label for="${field.name}">${field.label}</label>
                                <select id="${field.name}" name="${field.name}" class="form-control" ${field.required ? 'required' : ''}>
                                    ${options}
                                </select>
                            </div>
                        `;
                    } else if (field.type === 'textarea') {
                        fieldHtml = `
                            <div class="form-group">
                                <label for="${field.name}">${field.label}</label>
                                <textarea id="${field.name}" name="${field.name}" class="form-control" ${field.required ? 'required' : ''}>${value || ''}</textarea>
                            </div>
                        `;
                    } else if (field.type === 'contacts') {
                        fieldHtml = `
                            <div class="form-group">
                                <label>${field.label}</label>
                                <div id="contacts-list"></div>
                                <button type="button" class="btn btn-outline btn-sm" onclick="addContactRow()">+ 添加联系人</button>
                            </div>
                        `;
                    } else {
                        fieldHtml = `
                            <div class="form-group">
                                <label for="${field.name}">${field.label}</label>
                                <input type="${field.type}" id="${field.name}" name="${field.name}" class="form-control" value="${value || ''}" ${field.required ? 'required' : ''} ${field.min ? `min="${field.min}"` : ''} ${field.max ? `max="${field.max}"` : ''}>
                            </div>
                        `;
                    }
                    
                    return fieldHtml;
                }).join('');

                if (currentTab === 'elderly') {
                    const contacts = Array.isArray(item?.contacts) && item.contacts.length
                        ? item.contacts
                        : (item?.emergency_contact ? [{ relation: '家属', name: item.emergency_contact, phone: item.emergency_phone || '' }] : [{ relation: '家属', name: '', phone: '' }]);
                    const box = document.getElementById('contacts-list');
                    if (box) {
                        box.innerHTML = '';
                        contacts.forEach(c => addContactRow(c));
                    }
                }
                
                modal.classList.add('show');
            }

            function addContactRow(data = {}) {
                const box = document.getElementById('contacts-list');
                if (!box) return;
                const row = document.createElement('div');
                row.className = 'form-row';
                row.style.marginBottom = '8px';
                row.innerHTML = `
                    <div class="form-group" style="flex:1">
                        <input class="form-control contact-relation" placeholder="关系(儿子/女儿/配偶等)" value="${data.relation || '家属'}">
                    </div>
                    <div class="form-group" style="flex:1">
                        <input class="form-control contact-name" placeholder="姓名" value="${data.name || ''}">
                    </div>
                    <div class="form-group" style="flex:1">
                        <input class="form-control contact-phone" placeholder="电话" value="${data.phone || ''}">
                    </div>
                    <div class="form-group" style="width:80px">
                        <button type="button" class="btn btn-outline btn-sm" onclick="this.closest('.form-row').remove()">删除</button>
                    </div>
                `;
                box.appendChild(row);
            }

            function collectContacts() {
                const rows = Array.from(document.querySelectorAll('#contacts-list .form-row'));
                return rows.map(row => ({
                    relation: row.querySelector('.contact-relation')?.value?.trim() || '家属',
                    name: row.querySelector('.contact-name')?.value?.trim() || '',
                    phone: row.querySelector('.contact-phone')?.value?.trim() || ''
                })).filter(c => c.name);
            }
            
            function closeModal() {
                const modal = document.getElementById('edit-modal');
                modal.classList.remove('show');
                editingItem = null;
            }
            
            async function saveItem() {
                const form = document.getElementById('edit-form');
                const formData = new FormData(form);
                const data = Object.fromEntries(formData);
                
                const config = tabConfig[currentTab];
                if (currentTab === 'elderly') {
                    const contacts = collectContacts();
                    if (!contacts.length) {
                        showMessage('请至少添加1位家属/联系人');
                        return;
                    }
                    data.contacts = contacts;
                    if (!data.emergency_contact) data.emergency_contact = contacts[0].name || '';
                    if (!data.emergency_phone) data.emergency_phone = contacts[0].phone || '';
                }
                if (['doctors', 'devices', 'alerts', 'orders', 'visits', 'elderly'].includes(currentTab)) {
                    ['elderly_id', 'doctor_id', 'alert_id', 'nurse_id', 'rating', 'battery_level', 'alert_level'].forEach(k => {
                        if (data[k] !== undefined && data[k] !== '') data[k] = Number(data[k]);
                        if (data[k] === '') delete data[k];
                    });
                }
                
                try {
                    let response;
                    if (editingItem) {
                        response = await fetch(config.api.update(editingItem.id), {
                            method: 'PUT',
                            credentials: 'include',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(data)
                        });
                    } else {
                        response = await fetch(config.api.create, {
                            method: 'POST',
                            credentials: 'include',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(data)
                        });
                    }
                    
                    const result = await response.json();
                    if (result.success) {
                        closeModal();
                        fetchData();
                        showMessage(editingItem ? '更新成功' : '新增成功');
                    } else {
                        showMessage('操作失败: ' + (result.message || '未知错误'));
                    }
                } catch (error) {
                    showMessage('网络错误: ' + error.message);
                }
            }
            
            async function deleteItem(id) {
                if (!confirm('确定要删除吗？')) return;
                
                const config = tabConfig[currentTab];
                
                try {
                    const response = await fetch(config.api.delete(id), {
                        method: 'DELETE',
                        credentials: 'include'
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        fetchData();
                        showMessage('删除成功');
                    } else {
                        showMessage('删除失败: ' + (result.message || '未知错误'));
                    }
                } catch (error) {
                    showMessage('网络错误: ' + error.message);
                }
            }
            
            function editItem(id) {
                const item = currentData.find(item => item.id === id);
                if (item) {
                    openModal('编辑' + tabConfig[currentTab].title, item);
                }
            }
            
            function showMessage(message) {
                alert(message);
            }

            
            function switchTab(tab) {
                currentTab = tab;
                
                // 更新标签状态
                document.querySelectorAll('.nav-tab').forEach(t => {
                    t.classList.remove('active');
                });
                document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
                
                // 更新页面标题
                document.getElementById('page-title').textContent = tabConfig[tab].title;
                
                // 清空搜索
                document.getElementById('search-input').value = '';
                document.getElementById('status-filter').innerHTML = '<option value="">全部状态</option>';
                
                // 加载数据
                fetchData();
            }
            
            // 事件监听
            document.getElementById('search-btn').addEventListener('click', filterData);
            document.getElementById('search-input').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') filterData();
            });
            document.getElementById('status-filter').addEventListener('change', filterData);
            
            document.getElementById('add-btn').addEventListener('click', () => {
                const config = tabConfig[currentTab];
                if (config.api.create) {
                    openModal('新增' + config.title.replace('管理', ''));
                } else {
                    showMessage('当前模块不支持新增');
                }
            });
            
            document.getElementById('refresh-btn').addEventListener('click', fetchData);
            
            document.getElementById('close-modal').addEventListener('click', closeModal);
            document.getElementById('cancel-btn').addEventListener('click', closeModal);
            document.getElementById('save-btn').addEventListener('click', saveItem);
            
            document.querySelectorAll('.nav-tab').forEach(tab => {
                tab.addEventListener('click', () => {
                    switchTab(tab.dataset.tab);
                });
            });
            
            // 初始化
            fetchData();
        </script>
    </body>
    </html>
    """
    return HttpResponse(html, content_type="text/html; charset=utf-8")


def db_admin_page(_request):
    html = """
    <html><head><meta charset="utf-8"><title>数据库可视化</title>
    <style>
    body{font-family:'Microsoft YaHei',Arial;background:#f4f6fb;margin:0;padding:16px;color:#1f2937;}
    .layout{display:grid;grid-template-columns:320px 1fr;gap:12px;max-width:1400px;margin:0 auto;}
    .card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:12px;}
    h2{margin:0 0 8px;font-size:18px;} .hint{color:#667085;font-size:12px;margin:4px 0 10px;}
    .table-item{padding:8px;border:1px solid #edf0f5;border-radius:8px;cursor:pointer;margin-bottom:8px;}
    .table-item:hover,.table-item.active{background:#eef4ff;border-color:#bfd4ff;}
    .badge{font-size:11px;background:#edf2ff;color:#3b4f73;border-radius:10px;padding:2px 8px;}
    .toolbar{display:flex;gap:8px;align-items:center;margin-bottom:10px;}
    input,button{padding:8px 10px;border:1px solid #d7dce5;border-radius:8px;}
    button{background:#1e3c72;color:#fff;border-color:#1e3c72;cursor:pointer;}
    table{width:100%;border-collapse:collapse;font-size:12px;}
    th,td{border:1px solid #eceff5;padding:6px;text-align:left;vertical-align:top;}
    th{background:#f8fafc;position:sticky;top:0;}
    .scroll{max-height:70vh;overflow:auto;}
    </style></head><body>
    <div class="layout">
      <div class="card">
        <h2>数据库表</h2>
        <div class="hint">仅管理员可访问。若显示未登录，请先在系统登录。</div>
        <div id="tables">加载中...</div>
      </div>
      <div class="card">
        <h2 id="title">数据预览</h2>
        <div class="toolbar">
          <label>每页 <input id="limit" type="number" value="50" min="1" max="200" style="width:80px;"></label>
          <label>偏移 <input id="offset" type="number" value="0" min="0" style="width:90px;"></label>
          <button id="reloadBtn">刷新</button>
        </div>
        <div id="meta" class="hint">请选择左侧数据表</div>
        <div class="scroll"><table id="grid"></table></div>
      </div>
    </div>
    <script>
      let schema = [];
      let currentTable = "";
      async function req(url){
        const r = await fetch(url, {credentials:'include'});
        const j = await r.json();
        if(!r.ok || !j.success) throw new Error(j.message || '请求失败');
        return j.data;
      }
      function renderTables(){
        const el = document.getElementById('tables');
        if(!schema.length){ el.innerHTML = '<div class="hint">暂无表</div>'; return; }
        el.innerHTML = schema.map(s => `<div class="table-item ${currentTable===s.table?'active':''}" data-t="${s.table}">
          <div><strong>${s.table}</strong> <span class="badge">${s.rows} rows</span></div>
          <div class="hint">${s.columns.map(c=>c.name).slice(0,4).join(', ')}${s.columns.length>4?'...':''}</div>
        </div>`).join('');
        el.querySelectorAll('.table-item').forEach(n=>n.onclick=()=>{currentTable=n.dataset.t;loadTable();renderTables();});
      }
      function renderGrid(data){
        const grid = document.getElementById('grid');
        const cols = data.columns || [];
        const rows = data.rows || [];
        if(!cols.length){ grid.innerHTML=''; return; }
        const th = '<tr>'+cols.map(c=>`<th>${c}</th>`).join('')+'</tr>';
        const tr = rows.map(r=>'<tr>'+cols.map(c=>`<td>${r[c]===null?'':String(r[c])}</td>`).join('')+'</tr>').join('');
        grid.innerHTML = '<thead>'+th+'</thead><tbody>'+tr+'</tbody>';
        document.getElementById('meta').textContent = `总行数 ${data.total}，当前展示 ${rows.length} 行`;
        document.getElementById('title').textContent = `数据预览：${data.table}`;
      }
      async function loadSchema(){ schema = await req('/api/db/schema'); if(!currentTable && schema.length) currentTable = schema[0].table; renderTables(); }
      async function loadTable(){ if(!currentTable) return; const limit = Number(document.getElementById('limit').value || 50); const offset = Number(document.getElementById('offset').value || 0); const data = await req(`/api/db/table-preview?table=${encodeURIComponent(currentTable)}&limit=${limit}&offset=${offset}`); renderGrid(data); }
      document.getElementById('reloadBtn').onclick = ()=>loadTable().catch(e=>alert(e.message));
      loadSchema().then(loadTable).catch(e=>{ document.getElementById('tables').innerHTML = `<div class="hint">加载失败：${e.message}</div>`; });
    </script>
    </body></html>
    """
    return HttpResponse(html, content_type="text/html; charset=utf-8")


def health(_request):
    return JsonResponse({"success": True, "message": "Django backend is running"})


urlpatterns = [
    path("", root),
    path("admin-pages", admin_pages),
    path("db-admin", db_admin_page),
    path("health", health),
    path("api/", include("api.urls")),
]
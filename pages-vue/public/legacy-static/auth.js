const rolePermissions = {
    admin: {
        name: '管理员',
        description: '拥有系统全部功能权限',
        permissions: ['dashboard', 'elderly-list', 'elderly-detail', 'orders', 'alerts', 'visit-plan', 'devices', 'doctors', 'reports', 'ai-risk-warning', 'ai-diagnosis', 'settings'],
        color: '#ff4757'
    },
    doctor: {
        name: '医生',
        description: '派医工单、健康数据查看、处置记录',
        permissions: ['dashboard', 'elderly-list', 'elderly-detail', 'orders', 'alerts', 'reports', 'ai-risk-warning', 'ai-diagnosis'],
        color: '#3498db'
    },
    nurse: {
        name: '护理员',
        description: '巡访计划、日常关怀、设备查看',
        permissions: ['dashboard', 'elderly-list', 'elderly-detail', 'visit-plan', 'devices', 'alerts', 'ai-risk-warning', 'ai-diagnosis'],
        color: '#27ae60'
    },
    service: {
        name: '客服',
        description: '家属沟通、通知推送',
        permissions: ['dashboard', 'elderly-list', 'elderly-detail', 'alerts', 'reports', 'ai-risk-warning', 'ai-diagnosis'],
        color: '#f39c12'
    }
};

const pageNames = {
    'dashboard.html': '控制台',
    'elderly-list.html': '老年人列表',
    'orders.html': '派医工单',
    'alerts.html': '警报中心',
    'visit-plan.html': '巡访计划',
    'devices.html': '设备管理',
    'doctors.html': '医生管理',
    'reports.html': '数据报告',
    'settings.html': '系统设置',
    'ai-risk-warning.html': 'AI健康风险预警',
    'ai-diagnosis.html': 'AI辅助诊断'
};

function getCurrentUser() {
    const userStr = localStorage.getItem('currentUser');
    if (!userStr) {
        return null;
    }
    return JSON.parse(userStr);
}

function hasPermission(permission) {
    if (!permission) return true;
    const user = getCurrentUser();
    if (!user) return false;
    const role = rolePermissions[user.role] || rolePermissions.admin;
    return Array.isArray(role.permissions) && role.permissions.includes(permission);
}

function hasRole(...roles) {
    const user = getCurrentUser();
    if (!user) return false;
    return roles.includes(user.role);
}

function checkAuth() {
    const user = getCurrentUser();
    if (!user) {
        window.top.location.href = '/login';
        return false;
    }
    return user;
}

function logout() {
    if (confirm('确认退出当前账号吗？退出后需要重新登录。')) {
        localStorage.removeItem('currentUser');
        window.top.location.href = '/login';
    }
}

function createNavBar() {
    const user = checkAuth();
    if (!user) return;

    const role = rolePermissions[user.role] || rolePermissions.admin;
    const currentPage = window.location.pathname.split('/').pop();
    const pageName = pageNames[currentPage] || '未知页面';

    const navBar = document.createElement('div');
    navBar.id = 'globalNavBar';
    navBar.innerHTML = `
        <style>
            :root {
                --app-bg: #f3f6fb;
                --app-card: #ffffff;
                --app-text: #1f2937;
                --app-text-sub: #6b7280;
                --app-border: #dbe3ef;
                --app-primary: #2563eb;
                --app-primary-hover: #1d4ed8;
                --app-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
                --app-radius: 12px;
            }
            body {
                background: linear-gradient(180deg, #eef3fb 0%, #f8fafc 100%) !important;
                color: var(--app-text);
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Microsoft YaHei", sans-serif;
            }
            body > .header {
                max-width: 1200px;
                margin: 14px auto 0;
                border-radius: 14px;
                border: 1px solid var(--app-border);
                background: var(--app-card) !important;
                box-shadow: var(--app-shadow);
                color: var(--app-text) !important;
            }
            body > .header h1, body > .header p {
                color: inherit !important;
            }
            body > .container {
                max-width: 1200px;
                margin: 16px auto 24px;
            }
            .card, .stat-card, .chart-card, .table-card, .list-card, .summary-card, .info-card {
                border: 1px solid var(--app-border) !important;
                border-radius: var(--app-radius) !important;
                box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06) !important;
                background: var(--app-card) !important;
            }
            .card:hover, .stat-card:hover {
                transform: translateY(-2px);
                transition: all 0.2s ease;
            }
            .btn, button, .nav-btn, input[type="button"], input[type="submit"] {
                border-radius: 10px !important;
            }
            .btn-primary, button.btn-primary {
                background: var(--app-primary) !important;
                border-color: var(--app-primary) !important;
            }
            .btn-primary:hover, button.btn-primary:hover {
                background: var(--app-primary-hover) !important;
            }
            input, select, textarea {
                border: 1px solid var(--app-border) !important;
                border-radius: 10px !important;
                color: var(--app-text) !important;
                background: #fff !important;
            }
            input:focus, select:focus, textarea:focus {
                outline: none;
                border-color: var(--app-primary) !important;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.14) !important;
            }
            table {
                border-collapse: collapse;
            }
            th, td {
                border-color: #e5e7eb !important;
            }
            th {
                background: #f8fafc !important;
                color: #334155 !important;
            }
            #globalNavBar {
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 12px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: sticky;
                top: 0;
                z-index: 1000;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            #globalNavBar .nav-left {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            #globalNavBar .nav-logo {
                font-size: 18px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            #globalNavBar .nav-breadcrumb {
                font-size: 13px;
                opacity: 0.8;
            }
            #globalNavBar .nav-breadcrumb a {
                color: white;
                text-decoration: none;
            }
            #globalNavBar .nav-breadcrumb a:hover {
                text-decoration: underline;
            }
            #globalNavBar .nav-right {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            #globalNavBar .user-info {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            #globalNavBar .user-avatar {
                width: 35px;
                height: 35px;
                background: rgba(255,255,255,0.2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
            }
            #globalNavBar .user-name {
                font-size: 14px;
            }
            #globalNavBar .role-badge {
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 500;
            }
            #globalNavBar .nav-btn {
                padding: 8px 14px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.3s;
                display: flex;
                align-items: center;
                gap: 5px;
            }
            #globalNavBar .nav-btn-outline {
                background: transparent;
                border: 1px solid rgba(255,255,255,0.5);
                color: white;
            }
            #globalNavBar .nav-btn-outline:hover {
                background: rgba(255,255,255,0.1);
            }
            #globalNavBar .nav-btn-danger {
                background: rgba(255,71,87,0.8);
                color: white;
            }
            #globalNavBar .nav-btn-danger:hover {
                background: #ff4757;
            }
            #globalNavBar .nav-btn-back {
                background: rgba(255,255,255,0.12);
                border: 1px solid rgba(255,255,255,0.45);
                color: white;
            }
            #globalNavBar .nav-btn-back:hover {
                background: rgba(255,255,255,0.22);
            }
            @media (max-width: 768px) {
                #globalNavBar {
                    flex-direction: column;
                    gap: 10px;
                    padding: 10px 15px;
                }
                #globalNavBar .nav-left {
                    width: 100%;
                    justify-content: space-between;
                }
                #globalNavBar .nav-right {
                    width: 100%;
                    justify-content: space-between;
                }
            }
        </style>
        <div class="nav-left">
            <div class="nav-logo">
                <i class="fas fa-heartbeat"></i>
                <span>老年人监护系统</span>
            </div>
        </div>
        <div class="nav-right">
            <div class="user-info">
                <div class="user-avatar">
                    <i class="fas fa-user"></i>
                </div>
                <span class="user-name">${user.realName || user.username || '未命名用户'}</span>
                <span class="role-badge" style="background: ${role.color};">${role.name}</span>
            </div>
            <button class="nav-btn nav-btn-back" onclick="window.top.location.href='/home'">
                <i class="fas fa-arrow-left"></i> 返回首页
            </button>
            <button class="nav-btn nav-btn-danger" onclick="logout()">
                <i class="fas fa-sign-out-alt"></i> 退出
            </button>
        </div>
    `;

    document.body.insertBefore(navBar, document.body.firstChild);
}

function initAuth() {
    createNavBar();
    applyAccessControl();
}

function applyAccessControl() {
    const nodes = document.querySelectorAll('[data-require-role], [data-require-permission]');
    nodes.forEach((el) => {
        const needRoles = (el.dataset.requireRole || '').split(',').map((x) => x.trim()).filter(Boolean);
        const needPermission = (el.dataset.requirePermission || '').trim();
        const passRole = !needRoles.length || hasRole(...needRoles);
        const passPermission = !needPermission || hasPermission(needPermission);
        if (passRole && passPermission) return;
        if ('disabled' in el) {
            el.disabled = true;
        }
        el.classList.add('permission-disabled');
        el.style.opacity = '0.6';
        el.style.cursor = 'not-allowed';
        if (!el.title) el.title = '当前账号无权限';
        el.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            return false;
        }, true);
    });
}

function requirePagePermission(permission) {
    const user = checkAuth();
    if (!user) return false;
    if (!hasPermission(permission)) {
        alert('当前账号暂未开通该模块权限，请联系管理员处理。');
        window.top.location.href = '/home';
        return false;
    }
    return true;
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAuth);
} else {
    initAuth();
}

window.getCurrentUser = getCurrentUser;
window.hasPermission = hasPermission;
window.hasRole = hasRole;
window.requirePagePermission = requirePagePermission;
window.applyAccessControl = applyAccessControl;

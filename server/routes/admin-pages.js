const express = require('express');
const router = express.Router();
const { all, get, run } = require('../config/database');

function layout(title, content, currentPath = '/admin-pages') {
    const navItems = [
        { href: '/admin-pages', label: '数据总览', icon: '📊' },
        { href: '/admin-pages/elderly', label: '老人管理', icon: '👴' },
        { href: '/admin-pages/doctors', label: '医生管理', icon: '👨‍⚕️' },
        { href: '/admin-pages/devices', label: '设备管理', icon: '📱' },
        { href: '/admin-pages/alerts', label: '警报管理', icon: '⚠️' },
        { href: '/admin-pages/orders', label: '工单管理', icon: '📋' },
        { href: '/admin-pages/visits', label: '巡访管理', icon: '🏥' }
    ];
    const currentItem = navItems.find((item) => item.href === currentPath) || navItems[0];
    const navHtml = navItems
        .map((item) => {
            const active = item.href === currentPath ? 'active' : '';
            return `<a class="${active}" href="${item.href}"><span class="nav-icon">${item.icon}</span><span>${item.label}</span></a>`;
        })
        .join('');

    return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${title}</title>
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
      margin: 0;
      background: #f0f2f5;
      color: #333;
      line-height: 1.5;
    }
    .shell {
      max-width: 1480px;
      margin: 0 auto;
      padding: 20px 24px 28px;
      display: flex;
      gap: 20px;
      min-height: 100vh;
    }
    .wrap { 
      flex: 1; 
      min-width: 0;
      display: flex;
      flex-direction: column;
    }
    .sidebar {
      width: 280px;
      min-height: calc(100vh - 40px);
      position: sticky;
      top: 20px;
      background: #ffffff;
      border-radius: 16px;
      border: 1px solid #e1e5e9;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
      padding: 24px;
    }
    .sidebar h3 {
      margin: 0 0 8px;
      font-size: 18px;
      color: #1a202c;
      font-weight: 700;
    }
    .sidebar-sub {
      margin: 0 0 24px;
      font-size: 13px;
      color: #718096;
    }
    .system-head {
      background: #ffffff;
      border: 1px solid #e1e5e9;
      border-radius: 16px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
      padding: 20px 24px;
      margin-bottom: 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
    }
    .system-title {
      font-size: 24px;
      font-weight: 700;
      color: #1a202c;
    }
    .system-meta {
      font-size: 14px;
      color: #718096;
    }
    h1 { 
      margin: 0 0 12px; 
      font-size: 28px;
      color: #1a202c;
      font-weight: 700;
    }
    .sub { 
      margin: 0 0 24px; 
      color: #718096; 
      font-size: 14px;
    }
    .crumb {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      margin-bottom: 16px;
      background: #ebf8ff;
      border: 1px solid #bee3f8;
      border-radius: 999px;
      font-size: 13px;
      color: #2b6cb0;
      font-weight: 600;
    }
    .nav { 
      display: flex; 
      flex-direction: column; 
      gap: 8px;
    }
    .nav a {
      text-decoration: none;
      color: #4a5568;
      background: #f7fafc;
      border: 1px solid #e2e8f0;
      padding: 12px 16px;
      min-height: 48px;
      border-radius: 12px;
      font-size: 14px;
      font-weight: 600;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .nav-icon {
      font-size: 16px;
      flex: 0 0 auto;
    }
    .nav a:hover {
      background: #e6fffa;
      border-color: #b2f5ea;
      color: #22543d;
      transform: translateY(-1px);
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
    }
    .nav a.active {
      color: #ffffff;
      border-color: #3182ce;
      background: linear-gradient(135deg, #3182ce, #2c5282);
      box-shadow: 0 6px 16px rgba(49, 130, 206, 0.3);
    }
    .card {
      background: #ffffff;
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
      border: 1px solid #e1e5e9;
      margin-bottom: 20px;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
      gap: 16px; 
      margin-bottom: 24px;
    }
    .stat {
      background: #f7fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 20px;
      transition: all 0.2s ease;
    }
    .stat:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08);
      border-color: #cbd5e0;
    }
    .stat .k {
      color: #718096;
      font-size: 14px;
      margin-bottom: 8px;
      font-weight: 500;
    }
    .stat .v {
      font-size: 32px;
      font-weight: 700;
      color: #1a202c;
      margin-bottom: 4px;
    }
    .stat .trend {
      font-size: 12px;
      color: #48bb78;
      font-weight: 600;
    }
    .table-wrap {
      overflow: auto; 
      background: #ffffff;
      border-radius: 16px;
      border: 1px solid #e1e5e9;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
      margin-bottom: 20px;
    }
    table {
      width: 100%; 
      border-collapse: collapse;
      font-size: 14px;
    }
    th, td {
      border-bottom: 1px solid #e2e8f0;
      padding: 12px 16px;
      text-align: left;
      white-space: nowrap;
    }
    th {
      background: #f7fafc;
      color: #4a5568;
      font-weight: 600;
      position: sticky;
      top: 0;
      z-index: 10;
      border-bottom: 2px solid #e2e8f0;
    }
    tr:hover td {
      background: #f7fafc;
    }
    tr:nth-child(even) {
      background: #f7fafc;
    }
    .muted {
      color: #718096;
      font-size: 14px;
      margin-top: 12px;
    }
    .actions {
      display: flex; 
      gap: 10px; 
      margin: 0 0 20px; 
      flex-wrap: wrap;
      align-items: center;
    }
    .btn {
      border: 0;
      border-radius: 10px;
      padding: 10px 16px;
      cursor: pointer;
      font-size: 14px;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-weight: 600;
      transition: all 0.2s ease;
    }
    .btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .btn.primary {
      background: #3182ce;
      color: #ffffff;
    }
    .btn.primary:hover {
      background: #2c5282;
    }
    .btn.secondary {
      background: #718096;
      color: #ffffff;
    }
    .btn.secondary:hover {
      background: #4a5568;
    }
    .btn.success {
      background: #38a169;
      color: #ffffff;
    }
    .btn.success:hover {
      background: #2f855a;
    }
    .btn.warning {
      background: #ed8936;
      color: #ffffff;
    }
    .btn.warning:hover {
      background: #c05621;
    }
    .btn.danger {
      background: #e53e3e;
      color: #ffffff;
    }
    .btn.danger:hover {
      background: #c53030;
    }
    .btn.light {
      background: #e2e8f0;
      color: #2d3748;
    }
    .btn.light:hover {
      background: #cbd5e0;
    }
    form.inline {
      display: inline;
    }
    .form-card {
      margin-top: 20px;
    }
    .form-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
      margin-bottom: 20px;
    }
    .form-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .form-group label {
      font-size: 14px;
      font-weight: 600;
      color: #4a5568;
    }
    .form-group input,
    .form-group select,
    .form-group textarea {
      width: 100%;
      padding: 10px 12px;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      font-size: 14px;
      transition: all 0.2s ease;
    }
    .form-group input:focus,
    .form-group select:focus,
    .form-group textarea:focus {
      outline: none;
      border-color: #3182ce;
      box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
    }
    .hint {
      font-size: 13px;
      color: #718096;
      margin-bottom: 16px;
    }
    .search-bar {
      display: flex;
      gap: 10px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }
    .search-input {
      flex: 1;
      min-width: 200px;
      padding: 10px 16px;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      font-size: 14px;
    }
    .search-input:focus {
      outline: none;
      border-color: #3182ce;
      box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
    }
    .pagination {
      display: flex;
      gap: 8px;
      margin-top: 20px;
      justify-content: center;
    }
    .page-btn {
      padding: 8px 12px;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      background: #ffffff;
      color: #4a5568;
      cursor: pointer;
      font-size: 14px;
      transition: all 0.2s ease;
    }
    .page-btn:hover {
      background: #f7fafc;
      border-color: #cbd5e0;
    }
    .page-btn.active {
      background: #3182ce;
      color: #ffffff;
      border-color: #3182ce;
    }
    .status-badge {
      padding: 4px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
      text-align: center;
    }
    .status-active {
      background: #c6f6d5;
      color: #276749;
    }
    .status-inactive {
      background: #fed7d7;
      color: #9b2c2c;
    }
    .status-pending {
      background: #feebc8;
      color: #9c4221;
    }
    .status-completed {
      background: #bee3f8;
      color: #2b6cb0;
    }
    @media (max-width: 1024px) {
      .shell {
        flex-direction: column;
      }
      .sidebar {
        width: 100%;
        min-height: auto;
        position: static;
      }
      .nav {
        flex-direction: row;
        overflow-x: auto;
        padding-bottom: 8px;
      }
      .nav a {
        white-space: nowrap;
      }
      .stats {
        grid-template-columns: repeat(2, 1fr);
      }
    }
    @media (max-width: 768px) {
      .system-head {
        flex-direction: column;
        align-items: flex-start;
      }
      .form-grid {
        grid-template-columns: 1fr;
      }
      .stats {
        grid-template-columns: 1fr;
      }
      .actions {
        flex-direction: column;
        align-items: stretch;
      }
      .btn {
        justify-content: center;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside class="sidebar">
      <h3>后端管理平台</h3>
      <p class="sidebar-sub">Elderly Monitoring Admin</p>
      <div class="nav">${navHtml}</div>
    </aside>
    <div class="wrap">
      <div class="system-head">
        <div class="system-title">老年人监护系统 · 后端管理</div>
        <div class="system-meta">数据维护与运营后台</div>
      </div>
      <div class="crumb">当前模块：${currentItem.label}</div>
      <h1>${title}</h1>
      <p class="sub">后端管理界面 · 面向数据维护与快速操作</p>
      ${content}
    </div>
  </div>
</body>
</html>`;
}

function table(headers, rows) {
    const thead = `<tr>${headers.map((h) => `<th>${h}</th>`).join('')}</tr>`;
    const tbody = rows.length
        ? rows.map((r) => `<tr>${r.map((c) => `<td>${c ?? ''}</td>`).join('')}</tr>`).join('')
        : '<tr><td colspan="99">暂无数据</td></tr>';
    return `<div class="table-wrap"><table><thead>${thead}</thead><tbody>${tbody}</tbody></table></div>`;
}

function sanitize(v) {
    return (v ?? '').toString().trim();
}

router.get('/', (req, res) => {
    const elderlyCount = all('SELECT COUNT(*) as c FROM elderly')[0]?.c || 0;
    const doctorCount = all('SELECT COUNT(*) as c FROM doctors')[0]?.c || 0;
    const deviceCount = all('SELECT COUNT(*) as c FROM devices')[0]?.c || 0;
    const alertCount = all('SELECT COUNT(*) as c FROM alerts')[0]?.c || 0;
    const orderCount = all('SELECT COUNT(*) as c FROM orders')[0]?.c || 0;
    const visitCount = all('SELECT COUNT(*) as c FROM visits')[0]?.c || 0;
    
    const activeAlerts = all('SELECT COUNT(*) as c FROM alerts WHERE status = "未处理"')[0]?.c || 0;
    const onlineDoctors = all('SELECT COUNT(*) as c FROM doctors WHERE status = "在线"')[0]?.c || 0;
    const onlineDevices = all('SELECT COUNT(*) as c FROM devices WHERE status = "在线"')[0]?.c || 0;

    const html = layout(
        '数据库数据总览',
        `<div class="card">
          <div class="stats">
            <div class="stat">
              <div class="k">老人数量</div>
              <div class="v">${elderlyCount}</div>
              <div class="trend">总计</div>
            </div>
            <div class="stat">
              <div class="k">医生数量</div>
              <div class="v">${doctorCount}</div>
              <div class="trend">在线: ${onlineDoctors}</div>
            </div>
            <div class="stat">
              <div class="k">设备数量</div>
              <div class="v">${deviceCount}</div>
              <div class="trend">在线: ${onlineDevices}</div>
            </div>
            <div class="stat">
              <div class="k">警报数量</div>
              <div class="v">${alertCount}</div>
              <div class="trend">未处理: ${activeAlerts}</div>
            </div>
            <div class="stat">
              <div class="k">工单数量</div>
              <div class="v">${orderCount}</div>
              <div class="trend">总计</div>
            </div>
            <div class="stat">
              <div class="k">巡访数量</div>
              <div class="v">${visitCount}</div>
              <div class="trend">总计</div>
            </div>
          </div>
          <div class="actions">
            <a class="btn primary" href="/admin-pages/elderly">管理老人</a>
            <a class="btn secondary" href="/admin-pages/doctors">管理医生</a>
            <a class="btn warning" href="/admin-pages/alerts">查看警报</a>
          </div>
          <p class="muted">这是后端直接渲染的管理界面，用于快速查看和管理数据库数据。</p>
        </div>`,
        req.path
    );
    res.send(html);
});

router.get('/elderly', (req, res) => {
    const rows = all('SELECT id, name, gender, phone, health_status, risk_level, address FROM elderly ORDER BY id DESC LIMIT 100');
    const html = layout('老人数据', table(
        ['ID', '姓名', '性别', '电话', '健康状态', '风险等级', '地址', '操作'],
        rows.map((r) => [
            r.id, r.name, r.gender, r.phone, r.health_status, r.risk_level, r.address,
            `<a class="btn light" href="/admin-pages/elderly/edit/${r.id}">编辑</a>
             <form class="inline" method="POST" action="/admin-pages/elderly/delete">
               <input type="hidden" name="id" value="${r.id}" />
               <button class="btn danger" type="submit" onclick="return confirm('确定删除该记录吗？')">删除</button>
             </form>`
        ])
    ) + `<div class="actions"><a class="btn primary" href="/admin-pages/elderly/new">新增老人</a></div>`,
    req.path);
    res.send(html);
});

router.get('/elderly/new', (req, res) => {
    const html = layout('新增老人', `
    <div class="card form-card">
      <form method="POST" action="/admin-pages/elderly/create">
        <div class="form-grid">
          <div class="form-group">
            <label>姓名</label>
            <input name="name" placeholder="请输入姓名" required />
          </div>
          <div class="form-group">
            <label>性别</label>
            <select name="gender"><option value="男">男</option><option value="女">女</option></select>
          </div>
          <div class="form-group">
            <label>电话</label>
            <input name="phone" placeholder="请输入电话号码" />
          </div>
          <div class="form-group">
            <label>地址</label>
            <input name="address" placeholder="请输入地址" />
          </div>
          <div class="form-group">
            <label>健康状态</label>
            <input name="health_status" placeholder="请输入健康状态" value="良好" />
          </div>
          <div class="form-group">
            <label>风险等级</label>
            <input name="risk_level" placeholder="请输入风险等级" value="低风险" />
          </div>
        </div>
        <div class="actions" style="margin-top:20px">
          <button class="btn primary" type="submit">保存</button>
          <a class="btn light" href="/admin-pages/elderly">返回</a>
        </div>
      </form>
    </div>
    `, req.path);
    res.send(html);
});

router.get('/elderly/edit/:id', (req, res) => {
    const id = parseInt(req.params.id, 10);
    const item = get('SELECT * FROM elderly WHERE id = ?', [id]);
    if (!item) return res.redirect('/admin-pages/elderly');
    const html = layout(`编辑老人 #${id}`, `
    <div class="card form-card">
      <form method="POST" action="/admin-pages/elderly/update">
        <input type="hidden" name="id" value="${item.id}" />
        <div class="form-grid">
          <div class="form-group">
            <label>姓名</label>
            <input name="name" value="${item.name || ''}" required />
          </div>
          <div class="form-group">
            <label>性别</label>
            <select name="gender"><option value="男" ${item.gender === '男' ? 'selected' : ''}>男</option><option value="女" ${item.gender === '女' ? 'selected' : ''}>女</option></select>
          </div>
          <div class="form-group">
            <label>电话</label>
            <input name="phone" value="${item.phone || ''}" />
          </div>
          <div class="form-group">
            <label>地址</label>
            <input name="address" value="${item.address || ''}" />
          </div>
          <div class="form-group">
            <label>健康状态</label>
            <input name="health_status" value="${item.health_status || '良好'}" />
          </div>
          <div class="form-group">
            <label>风险等级</label>
            <input name="risk_level" value="${item.risk_level || '低风险'}" />
          </div>
        </div>
        <div class="actions" style="margin-top:20px">
          <button class="btn primary" type="submit">保存修改</button>
          <a class="btn light" href="/admin-pages/elderly">返回</a>
        </div>
      </form>
    </div>
    `, req.path);
    res.send(html);
});

router.post('/elderly/create', (req, res) => {
    const name = sanitize(req.body.name);
    if (!name) return res.redirect('/admin-pages/elderly');
    run(
        `INSERT INTO elderly (name, gender, phone, address, health_status, risk_level)
         VALUES (?, ?, ?, ?, ?, ?)`,
        [
            name,
            sanitize(req.body.gender) || '男',
            sanitize(req.body.phone),
            sanitize(req.body.address),
            sanitize(req.body.health_status) || '良好',
            sanitize(req.body.risk_level) || '低风险'
        ]
    );
    res.redirect('/admin-pages/elderly');
});

router.post('/elderly/update', (req, res) => {
    const id = parseInt(req.body.id, 10);
    if (!id) return res.redirect('/admin-pages/elderly');
    run(
        `UPDATE elderly SET name = ?, gender = ?, phone = ?, address = ?, health_status = ?, risk_level = ?
         WHERE id = ?`,
        [
            sanitize(req.body.name),
            sanitize(req.body.gender) || '男',
            sanitize(req.body.phone),
            sanitize(req.body.address),
            sanitize(req.body.health_status) || '良好',
            sanitize(req.body.risk_level) || '低风险',
            id
        ]
    );
    res.redirect('/admin-pages/elderly');
});

router.post('/elderly/delete', (req, res) => {
    const id = parseInt(req.body.id, 10);
    if (id) {
        try {
            run('DELETE FROM elderly WHERE id = ?', [id]);
        } catch (error) {
            // 被外键引用时，后台删除采用“先清理关联再删除”
            run('DELETE FROM family_communication WHERE elderly_id = ?', [id]);
            run('DELETE FROM visits WHERE elderly_id = ?', [id]);
            run('DELETE FROM orders WHERE elderly_id = ?', [id]);
            run('DELETE FROM alerts WHERE elderly_id = ?', [id]);
            run('DELETE FROM health_data WHERE elderly_id = ?', [id]);
            run('DELETE FROM devices WHERE elderly_id = ?', [id]);
            run('DELETE FROM elderly WHERE id = ?', [id]);
        }
    }
    res.redirect('/admin-pages/elderly');
});

router.get('/doctors', (req, res) => {
    const rows = all('SELECT id, name, phone, specialization, status, rating FROM doctors ORDER BY id DESC LIMIT 100');
    const html = layout('医生数据', table(
        ['ID', '姓名', '电话', '专长', '状态', '评分', '操作'],
        rows.map((r) => [
            r.id, r.name, r.phone, r.specialization, r.status, r.rating,
            `<a class="btn light" href="/admin-pages/doctors/edit/${r.id}">编辑</a>
             <form class="inline" method="POST" action="/admin-pages/doctors/delete">
               <input type="hidden" name="id" value="${r.id}" />
               <button class="btn danger" type="submit" onclick="return confirm('确定删除该医生吗？')">删除</button>
             </form>`
        ])
    ) + `<div class="actions"><a class="btn primary" href="/admin-pages/doctors/new">新增医生</a></div>`,
    req.path);
    res.send(html);
});

router.get('/doctors/new', (req, res) => {
    const html = layout('新增医生', `
    <div class="card form-card">
      <form method="POST" action="/admin-pages/doctors/create">
        <div class="form-grid">
          <div class="form-group">
            <label>姓名</label>
            <input name="name" placeholder="请输入姓名" required />
          </div>
          <div class="form-group">
            <label>电话</label>
            <input name="phone" placeholder="请输入电话号码" />
          </div>
          <div class="form-group">
            <label>专长</label>
            <input name="specialization" placeholder="请输入专长" />
          </div>
          <div class="form-group">
            <label>状态</label>
            <select name="status"><option value="在线">在线</option><option value="忙碌">忙碌</option><option value="离线" selected>离线</option></select>
          </div>
          <div class="form-group">
            <label>评分</label>
            <input name="rating" value="5" />
          </div>
          <div class="form-group">
            <label>医院</label>
            <input name="hospital" placeholder="请输入医院" />
          </div>
        </div>
        <div class="actions" style="margin-top:20px">
          <button class="btn primary" type="submit">保存</button>
          <a class="btn light" href="/admin-pages/doctors">返回</a>
        </div>
      </form>
    </div>
    `, req.path);
    res.send(html);
});

router.get('/doctors/edit/:id', (req, res) => {
    const id = parseInt(req.params.id, 10);
    const item = get('SELECT * FROM doctors WHERE id = ?', [id]);
    if (!item) return res.redirect('/admin-pages/doctors');
    const html = layout(`编辑医生 #${id}`, `
    <div class="card form-card">
      <form method="POST" action="/admin-pages/doctors/update">
        <input type="hidden" name="id" value="${item.id}" />
        <div class="form-grid">
          <div class="form-group">
            <label>姓名</label>
            <input name="name" value="${item.name || ''}" required />
          </div>
          <div class="form-group">
            <label>电话</label>
            <input name="phone" value="${item.phone || ''}" />
          </div>
          <div class="form-group">
            <label>专长</label>
            <input name="specialization" value="${item.specialization || ''}" />
          </div>
          <div class="form-group">
            <label>状态</label>
            <select name="status"><option value="在线" ${item.status === '在线' ? 'selected' : ''}>在线</option><option value="忙碌" ${item.status === '忙碌' ? 'selected' : ''}>忙碌</option><option value="离线" ${item.status === '离线' ? 'selected' : ''}>离线</option></select>
          </div>
          <div class="form-group">
            <label>评分</label>
            <input name="rating" value="${item.rating || 5}" />
          </div>
          <div class="form-group">
            <label>医院</label>
            <input name="hospital" value="${item.hospital || ''}" />
          </div>
        </div>
        <div class="actions" style="margin-top:20px">
          <button class="btn primary" type="submit">保存修改</button>
          <a class="btn light" href="/admin-pages/doctors">返回</a>
        </div>
      </form>
    </div>
    `, req.path);
    res.send(html);
});

router.post('/doctors/create', (req, res) => {
    const name = sanitize(req.body.name);
    if (!name) return res.redirect('/admin-pages/doctors');
    run(
        `INSERT INTO doctors (name, phone, specialization, status, rating, hospital)
         VALUES (?, ?, ?, ?, ?, ?)`,
        [
            name,
            sanitize(req.body.phone),
            sanitize(req.body.specialization),
            sanitize(req.body.status) || '离线',
            Number(req.body.rating) || 5,
            sanitize(req.body.hospital)
        ]
    );
    res.redirect('/admin-pages/doctors');
});

router.post('/doctors/update', (req, res) => {
    const id = parseInt(req.body.id, 10);
    if (!id) return res.redirect('/admin-pages/doctors');
    run(
        `UPDATE doctors SET name = ?, phone = ?, specialization = ?, status = ?, rating = ?, hospital = ?
         WHERE id = ?`,
        [
            sanitize(req.body.name),
            sanitize(req.body.phone),
            sanitize(req.body.specialization),
            sanitize(req.body.status) || '离线',
            Number(req.body.rating) || 5,
            sanitize(req.body.hospital),
            id
        ]
    );
    res.redirect('/admin-pages/doctors');
});

router.post('/doctors/delete', (req, res) => {
    const id = parseInt(req.body.id, 10);
    if (id) {
        try {
            run('DELETE FROM doctors WHERE id = ?', [id]);
        } catch (error) {
            // 医生被工单引用时，先解绑工单再删除医生
            run('UPDATE orders SET doctor_id = NULL WHERE doctor_id = ?', [id]);
            run('DELETE FROM doctors WHERE id = ?', [id]);
        }
    }
    res.redirect('/admin-pages/doctors');
});

router.get('/devices', (req, res) => {
    const rows = all(`
        SELECT d.id, d.device_id, d.device_type, d.status, d.battery_level, d.last_online_at, e.name AS elderly_name
        FROM devices d
        LEFT JOIN elderly e ON e.id = d.elderly_id
        ORDER BY d.id DESC LIMIT 100
    `);
    const html = layout('设备数据', table(
        ['ID', '设备ID', '关联老人', '类型', '状态', '电量', '最后在线', '操作'],
        rows.map((r) => [
            r.id, r.device_id, r.elderly_name || '-', r.device_type, r.status, r.battery_level, r.last_online_at,
            `<a class="btn light" href="/admin-pages/devices/edit/${r.id}">编辑</a>`
        ])
    ) + `<div class="actions"><a class="btn primary" href="/admin-pages/devices/new">新增设备</a></div>`, req.path);
    res.send(html);
});

router.get('/devices/new', (req, res) => {
    const elderlyOptions = all('SELECT id, name FROM elderly ORDER BY id DESC LIMIT 300')
        .map((e) => `<option value="${e.id}">${e.name}（ID:${e.id}）</option>`)
        .join('');
    const html = layout('新增设备', `
    <div class="card form-card">
      <form method="POST" action="/admin-pages/devices/create">
        <div class="form-grid">
          <input name="device_id" placeholder="设备ID" required />
          <select name="elderly_id"><option value="">未关联</option>${elderlyOptions}</select>
          <input name="device_type" value="手表" />
          <select name="status"><option value="在线">在线</option><option value="离线" selected>离线</option><option value="故障">故障</option></select>
          <input name="battery_level" value="100" />
          <input name="last_online_at" placeholder="最后在线时间" />
        </div>
        <div class="actions" style="margin-top:20px">
          <button class="btn primary" type="submit">保存</button>
          <a class="btn light" href="/admin-pages/devices">返回</a>
        </div>
      </form>
    </div>
    `, req.path);
    res.send(html);
});

router.get('/devices/edit/:id', (req, res) => {
    const id = parseInt(req.params.id, 10);
    const item = get('SELECT * FROM devices WHERE id = ?', [id]);
    if (!item) return res.redirect('/admin-pages/devices');
    const elderlyOptions = all('SELECT id, name FROM elderly ORDER BY id DESC LIMIT 300')
        .map((e) => `<option value="${e.id}" ${Number(item.elderly_id) === Number(e.id) ? 'selected' : ''}>${e.name}（ID:${e.id}）</option>`)
        .join('');
    const html = layout(`编辑设备 #${id}`, `
    <div class="card form-card">
      <form method="POST" action="/admin-pages/devices/update">
        <input type="hidden" name="id" value="${item.id}" />
        <div class="form-grid">
          <input name="device_id" value="${item.device_id || ''}" required />
          <select name="elderly_id"><option value="">未关联</option>${elderlyOptions}</select>
          <input name="device_type" value="${item.device_type || '手表'}" />
          <select name="status"><option value="在线" ${item.status === '在线' ? 'selected' : ''}>在线</option><option value="离线" ${item.status === '离线' ? 'selected' : ''}>离线</option><option value="故障" ${item.status === '故障' ? 'selected' : ''}>故障</option></select>
          <input name="battery_level" value="${item.battery_level ?? 100}" />
          <input name="last_online_at" value="${item.last_online_at || ''}" />
        </div>
        <div class="actions" style="margin-top:20px">
          <button class="btn primary" type="submit">保存修改</button>
          <a class="btn light" href="/admin-pages/devices">返回</a>
        </div>
      </form>
    </div>
    `, req.path);
    res.send(html);
});

router.post('/devices/create', (req, res) => {
    const deviceId = sanitize(req.body.device_id);
    if (!deviceId) return res.redirect('/admin-pages/devices');
    run(
        `INSERT INTO devices (device_id, elderly_id, device_type, status, battery_level, last_online_at)
         VALUES (?, ?, ?, ?, ?, ?)`,
        [
            deviceId,
            Number(req.body.elderly_id) || null,
            sanitize(req.body.device_type) || '手表',
            sanitize(req.body.status) || '离线',
            Number(req.body.battery_level) || 100,
            sanitize(req.body.last_online_at) || null
        ]
    );
    res.redirect('/admin-pages/devices');
});

router.post('/devices/update', (req, res) => {
    const id = parseInt(req.body.id, 10);
    if (!id) return res.redirect('/admin-pages/devices');
    run(
        `UPDATE devices SET device_id = ?, elderly_id = ?, device_type = ?, status = ?, battery_level = ?, last_online_at = ? WHERE id = ?`,
        [
            sanitize(req.body.device_id),
            Number(req.body.elderly_id) || null,
            sanitize(req.body.device_type) || '手表',
            sanitize(req.body.status) || '离线',
            Number(req.body.battery_level) || 100,
            sanitize(req.body.last_online_at) || null,
            id
        ]
    );
    res.redirect('/admin-pages/devices');
});

router.get('/alerts', (req, res) => {
    const rows = all(`
        SELECT a.id, a.alert_type, a.alert_level, a.title, a.status, a.created_at, e.name AS elderly_name
        FROM alerts a
        LEFT JOIN elderly e ON e.id = a.elderly_id
        ORDER BY a.id DESC LIMIT 100
    `);
    const html = layout('警报数据', table(
        ['ID', '关联老人', '类型', '等级', '标题', '状态', '创建时间'],
        rows.map((r) => [
            r.id, r.elderly_name || '-', r.alert_type, r.alert_level, r.title, r.status, r.created_at
        ])
    ) + `<div class="actions"><a class="btn primary" href="/admin-pages/alerts/new">新增警报</a></div>`, req.path);
    res.send(html);
});

router.get('/alerts/new', (req, res) => {
    const elderlyOptions = all('SELECT id, name FROM elderly ORDER BY id DESC LIMIT 300')
        .map((e) => `<option value="${e.id}">${e.name}（ID:${e.id}）</option>`)
        .join('');
    const html = layout('新增警报', `
    <div class="card form-card">
      <form method="POST" action="/admin-pages/alerts/create">
        <div class="form-grid">
          <select name="elderly_id" required><option value="">请选择老人</option>${elderlyOptions}</select>
          <input name="alert_type" value="健康异常" />
          <input name="alert_level" value="1" />
          <input name="title" placeholder="标题" required />
          <select name="status"><option value="待处理">待处理</option><option value="处理中">处理中</option><option value="已处理">已处理</option></select>
          <input name="location" placeholder="位置" />
        </div>
        <div class="form-grid">
          <input name="content" placeholder="警报内容" />
        </div>
        <div class="actions" style="margin-top:20px">
          <button class="btn primary" type="submit">保存</button>
          <a class="btn light" href="/admin-pages/alerts">返回</a>
        </div>
      </form>
    </div>
    `, req.path);
    res.send(html);
});

router.post('/alerts/create', (req, res) => {
    const elderlyId = Number(req.body.elderly_id);
    const title = sanitize(req.body.title);
    if (!elderlyId || !title) return res.redirect('/admin-pages/alerts');
    run(
        `INSERT INTO alerts (elderly_id, alert_type, alert_level, title, content, location, status) VALUES (?, ?, ?, ?, ?, ?, ?)`,
        [elderlyId, sanitize(req.body.alert_type) || '健康异常', Number(req.body.alert_level) || 1, title, sanitize(req.body.content), sanitize(req.body.location), sanitize(req.body.status) || '待处理']
    );
    res.redirect('/admin-pages/alerts');
});

function genOrderNo() {
    const n = Date.now().toString().slice(-8);
    const r = Math.floor(Math.random() * 900 + 100);
    return `ORD${n}${r}`;
}

router.get('/orders', (req, res) => {
    const rows = all(`
        SELECT o.id, o.order_no, o.urgency, o.status, o.created_at,
               e.name AS elderly_name, d.name AS doctor_name
        FROM orders o
        LEFT JOIN elderly e ON e.id = o.elderly_id
        LEFT JOIN doctors d ON d.id = o.doctor_id
        ORDER BY o.id DESC LIMIT 100
    `);
    const html = layout('工单数据', table(
        ['ID', '工单号', '老人姓名', '医生姓名', '紧急度', '状态', '创建时间'],
        rows.map((r) => [
            r.id, r.order_no, r.elderly_name || '-', r.doctor_name || '-', r.urgency, r.status, r.created_at
        ])
    ) + `<div class="actions"><a class="btn primary" href="/admin-pages/orders/new">新增工单</a></div>`, req.path);
    res.send(html);
});

router.get('/orders/new', (req, res) => {
    const elderlyOptions = all('SELECT id, name FROM elderly ORDER BY id DESC LIMIT 300')
        .map((e) => `<option value="${e.id}">${e.name}（ID:${e.id}）</option>`)
        .join('');
    const doctorOptions = all('SELECT id, name FROM doctors ORDER BY id DESC LIMIT 300')
        .map((d) => `<option value="${d.id}">${d.name}（ID:${d.id}）</option>`)
        .join('');
    const alertOptions = all('SELECT id, title FROM alerts ORDER BY id DESC LIMIT 300')
        .map((a) => `<option value="${a.id}">${a.title}（ID:${a.id}）</option>`)
        .join('');
    const html = layout('新增工单', `
    <div class="card form-card">
      <form method="POST" action="/admin-pages/orders/create">
        <div class="form-grid">
          <input name="order_no" value="${genOrderNo()}" required />
          <select name="elderly_id" required><option value="">请选择老人</option>${elderlyOptions}</select>
          <select name="alert_id"><option value="">不关联警报</option>${alertOptions}</select>
          <select name="doctor_id"><option value="">暂不指定医生</option>${doctorOptions}</select>
          <select name="urgency"><option value="低">低</option><option value="一般" selected>一般</option><option value="高">高</option><option value="紧急">紧急</option></select>
          <select name="status"><option value="待接单">待接单</option><option value="已接单">已接单</option><option value="处置中">处置中</option><option value="已完成">已完成</option></select>
        </div>
        <div class="form-grid"><input name="description" placeholder="工单描述" /></div>
        <div class="actions" style="margin-top:20px">
          <button class="btn primary" type="submit">保存</button>
          <a class="btn light" href="/admin-pages/orders">返回</a>
        </div>
      </form>
    </div>
    `, req.path);
    res.send(html);
});

router.post('/orders/create', (req, res) => {
    const elderlyId = Number(req.body.elderly_id);
    if (!elderlyId) return res.redirect('/admin-pages/orders');
    run(
        `INSERT INTO orders (order_no, elderly_id, alert_id, doctor_id, urgency, description, status, result)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
        [
            sanitize(req.body.order_no) || genOrderNo(),
            elderlyId,
            Number(req.body.alert_id) || null,
            Number(req.body.doctor_id) || null,
            sanitize(req.body.urgency) || '一般',
            sanitize(req.body.description),
            sanitize(req.body.status) || '待接单',
            sanitize(req.body.result)
        ]
    );
    res.redirect('/admin-pages/orders');
});

router.get('/visits', (req, res) => {
    const rows = all(`
        SELECT v.id, v.plan_date, v.plan_time, v.status, v.created_at, e.name AS elderly_name, u.real_name AS nurse_name
        FROM visits v
        LEFT JOIN elderly e ON e.id = v.elderly_id
        LEFT JOIN users u ON u.id = v.nurse_id
        ORDER BY v.id DESC LIMIT 100
    `);
    const html = layout('巡访数据', table(
        ['ID', '老人姓名', '护士姓名', '计划日期', '计划时间', '状态', '创建时间'],
        rows.map((r) => [
            r.id, r.elderly_name || '-', r.nurse_name || '-', r.plan_date, r.plan_time, r.status, r.created_at
        ])
    ) + `<div class="actions"><a class="btn primary" href="/admin-pages/visits/new">新增巡访</a></div>`, req.path);
    res.send(html);
});

router.get('/visits/new', (req, res) => {
    const elderlyOptions = all('SELECT id, name FROM elderly ORDER BY id DESC LIMIT 300')
        .map((e) => `<option value="${e.id}">${e.name}（ID:${e.id}）</option>`)
        .join('');
    const nurseOptions = all(`SELECT id, real_name FROM users WHERE role = 'nurse' ORDER BY id DESC LIMIT 300`)
        .map((u) => `<option value="${u.id}">${u.real_name}（ID:${u.id}）</option>`)
        .join('');
    const html = layout('新增巡访', `
    <div class="card form-card">
      <form method="POST" action="/admin-pages/visits/create">
        <div class="form-grid">
          <select name="elderly_id" required><option value="">请选择老人</option>${elderlyOptions}</select>
          <select name="nurse_id" required><option value="">请选择护士</option>${nurseOptions}</select>
          <input name="plan_date" type="date" required />
          <input name="plan_time" type="time" />
          <select name="status"><option value="待执行">待执行</option><option value="执行中">执行中</option><option value="已完成">已完成</option><option value="已取消">已取消</option></select>
          <input name="visit_content" placeholder="巡访内容" />
        </div>
        <div class="actions" style="margin-top:20px">
          <button class="btn primary" type="submit">保存</button>
          <a class="btn light" href="/admin-pages/visits">返回</a>
        </div>
      </form>
    </div>
    `, req.path);
    res.send(html);
});

router.post('/visits/create', (req, res) => {
    const elderlyId = Number(req.body.elderly_id);
    const nurseId = Number(req.body.nurse_id);
    const planDate = sanitize(req.body.plan_date);
    if (!elderlyId || !nurseId || !planDate) return res.redirect('/admin-pages/visits');
    run(
        `INSERT INTO visits (elderly_id, nurse_id, plan_date, plan_time, status, visit_content)
         VALUES (?, ?, ?, ?, ?, ?)`,
        [elderlyId, nurseId, planDate, sanitize(req.body.plan_time) || null, sanitize(req.body.status) || '待执行', sanitize(req.body.visit_content)]
    );
    res.redirect('/admin-pages/visits');
});


module.exports = router;

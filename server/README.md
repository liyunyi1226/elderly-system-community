# 老年人监护系统 - 后端服务

## 技术栈

- 后端：Node.js + Express
- 数据库：SQLite（`server/data/elderly_monitoring.db`）
- 认证：Session + Cookie

## 快速开始

### 1) 安装依赖

```bash
cd server
npm install
```

### 2) 初始化数据库

```bash
npm run init-db
```

### 3) 启动服务

```bash
npm run dev
```

服务地址：`http://localhost:3000`

## 登录账号（当前环境）

> 当前环境密码统一为：`123456`

- `admin_system`（管理员）
- `nurse_lihushi`（护理员）
- `service_wangkefu`（客服）
- `doctor_zhangweiming`（医生）
- `doctor_lifanghua`（医生）
- `doctor_wangqiangjun`（医生）
- `doctor_chenjingyi`（医生）
- `doctor_zhouwenbo`（医生）
- `doctor_sunyaqin`（医生）

## 核心权限规则

- 登录采用个人账号（后端按账号返回角色）。
- 仅 `admin`、`service` 可创建工单（派医）。
- 医生可接单与更新本人负责工单状态，但不可派医。
- 医生查询工单时仅返回本人关联工单。
- 前端按钮置灰仅用于体验，后端接口负责最终权限校验。

## 主要 API

### 认证

- `POST /api/auth/login` 登录
- `POST /api/auth/logout` 登出
- `GET /api/auth/current` 当前用户

### 老人

- `GET /api/elderly/list`
- `GET /api/elderly/:id`
- `POST /api/elderly/create`
- `PUT /api/elderly/:id`
- `DELETE /api/elderly/:id`

### 告警

- `GET /api/alerts/list`
- `GET /api/alerts/statistics`
- `POST /api/alerts/create`
- `PUT /api/alerts/:id/handle`

### 工单

- `GET /api/orders/list`
- `POST /api/orders/create`
- `PUT /api/orders/:id/status`
- `PUT /api/orders/:id/complete`

### 设备

- `GET /api/devices/list`
- `GET /api/devices/statistics`
- `POST /api/devices/create`
- `PUT /api/devices/:id`
- `PUT /api/devices/:id/status`

### 医生

- `GET /api/doctors/list`
- `POST /api/doctors/create`
- `PUT /api/doctors/:id`
- `PUT /api/doctors/:id/status`

### 巡访

- `GET /api/visits/list`
- `POST /api/visits/create`
- `PUT /api/visits/:id/complete`

### 控制台

- `GET /api/dashboard/overview`
- `GET /api/dashboard/trend`

## 目录结构

```text
server/
├── config/
│   └── database.js
├── middleware/
│   └── auth.js
├── routes/
│   ├── auth.js
│   ├── elderly.js
│   ├── alerts.js
│   ├── orders.js
│   ├── devices.js
│   ├── doctors.js
│   ├── visits.js
│   └── dashboard.js
├── scripts/
│   └── initDatabase.js
├── data/
├── package.json
└── server.js
```

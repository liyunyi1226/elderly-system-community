# 老年人监护系统

本项目为社区老年人监护系统（本地部署版），当前包含两套可独立运行的入口：

- 前端业务端：`pages-vue`（Vue + Vite）
- 后端管理端：`server`（Node.js + Express + SQLite）
- 数据库：SQLite（`server/data/elderly_monitoring.db`）

## 快速开始

### 1) 启动后端

```bash
cd "d:\练习\oldsystem-main\server"
npm install
npm run init-db
npm run dev
```

后端访问地址：

- 根地址（默认跳转）：`http://localhost:3000/` -> `/admin-pages`
- 后端管理页面：`http://localhost:3000/admin-pages`
- API 基地址：`http://localhost:3000/api`

### 2) 启动前端

```bash
cd "d:\练习\oldsystem-main\pages-vue"
npm install
npm run dev
```

前端地址：

- 登录页：`http://localhost:5173/login`
- 首页：`http://localhost:5173/home`

> 说明：后端当前已取消旧静态页面挂载，仅保留 `admin-pages` 和 `api`。前端请通过 Vite 独立启动访问。

## 登录账号（当前可用）

> 当前环境密码统一为：`123456`

### 管理与服务账号

- 管理员：`admin_system`
- 护理员：`nurse_lihushi`
- 客服：`service_wangkefu`

### 医生账号

- `doctor_zhangweiming`（张伟明）
- `doctor_lifanghua`（李芳华）
- `doctor_wangqiangjun`（王强军）
- `doctor_chenjingyi`（陈静怡）
- `doctor_zhouwenbo`（周文博）
- `doctor_sunyaqin`（孙雅琴）

## 权限与业务规则（新系统）

- 登录方式：个人账号登录（不再手动选择角色）。
- 老人详情：所有角色可查看老人详情。
- 派医权限：仅 `admin`、`service` 可派医/创建工单。
- 医生权限：医生不能派医，但可在自己的工单中接单、更新状态、完成工单。
- 工单可见性：医生账号仅能看到“分配给自己”的工单。
- 按钮控制：无权限按钮统一置灰并禁用点击（前端展示 + 后端接口双重限制）。

## 当前后端管理端（/admin-pages）能力

- `老人管理`：增 / 删 / 改 / 查
- `医生管理`：增 / 删 / 改 / 查
- `设备管理`：增 / 改 / 查（不提供删除）
- `警报管理`：增 / 查（不提供编辑、删除）
- `工单管理`：增 / 查（不提供编辑、删除）
- `巡访管理`：增 / 查（不提供编辑、删除）

> 业务字段展示规则：后台列表优先展示“姓名”等业务字段，不以 ID 作为主要展示信息。

## 前端主要模块（pages-vue）

- 控制台
- 老年人列表
- 派医工单
- 警报中心
- 巡访计划
- 设备管理
- 医生管理
- 数据报告
- 系统设置
- AI 健康风险预警
- AI 辅助诊断

## 目录结构

```text
oldsystem-main/
├── pages-vue/
│   ├── src/
│   └── public/legacy-static/
├── server/
│   ├── config/
│   ├── routes/
│   ├── scripts/
│   ├── data/
│   └── server.js
└── README.md
```

## 常见问题

### 1) 端口占用（EADDRINUSE）

3000 或 5173 被占用时，先关闭占用进程再重启服务。

### 2) 登录失败 / 页面打不开

- 先确认后端服务在 `3000` 端口正常启动。
- 后端管理页使用 `http://localhost:3000/admin-pages`。
- 前端业务页需先启动 `pages-vue`，并通过 `http://localhost:5173/login` 进入。
- 前端建议强制刷新（`Ctrl + F5`）或用无痕窗口验证。

### 3) 数据异常

在 `server` 目录重新执行：

```bash
npm run init-db
```

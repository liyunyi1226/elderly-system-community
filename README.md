# 老年人监护系统（Django + Vue）

社区老年人健康与风险闭环管理系统，支持老人档案、医生/设备管理、告警闭环、工单调度、巡访执行、报表导出与 AI 辅助判别。

## 项目定位

- **应用场景**：社区网格化养老、居家健康监测、异常事件联动处置
- **技术栈**：`Vue 3 + Vite`（前端） + `Django + SQLite`（后端）
- **系统形态**：前后端分离 + 后端可视化管理页（`/admin-pages`）

## 快速启动

### 1) 启动后端

```bash
cd "d:\练习\oldsystem-main\server\django_backend"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:3000
```

后端使用入口（按当前要求）：

- `http://localhost:3000/admin-pages`（后端可视化管理）

### 2) 启动前端

```bash
cd "d:\练习\oldsystem-main\pages-vue"
npm install
npm run dev
```

前端入口：

- `http://localhost:5173/login`
- `http://localhost:5173/home`

## 目录结构

```text
oldsystem-main/
├── pages-vue/                      # Vue 前端
│   ├── src/                        # Vue 页面与服务层
│   └── public/legacy-static/       # 旧版静态页面（已动态化接后端）
├── server/
│   ├── data/elderly_monitoring.db  # 业务数据库（SQLite）
│   └── django_backend/             # Django 后端
│       ├── api/                    # 业务 API（auth/elderly/alerts/orders...）
│       └── django_backend/         # 路由与配置
├── render.yaml                     # 部署配置
└── README.md
```

## 系统结构

- **展示层（前端）**：登录、总览、老人/医生/设备/告警/工单/巡访、报表、AI 页面
- **管理层（后端页面）**：`/admin-pages` 提供模块化 CRUD 管理
- **业务层（API）**：统一 `api/views.py` 实现业务流程与权限校验
- **数据层（SQLite）**：老人、联系人、沟通记录、告警、工单、巡访、设备、事件追踪
- **智能层（AI）**：LLM 推理 + 规则兜底，保障“可用、可解释、可降级”

## 前端模块说明（业务视角）

- **登录与权限**
  - 用户按账号登录，后端基于角色控制可见菜单与接口权限
- **首页总览（Dashboard）**
  - 查看老人数量、告警态势、工单趋势、设备在线情况
- **老年人管理**
  - 老人档案维护（基础信息、病史、过敏、用药、网格、重点标签）
  - 支持多联系人与沟通记录联动
- **老年人详情**
  - 展示老人体征、设备、告警、沟通记录与 AI 风险信息
- **医生管理**
  - 维护医生信息、专长、状态与评分
- **设备管理**
  - 维护设备绑定关系、状态、电量与遥测入库
- **告警中心**
  - 展示告警、AI 分级、置信度与处置状态
- **工单管理**
  - 创建并查看工单，支撑派单与执行记录
- **巡访计划**
  - 创建巡访并查看执行结果
- **数据报表**
  - 查看统计数据并导出 CSV、打印台账
- **AI 模块**
  - AI 风险预警与 AI 辅助诊断页面，支持 LLM + 规则兜底

## 智能体/AI 接入说明

系统已接入“**LLM + 规则兜底**”的智能能力：

- **AI 风险预警**：`/api/ai/risk`
- **AI 辅助诊断**：`/api/ai/diagnosis`
- **告警 AI 分级**：告警创建与自动预警时触发 AI 分级（含置信度、依据、来源）

### 运行机制

- 优先调用外部大模型（OpenAI 兼容接口）
- 若未配置或调用失败，自动回退到本地规则引擎

### 环境变量

- `LLM_API_KEY`
- `LLM_API_BASE`（默认 `https://api.openai.com/v1`）
- `LLM_MODEL`（默认 `gpt-4o-mini`）

## 典型业务情景（示例）

**场景：社区老人夜间心率异常，系统自动告警并形成闭环**

1. 设备上传老人体征（心率/血氧等）  
2. 后端写入健康数据并触发自动预警  
3. AI 模块给出告警分级、置信度和判断依据  
4. 告警进入处置流程，生成或关联工单  
5. 医护执行上门处置并回填结果  
6. 系统记录通知与事件链路（`event_id`）  
7. 报表模块统计本次事件，纳入社区台账

## 账号与权限（当前库中账号）

当前账号来自 `users` 表，用户名如下：

- 管理员：`admin_system`
- 护士：`nurse_lihushi`
- 客服：`service_wangkefu`
- 医生：`doctor_zhangweiming`、`doctor_lifanghua`、`doctor_wangqiangjun`、`doctor_chenjingyi`、`doctor_zhouwenbo`、`doctor_sunyaqin`

> 密码为123456。

## 常见问题

- **页面没更新**：先 `Ctrl + F5` 强刷，必要时重启 Django
- **后端启动失败**：确认已激活 `.venv` 且安装 `requirements.txt`
- **端口占用**：释放 `3000/5173` 后重启
- **数据异常**：检查 `server/data/elderly_monitoring.db` 是否存在并可读

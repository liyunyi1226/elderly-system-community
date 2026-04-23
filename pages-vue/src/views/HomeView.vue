<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";
import { rolePermissions } from "../config/roles";

const router = useRouter();
const user = computed(() => JSON.parse(localStorage.getItem("currentUser") || "{}"));
const role = computed(() => rolePermissions[user.value.role] || rolePermissions.admin);

const permissions = computed(() => role.value.permissions || []);

const corePages = [
  { key: "dashboard", title: "控制台", desc: "查看今日预警、待办工单与关键统计", page: "dashboard", icon: "fas fa-chart-line" },
  { key: "elderly-list", title: "老年人列表", desc: "维护基础信息并查看健康档案", page: "elderly-list", icon: "fas fa-users" },
  { key: "orders", title: "派医工单", desc: "创建、分派并跟踪处置进度", page: "orders", icon: "fas fa-clipboard-list" },
  { key: "alerts", title: "警报中心", desc: "集中处理紧急告警与事件记录", page: "alerts", icon: "fas fa-bell" }
];

const supportPages = [
  { key: "visit-plan", title: "巡访计划", desc: "安排巡访任务并记录执行情况", page: "visit-plan", icon: "fas fa-calendar-check" },
  { key: "devices", title: "设备管理", desc: "查看设备状态并处理异常上报", page: "devices", icon: "fas fa-microchip" },
  { key: "doctors", title: "医生管理", desc: "管理医生档案与在线状态", page: "doctors", icon: "fas fa-user-md" },
  { key: "reports", title: "数据报告", desc: "导出统计报表并跟踪趋势变化", page: "reports", icon: "fas fa-chart-bar" },
  { key: "settings", title: "系统设置", desc: "维护预警阈值与通知策略", page: "settings", icon: "fas fa-cog" }
];

const aiPages = [
  { key: "ai-risk-warning", title: "健康风险预警", desc: "结合多维数据识别高风险人群", page: "ai-risk-warning", icon: "fas fa-shield-alt" },
  { key: "ai-diagnosis", title: "辅助诊断", desc: "提供病因分析与处置建议参考", page: "ai-diagnosis", icon: "fas fa-stethoscope" }
];

function openPage(page) {
  router.push(`/legacy/${page}`);
}

function logout() {
  // 上线场景下避免误触直接退出
  if (!window.confirm("确认退出当前账号吗？")) return;
  localStorage.removeItem("currentUser");
  router.push("/login");
}
</script>

<template>
  <div class="home-page">
    <div class="container">
      <div class="top-bar">
        <div class="user-info">
          <div class="user-avatar">
            <i class="fas fa-user"></i>
          </div>
          <div class="user-details">
            <h4>{{ user.realName || user.username || "未命名用户" }}</h4>
            <p>{{ role.name }} · 已登录</p>
          </div>
        </div>
        <button class="logout-btn app-btn app-btn-danger" @click="logout">
          <i class="fas fa-sign-out-alt"></i>
          <span>退出登录</span>
        </button>
      </div>

      <div class="page-header">
        <h1>老年人监护系统</h1>
        <p>请按岗位职责处理预警、工单与巡访任务</p>
      </div>

      <div class="section">
        <div class="section-title">
          <h2>核心功能</h2>
        </div>
        <div class="grid">
          <div
            v-for="item in corePages"
            :key="item.key"
            class="card"
            :class="{ disabled: !permissions.includes(item.key) }"
            @click="permissions.includes(item.key) ? openPage(item.page) : null"
          >
            <div class="card-icon"><i :class="item.icon"></i></div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.desc }}</p>
          </div>
        </div>
      </div>

      <div class="section">
        <div class="section-title">
          <h2>辅助功能</h2>
        </div>
        <div class="grid">
          <div
            v-for="item in supportPages"
            :key="item.key"
            class="card"
            :class="{ disabled: !permissions.includes(item.key) }"
            @click="permissions.includes(item.key) ? openPage(item.page) : null"
          >
            <div class="card-icon"><i :class="item.icon"></i></div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.desc }}</p>
          </div>
        </div>
      </div>

      <div class="section ai-section">
        <div class="section-title">
          <h2><i class="fas fa-robot"></i> AI智能</h2>
        </div>
        <div class="grid ai-grid">
          <div
            v-for="item in aiPages"
            :key="item.key"
            class="card ai-card"
            :class="{ disabled: !permissions.includes(item.key) }"
            @click="permissions.includes(item.key) ? openPage(item.page) : null"
          >
            <div class="card-icon"><i :class="item.icon"></i></div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.desc }}</p>
            <span class="ai-badge">AI</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #eef3fb 0%, #f8fafc 100%);
  padding: 20px;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.top-bar {
  background: #fff;
  border-radius: 14px;
  padding: 15px 25px;
  margin-bottom: 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid #dbe3ef;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-avatar {
  width: 45px;
  height: 45px;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
}

.user-details h4 {
  margin: 0 0 3px;
  font-size: 15px;
  color: #333;
}

.user-details p {
  margin: 0;
  font-size: 12px;
  color: #666;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-header h1 {
  font-size: 36px;
  margin: 0 0 8px;
  color: #333;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  font-size: 16px;
  color: #4b5563;
}

.section {
  margin-bottom: 35px;
}

.section-title {
  margin-bottom: 20px;
}

.section-title h2 {
  font-size: 20px;
  margin: 0;
  color: #333;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 20px;
}

.card {
  background: #fff;
  border-radius: 12px;
  padding: 25px 20px;
  text-align: center;
  transition: all 0.3s;
  cursor: pointer;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
  border: 1px solid #dbe3ef;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.card.disabled {
  display: none;
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  margin: 0 auto 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  color: #fff;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
}

.card h3 {
  margin: 0 0 8px;
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

.card p {
  margin: 0;
  color: #666;
  font-size: 13px;
  line-height: 1.5;
}

.ai-section {
  margin-top: 40px;
}

.ai-card {
  position: relative;
}

.ai-card .card-icon {
  background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
}

.ai-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 10px;
  margin-top: 10px;
  font-weight: 600;
  background: linear-gradient(135deg, #0f766e 0%, #0d9488 100%);
  color: #fff;
}

@media (max-width: 768px) {
  .top-bar {
    flex-direction: column;
    gap: 15px;
  }

  .page-header h1 {
    font-size: 28px;
  }

  .grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
  }

  .card {
    padding: 20px 15px;
  }
}
</style>
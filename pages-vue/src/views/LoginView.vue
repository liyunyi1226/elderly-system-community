<script setup>
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../services/api";
import { rolePermissions } from "../config/roles";

const username = ref("");
const password = ref("");
const loading = ref(false);
const errorText = ref("");
const router = useRouter();
const roleHint = computed(() => {
  if (loading.value) return "正在验证账号与权限，请稍候";
  return "系统将根据账号自动识别身份并加载对应功能";
});

async function handleLogin() {
  errorText.value = "";
  if (!username.value || !password.value) {
    errorText.value = "请输入账号和密码后再登录。";
    return;
  }

  loading.value = true;
  try {
    const result = await api.auth.login(username.value, password.value);
    const role = rolePermissions[result.data.role] || rolePermissions.admin;
    localStorage.setItem(
      "currentUser",
      JSON.stringify({
        id: result.data.id,
        username: result.data.username,
        realName: result.data.realName,
        role: result.data.role,
        roleName: role.name,
        permissions: role.permissions,
        loginTime: new Date().toISOString()
      })
    );
    router.push("/home");
  } catch (error) {
    errorText.value = `登录失败：${error.message || "请检查账号密码或稍后重试。"}`;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card app-card">
      <div class="login-header">
        <h1>老年人监护系统</h1>
        <p>账号登录</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <p v-if="errorText" class="alert-inline error">{{ errorText }}</p>

        <div class="form-group">
          <label>账号</label>
          <input v-model="username" type="text" class="app-input" placeholder="请输入账号" required />
        </div>

        <div class="form-group">
          <label>密码</label>
          <input v-model="password" type="password" class="app-input" placeholder="请输入密码" required />
        </div>

        <p class="role-hint">{{ roleHint }}</p>

        <button type="submit" class="login-btn app-btn app-btn-primary" :disabled="loading">
          {{ loading ? "登录中..." : "登录" }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  padding: 16px;
}
.login-card {
  width: 100%;
  max-width: 380px;
  padding: 28px 24px;
  background: #fff;
}
.login-header {
  text-align: center;
  margin-bottom: 20px;
}
.login-header h1 {
  margin: 0 0 6px;
  font-size: 24px;
  color: #111827;
}
.login-header p {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}
.login-form {
  display: flex;
  flex-direction: column;
}
.form-group {
  margin-bottom: 14px;
}
.form-group label {
  display: block;
  font-size: 13px;
  margin-bottom: 8px;
  color: #4b5563;
}
.remember-forgot {
  display: none;
}
.role-hint {
  margin: 2px 0 14px;
  color: #6b7280;
  font-size: 12px;
  text-align: left;
}
.login-btn {
  width: 100%;
  padding: 14px;
}
.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
@media (max-width: 768px) {
  .login-card {
    padding: 24px 18px;
  }
}
</style>

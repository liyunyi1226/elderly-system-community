import { createRouter, createWebHistory } from "vue-router";
import LoginView from "../views/LoginView.vue";
import HomeView from "../views/HomeView.vue";
import LegacyView from "../views/LegacyView.vue";

const routes = [
  { path: "/", redirect: "/login" },
  { path: "/login", name: "login", component: LoginView },
  { path: "/home", name: "home", component: HomeView },
  { path: "/legacy/:page", name: "legacy", component: LegacyView, props: true }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to) => {
  if (to.path === "/login") return true;
  const userStr = localStorage.getItem("currentUser");
  if (!userStr) {
    return "/login";
  }
  return true;
});

export default router;

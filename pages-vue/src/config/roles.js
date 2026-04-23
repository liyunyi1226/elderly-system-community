export const rolePermissions = {
  admin: {
    name: "管理员",
    description: "拥有系统全部功能权限",
    permissions: [
      "dashboard",
      "elderly-list",
      "elderly-detail",
      "orders",
      "alerts",
      "visit-plan",
      "devices",
      "emergency-resources",
      "doctors",
      "reports",
      "ai-risk-warning",
      "ai-diagnosis",
      "settings"
    ],
    color: "role-admin"
  },
  doctor: {
    name: "医生",
    description: "派医工单、健康数据查看、处置记录",
    permissions: [
      "dashboard",
      "elderly-list",
      "elderly-detail",
      "orders",
      "alerts",
      "reports",
      "ai-risk-warning",
      "ai-diagnosis"
    ],
    color: "role-doctor"
  },
  nurse: {
    name: "护理员",
    description: "巡访计划、日常关怀、设备查看",
    permissions: [
      "dashboard",
      "elderly-list",
      "elderly-detail",
      "visit-plan",
      "devices",
      "alerts",
      "ai-risk-warning",
      "ai-diagnosis"
    ],
    color: "role-nurse"
  },
  service: {
    name: "客服",
    description: "家属沟通、通知推送",
    permissions: ["dashboard", "elderly-list", "elderly-detail", "alerts", "reports", "ai-risk-warning", "ai-diagnosis"],
    color: "role-service"
  }
};


const { initDatabase, run, all } = require("../config/database");

const TARGET = {
  "健康": "健康良好",
  "良好": "健康良好",
  "一般": "需要关注",
  "较差": "危重状态",
  "健康良好": "健康良好",
  "需要关注": "需要关注",
  "危重状态": "危重状态",
};

async function main() {
  await initDatabase();
  const rows = all("SELECT id, health_status FROM elderly");
  let changed = 0;
  for (const row of rows) {
    const current = row.health_status || "";
    const normalized = TARGET[current] || "需要关注";
    if (normalized !== current) {
      run("UPDATE elderly SET health_status = ?, updated_at = datetime('now', 'localtime') WHERE id = ?", [normalized, row.id]);
      changed += 1;
    }
  }
  const grouped = all("SELECT health_status, COUNT(*) as count FROM elderly GROUP BY health_status");
  console.log(`健康状态归一化完成，更新 ${changed} 条记录`);
  console.log("当前分布:", grouped);
}

main().catch((error) => {
  console.error("归一化失败:", error);
  process.exit(1);
});


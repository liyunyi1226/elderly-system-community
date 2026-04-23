const { initDatabase, all, run } = require("../config/database");

const ELDERLY_NAME_BY_PHONE = {
  "13900000001": "王建国",
  "13900000002": "李秀兰",
  "13900000003": "张志强",
  "13900000004": "赵淑芬",
  "13900000005": "刘福生",
};

const DOCTOR_NAME_BY_PHONE = {
  "13811111111": "张伟明",
  "13811111112": "李芳华",
  "13811111113": "王强军",
  "13811111114": "陈静怡",
  "122222": "周文博",
  "8888": "孙雅琴",
};

function deduplicateElderlyByPhone() {
  const elderly = all("SELECT id, name, phone FROM elderly ORDER BY id ASC");
  const byPhone = new Map();
  for (const row of elderly) {
    if (!row.phone) continue;
    if (!byPhone.has(row.phone)) byPhone.set(row.phone, []);
    byPhone.get(row.phone).push(row);
  }

  let removed = 0;
  for (const [, rows] of byPhone.entries()) {
    if (rows.length <= 1) continue;
    const keepId = rows[0].id;
    const removeRows = rows.slice(1);
    for (const row of removeRows) {
      const removeId = row.id;
      run("UPDATE devices SET elderly_id = ? WHERE elderly_id = ?", [keepId, removeId]);
      run("UPDATE health_data SET elderly_id = ? WHERE elderly_id = ?", [keepId, removeId]);
      run("UPDATE alerts SET elderly_id = ? WHERE elderly_id = ?", [keepId, removeId]);
      run("UPDATE orders SET elderly_id = ? WHERE elderly_id = ?", [keepId, removeId]);
      run("UPDATE visits SET elderly_id = ? WHERE elderly_id = ?", [keepId, removeId]);
      run("UPDATE family_communication SET elderly_id = ? WHERE elderly_id = ?", [keepId, removeId]);
      run("DELETE FROM elderly WHERE id = ?", [removeId]);
      removed += 1;
    }
  }
  return removed;
}

function normalizeElderlyNames() {
  const rows = all("SELECT id, phone, name FROM elderly");
  let updated = 0;
  for (const row of rows) {
    const target = ELDERLY_NAME_BY_PHONE[row.phone];
    if (target && target !== row.name) {
      run("UPDATE elderly SET name = ?, updated_at = datetime('now', 'localtime') WHERE id = ?", [target, row.id]);
      updated += 1;
    }
  }
  return updated;
}

function normalizeDoctorNames() {
  const rows = all("SELECT id, phone, name FROM doctors");
  let updated = 0;
  for (const row of rows) {
    const target = DOCTOR_NAME_BY_PHONE[row.phone];
    if (target && target !== row.name) {
      run("UPDATE doctors SET name = ? WHERE id = ?", [target, row.id]);
      updated += 1;
    }
  }
  return updated;
}

function deduplicateDoctorsByPhone() {
  const doctors = all("SELECT id, phone FROM doctors ORDER BY id ASC");
  const byPhone = new Map();
  for (const row of doctors) {
    if (!row.phone) continue;
    if (!byPhone.has(row.phone)) byPhone.set(row.phone, []);
    byPhone.get(row.phone).push(row);
  }

  let removed = 0;
  for (const [, rows] of byPhone.entries()) {
    if (rows.length <= 1) continue;
    const keepId = rows[0].id;
    const removeRows = rows.slice(1);
    for (const row of removeRows) {
      run("UPDATE orders SET doctor_id = ? WHERE doctor_id = ?", [keepId, row.id]);
      run("DELETE FROM doctors WHERE id = ?", [row.id]);
      removed += 1;
    }
  }
  return removed;
}

function checkDuplicates(table) {
  return all(`SELECT name, COUNT(*) as count FROM ${table} GROUP BY name HAVING COUNT(*) > 1`);
}

async function main() {
  await initDatabase();
  const elderlyRemoved = deduplicateElderlyByPhone();
  const doctorRemoved = deduplicateDoctorsByPhone();
  const elderlyUpdated = normalizeElderlyNames();
  const doctorUpdated = normalizeDoctorNames();
  const elderlyDup = checkDuplicates("elderly");
  const doctorDup = checkDuplicates("doctors");

  console.log(`老人去重完成，删除重复记录 ${elderlyRemoved} 条`);
  console.log(`医生去重完成，删除重复记录 ${doctorRemoved} 条`);
  console.log(`老人姓名更新 ${elderlyUpdated} 条，医生姓名更新 ${doctorUpdated} 条`);
  console.log("老人重名检查:", elderlyDup);
  console.log("医生重名检查:", doctorDup);
}

main().catch((error) => {
  console.error("姓名归一化失败:", error);
  process.exit(1);
});


const { initDatabase, all, run } = require('../config/database');

async function main() {
    await initDatabase();

    const badUrgency = all(
        "SELECT id FROM orders WHERE urgency NOT IN ('紧急','一般','常规') OR urgency IS NULL OR urgency = ''"
    );
    for (const row of badUrgency) {
        run("UPDATE orders SET urgency = '一般' WHERE id = ?", [row.id]);
    }

    const badStatus = all(
        "SELECT id FROM orders WHERE status NOT IN ('待接单','已接单','已到达','已完成') OR status IS NULL OR status = ''"
    );
    for (const row of badStatus) {
        run("UPDATE orders SET status = '待接单' WHERE id = ?", [row.id]);
    }

    console.log(`fixed urgency=${badUrgency.length}, status=${badStatus.length}`);
}

main().catch((err) => {
    console.error(err);
    process.exit(1);
});

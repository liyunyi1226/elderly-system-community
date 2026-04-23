const initSqlJs = require('sql.js');
const path = require('path');
const fs = require('fs');

const dbPath = path.join(__dirname, '../data/elderly_monitoring.db');
const dataDir = path.dirname(dbPath);

if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
}

let db = null;
let SQL = null;

async function initDatabase() {
    if (db) return db;
    
    SQL = await initSqlJs();
    
    if (fs.existsSync(dbPath)) {
        const buffer = fs.readFileSync(dbPath);
        db = new SQL.Database(buffer);
    } else {
        db = new SQL.Database();
    }
    
    db.run('PRAGMA foreign_keys = ON');
    
    console.log('SQLite数据库连接成功');
    console.log('数据库文件位置:', dbPath);
    
    return db;
}

function saveDatabase() {
    if (db) {
        const data = db.export();
        const buffer = Buffer.from(data);
        fs.writeFileSync(dbPath, buffer);
    }
}

function run(sql, params = []) {
    if (!db) throw new Error('数据库未初始化');
    db.run(sql, params);
    saveDatabase();
    return { changes: db.getRowsModified() };
}

function get(sql, params = []) {
    if (!db) throw new Error('数据库未初始化');
    const stmt = db.prepare(sql);
    stmt.bind(params);
    if (stmt.step()) {
        const row = stmt.getAsObject();
        stmt.free();
        return row;
    }
    stmt.free();
    return undefined;
}

function all(sql, params = []) {
    if (!db) throw new Error('数据库未初始化');
    const stmt = db.prepare(sql);
    stmt.bind(params);
    const results = [];
    while (stmt.step()) {
        results.push(stmt.getAsObject());
    }
    stmt.free();
    return results;
}

function exec(sql) {
    if (!db) throw new Error('数据库未初始化');
    db.run(sql);
    saveDatabase();
}

module.exports = {
    initDatabase,
    saveDatabase,
    run,
    get,
    all,
    exec,
    getDb: () => db
};

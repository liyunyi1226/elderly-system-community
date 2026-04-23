const { initDatabase, run, saveDatabase } = require('../config/database');
const bcrypt = require('bcryptjs');

async function initialize() {
    try {
        await initDatabase();
        
        console.log('正在初始化数据库...');
        
        run(`
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                real_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'nurse',
                phone TEXT,
                email TEXT,
                status INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        `);
        
        run(`
            CREATE TABLE IF NOT EXISTS elderly (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                gender TEXT NOT NULL,
                birth_date DATE,
                id_card TEXT,
                phone TEXT,
                address TEXT,
                emergency_contact TEXT,
                emergency_phone TEXT,
                health_status TEXT DEFAULT '良好',
                risk_level TEXT DEFAULT '低风险',
                chronic_diseases TEXT,
                allergies TEXT,
                medications TEXT,
                device_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        `);
        
        run(`
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                gender TEXT,
                phone TEXT,
                specialization TEXT,
                hospital TEXT,
                status TEXT DEFAULT '离线',
                current_location TEXT,
                rating REAL DEFAULT 5.00,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        `);
        
        run(`
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL UNIQUE,
                elderly_id INTEGER,
                device_type TEXT DEFAULT '手表',
                status TEXT DEFAULT '离线',
                battery_level INTEGER DEFAULT 100,
                last_online_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (elderly_id) REFERENCES elderly(id)
            )
        `);
        
        run(`
            CREATE TABLE IF NOT EXISTS health_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                elderly_id INTEGER NOT NULL,
                heart_rate INTEGER,
                blood_pressure_high INTEGER,
                blood_pressure_low INTEGER,
                blood_oxygen REAL,
                temperature REAL,
                steps INTEGER DEFAULT 0,
                sleep_hours REAL,
                recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (elderly_id) REFERENCES elderly(id)
            )
        `);
        
        run(`
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                elderly_id INTEGER NOT NULL,
                alert_type TEXT NOT NULL,
                alert_level INTEGER DEFAULT 1,
                title TEXT NOT NULL,
                content TEXT,
                location TEXT,
                status TEXT DEFAULT '待处理',
                handler_id INTEGER,
                handle_time DATETIME,
                handle_result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (elderly_id) REFERENCES elderly(id),
                FOREIGN KEY (handler_id) REFERENCES users(id)
            )
        `);
        
        run(`
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_no TEXT NOT NULL UNIQUE,
                elderly_id INTEGER NOT NULL,
                alert_id INTEGER,
                doctor_id INTEGER,
                urgency TEXT DEFAULT '一般',
                description TEXT,
                status TEXT DEFAULT '待接单',
                accept_time DATETIME,
                arrive_time DATETIME,
                complete_time DATETIME,
                result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (elderly_id) REFERENCES elderly(id),
                FOREIGN KEY (alert_id) REFERENCES alerts(id),
                FOREIGN KEY (doctor_id) REFERENCES doctors(id)
            )
        `);
        
        run(`
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                elderly_id INTEGER NOT NULL,
                nurse_id INTEGER NOT NULL,
                plan_date DATE NOT NULL,
                plan_time TIME,
                status TEXT DEFAULT '待执行',
                visit_content TEXT,
                health_check TEXT,
                medication_check TEXT,
                needs_feedback TEXT,
                next_visit_date DATE,
                actual_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (elderly_id) REFERENCES elderly(id),
                FOREIGN KEY (nurse_id) REFERENCES users(id)
            )
        `);
        
        run(`
            CREATE TABLE IF NOT EXISTS family_communication (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                elderly_id INTEGER NOT NULL,
                contact_name TEXT,
                contact_phone TEXT,
                contact_relation TEXT,
                communication_type TEXT DEFAULT '电话',
                content TEXT,
                result TEXT,
                next_follow_up DATE,
                operator_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (elderly_id) REFERENCES elderly(id),
                FOREIGN KEY (operator_id) REFERENCES users(id)
            )
        `);
        
        const hashedPassword = bcrypt.hashSync('123456', 10);
        
        run(`INSERT OR IGNORE INTO users (username, password, real_name, role, phone, email) VALUES (?, ?, ?, ?, ?, ?)`, 
            ['admin_system', hashedPassword, '系统管理员', 'admin', '13800000001', 'admin@example.com']);
        run(`INSERT OR IGNORE INTO users (username, password, real_name, role, phone, email) VALUES (?, ?, ?, ?, ?, ?)`, 
            ['nurse_lihushi', hashedPassword, '李护士', 'nurse', '13800000003', 'li@example.com']);
        run(`INSERT OR IGNORE INTO users (username, password, real_name, role, phone, email) VALUES (?, ?, ?, ?, ?, ?)`, 
            ['service_wangkefu', hashedPassword, '王客服', 'service', '13800000004', 'wang@example.com']);
        run(`INSERT OR IGNORE INTO users (username, password, real_name, role, phone, email) VALUES (?, ?, ?, ?, ?, ?)`, 
            ['doctor_zhangweiming', hashedPassword, '张伟明', 'doctor', '13800000002', 'zhang@example.com']);
        run(`INSERT OR IGNORE INTO users (username, password, real_name, role, phone, email) VALUES (?, ?, ?, ?, ?, ?)`, 
            ['doctor_lifanghua', hashedPassword, '李芳华', 'doctor', '13800000005', 'lifanghua@example.com']);
        run(`INSERT OR IGNORE INTO users (username, password, real_name, role, phone, email) VALUES (?, ?, ?, ?, ?, ?)`, 
            ['doctor_wangqiangjun', hashedPassword, '王强军', 'doctor', '13800000006', 'wangqiangjun@example.com']);
        run(`INSERT OR IGNORE INTO users (username, password, real_name, role, phone, email) VALUES (?, ?, ?, ?, ?, ?)`, 
            ['doctor_chenjingyi', hashedPassword, '陈静怡', 'doctor', '13800000007', 'chenjingyi@example.com']);
        run(`INSERT OR IGNORE INTO users (username, password, real_name, role, phone, email) VALUES (?, ?, ?, ?, ?, ?)`, 
            ['doctor_zhouwenbo', hashedPassword, '周文博', 'doctor', '13800000008', 'zhouwenbo@example.com']);
        run(`INSERT OR IGNORE INTO users (username, password, real_name, role, phone, email) VALUES (?, ?, ?, ?, ?, ?)`, 
            ['doctor_sunyaqin', hashedPassword, '孙雅琴', 'doctor', '13800000009', 'sunyaqin@example.com']);
        
        run(`INSERT OR IGNORE INTO elderly (name, gender, birth_date, phone, address, emergency_contact, emergency_phone, health_status, risk_level, chronic_diseases, device_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`, 
            ['王建国', '男', '1945-03-15', '13900000001', '幸福社区A栋1单元101', '王小明', '13900000011', '一般', '中风险', '高血压、糖尿病', 'DEV001']);
        run(`INSERT OR IGNORE INTO elderly (name, gender, birth_date, phone, address, emergency_contact, emergency_phone, health_status, risk_level, chronic_diseases, device_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`, 
            ['李秀兰', '女', '1948-07-22', '13900000002', '幸福社区B栋2单元302', '李小红', '13900000012', '良好', '低风险', '无', 'DEV002']);
        run(`INSERT OR IGNORE INTO elderly (name, gender, birth_date, phone, address, emergency_contact, emergency_phone, health_status, risk_level, chronic_diseases, device_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`, 
            ['张志强', '男', '1942-11-08', '13900000003', '幸福社区C栋3单元501', '张小刚', '13900000013', '较差', '高风险', '心脏病、高血压', 'DEV003']);
        run(`INSERT OR IGNORE INTO elderly (name, gender, birth_date, phone, address, emergency_contact, emergency_phone, health_status, risk_level, chronic_diseases, device_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`, 
            ['赵淑芬', '女', '1950-05-30', '13900000004', '幸福社区A栋2单元201', '赵小芳', '13900000014', '健康', '低风险', '无', 'DEV004']);
        run(`INSERT OR IGNORE INTO elderly (name, gender, birth_date, phone, address, emergency_contact, emergency_phone, health_status, risk_level, chronic_diseases, device_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`, 
            ['刘福生', '男', '1946-09-12', '13900000005', '幸福社区B栋1单元402', '刘小华', '13900000015', '一般', '中风险', '关节炎', 'DEV005']);
        
        run(`INSERT OR IGNORE INTO doctors (name, gender, phone, specialization, hospital, status, rating) VALUES (?, ?, ?, ?, ?, ?, ?)`, 
            ['张伟明', '男', '13811111111', '内科', '社区医院', '在线', 4.8]);
        run(`INSERT OR IGNORE INTO doctors (name, gender, phone, specialization, hospital, status, rating) VALUES (?, ?, ?, ?, ?, ?, ?)`, 
            ['李芳华', '女', '13811111112', '心血管科', '社区医院', '在线', 4.9]);
        run(`INSERT OR IGNORE INTO doctors (name, gender, phone, specialization, hospital, status, rating) VALUES (?, ?, ?, ?, ?, ?, ?)`, 
            ['王强军', '男', '13811111113', '急诊科', '社区医院', '忙碌', 4.7]);
        run(`INSERT OR IGNORE INTO doctors (name, gender, phone, specialization, hospital, status, rating) VALUES (?, ?, ?, ?, ?, ?, ?)`, 
            ['陈静怡', '女', '13811111114', '老年科', '社区医院', '离线', 4.6]);
        
        run(`INSERT OR IGNORE INTO devices (device_id, elderly_id, device_type, status, battery_level, last_online_at) VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))`, 
            ['DEV001', 1, '手表', '在线', 85]);
        run(`INSERT OR IGNORE INTO devices (device_id, elderly_id, device_type, status, battery_level, last_online_at) VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))`, 
            ['DEV002', 2, '手表', '在线', 92]);
        run(`INSERT OR IGNORE INTO devices (device_id, elderly_id, device_type, status, battery_level, last_online_at) VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))`, 
            ['DEV003', 3, '手表', '在线', 78]);
        run(`INSERT OR IGNORE INTO devices (device_id, elderly_id, device_type, status, battery_level, last_online_at) VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))`, 
            ['DEV004', 4, '手表', '离线', 15]);
        run(`INSERT OR IGNORE INTO devices (device_id, elderly_id, device_type, status, battery_level, last_online_at) VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))`, 
            ['DEV005', 5, '手表', '在线', 67]);
        
        run(`INSERT OR IGNORE INTO alerts (elderly_id, alert_type, alert_level, title, content, location, status) VALUES (?, ?, ?, ?, ?, ?, ?)`, 
            [3, '紧急', 1, '张志强心率异常', '心率高达120次/分钟，请立即处理', '幸福社区C栋3单元501', '待处理']);
        run(`INSERT OR IGNORE INTO alerts (elderly_id, alert_type, alert_level, title, content, location, status) VALUES (?, ?, ?, ?, ?, ?, ?)`, 
            [1, '警告', 2, '王建国血压偏高', '血压158/95 mmHg，建议关注', '幸福社区A栋1单元101', '待处理']);
        run(`INSERT OR IGNORE INTO alerts (elderly_id, alert_type, alert_level, title, content, location, status) VALUES (?, ?, ?, ?, ?, ?, ?)`, 
            [2, '提醒', 3, '李秀兰服药提醒', '下午3点需服用降压药', '幸福社区B栋2单元302', '已处理']);
        
        saveDatabase();
        
        console.log('数据库初始化完成！');
        console.log('');
        console.log('默认用户账号（密码都是 123456）:');
        console.log('  管理员: admin_system');
        console.log('  医生: doctor_zhangweiming, doctor_lifanghua, doctor_wangqiangjun, doctor_chenjingyi, doctor_zhouwenbo, doctor_sunyaqin');
        console.log('  护理员: nurse_lihushi');
        console.log('  客服: service_wangkefu');
        console.log('');
        
    } catch (error) {
        console.error('数据库初始化失败:', error);
        process.exit(1);
    }
}

initialize();

require('dotenv').config();
const express = require('express');
const session = require('express-session');
const cors = require('cors');
const bodyParser = require('body-parser');

const { initDatabase } = require('./config/database');

const authRoutes = require('./routes/auth');
const elderlyRoutes = require('./routes/elderly');
const alertRoutes = require('./routes/alerts');
const orderRoutes = require('./routes/orders');
const deviceRoutes = require('./routes/devices');
const doctorRoutes = require('./routes/doctors');
const visitRoutes = require('./routes/visits');
const dashboardRoutes = require('./routes/dashboard');
const settingsRoutes = require('./routes/settings');
const adminPagesRoutes = require('./routes/admin-pages');

const app = express();

app.use(cors({
    origin: true,
    credentials: true
}));

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

app.use(session({
    secret: process.env.SESSION_SECRET || 'elderly_monitoring_secret',
    resave: false,
    saveUninitialized: false,
    cookie: {
        secure: false,
        maxAge: 24 * 60 * 60 * 1000
    }
}));

// 后端服务仅保留 API 与 admin-pages 管理界面，不再关联旧前端静态页面

app.use('/api/auth', authRoutes);
app.use('/api/elderly', elderlyRoutes);
app.use('/api/alerts', alertRoutes);
app.use('/api/orders', orderRoutes);
app.use('/api/devices', deviceRoutes);
app.use('/api/doctors', doctorRoutes);
app.use('/api/visits', visitRoutes);
app.use('/api/dashboard', dashboardRoutes);
app.use('/api/settings', settingsRoutes);
app.use('/admin-pages', adminPagesRoutes);

app.get('/', (req, res) => {
    return res.redirect('/admin-pages');
});

app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({
        success: false,
        message: '服务器内部错误',
        error: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
});

const PORT = process.env.PORT || 3000;

async function startServer() {
    try {
        await initDatabase();
        
        app.listen(PORT, () => {
            console.log(`=================================`);
            console.log(`老年人监护系统后端服务已启动`);
            console.log(`端口: ${PORT}`);
            console.log(`访问地址: http://localhost:${PORT}`);
            console.log(`=================================`);
        });
    } catch (error) {
        console.error('服务器启动失败:', error);
        process.exit(1);
    }
}

startServer();

module.exports = app;

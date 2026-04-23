const express = require('express');
const router = express.Router();
const { get, all } = require('../config/database');
const { requireAuth } = require('../middleware/auth');

router.get('/overview', requireAuth, (req, res) => {
    try {
        const elderlyCount = get('SELECT COUNT(*) as count FROM elderly');
        const alertCount = get('SELECT COUNT(*) as count FROM alerts WHERE status = "待处理"');
        const orderCount = get('SELECT COUNT(*) as count FROM orders WHERE status IN ("待接单", "已接单", "出发中", "已到达", "处置中")');
        const doctorOnline = get('SELECT COUNT(*) as count FROM doctors WHERE status = "在线"');

        const alertsByLevel = all(`
            SELECT alert_type, COUNT(*) as count 
            FROM alerts 
            WHERE date(created_at) = date('now', 'localtime')
            GROUP BY alert_type
        `);

        const recentAlerts = all(`
            SELECT a.*, e.name as elderly_name 
            FROM alerts a
            LEFT JOIN elderly e ON a.elderly_id = e.id
            WHERE a.status = '待处理'
            ORDER BY a.created_at DESC 
            LIMIT 5
        `);

        const pendingOrders = all(`
            SELECT o.*, e.name as elderly_name, e.address
            FROM orders o
            LEFT JOIN elderly e ON o.elderly_id = e.id
            WHERE o.status IN ('待接单', '已接单')
            ORDER BY o.created_at DESC 
            LIMIT 5
        `);

        const deviceStats = get(`
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = '在线' THEN 1 ELSE 0 END) as online,
                SUM(CASE WHEN battery_level < 20 THEN 1 ELSE 0 END) as low_battery
            FROM devices
        `);

        res.json({
            success: true,
            data: {
                elderlyCount: elderlyCount.count,
                alertCount: alertCount.count,
                orderCount: orderCount.count,
                doctorOnline: doctorOnline.count,
                alertsByLevel,
                recentAlerts,
                pendingOrders,
                deviceStats
            }
        });

    } catch (error) {
        console.error('获取控制台概览错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.get('/trend', requireAuth, (req, res) => {
    try {
        const { days = 7 } = req.query;

        const orderTrend = all(`
            SELECT date(created_at) as date, COUNT(*) as count
            FROM orders
            WHERE created_at >= date('now', '-' || ? || ' days', 'localtime')
            GROUP BY date(created_at)
            ORDER BY date
        `, [days]);

        const alertTrend = all(`
            SELECT date(created_at) as date, COUNT(*) as count
            FROM alerts
            WHERE created_at >= date('now', '-' || ? || ' days', 'localtime')
            GROUP BY date(created_at)
            ORDER BY date
        `, [days]);

        res.json({
            success: true,
            data: {
                orderTrend,
                alertTrend
            }
        });

    } catch (error) {
        console.error('获取趋势数据错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

module.exports = router;

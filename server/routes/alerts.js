const express = require('express');
const router = express.Router();
const { get, all, run } = require('../config/database');
const { requireAuth } = require('../middleware/auth');

router.get('/list', requireAuth, (req, res) => {
    try {
        const { page = 1, pageSize = 10, status, alertType } = req.query;
        const offset = (page - 1) * pageSize;

        let sql = `
            SELECT a.*, e.name as elderly_name, e.address, e.phone as elderly_phone
            FROM alerts a
            LEFT JOIN elderly e ON a.elderly_id = e.id
            WHERE 1=1
        `;
        const params = [];

        if (status) {
            sql += ' AND a.status = ?';
            params.push(status);
        }

        if (alertType) {
            sql += ' AND a.alert_type = ?';
            params.push(alertType);
        }

        const countSql = sql.replace('SELECT a.*', 'SELECT COUNT(*) as total');
        const countResult = get(countSql, params);
        const total = countResult.total;

        sql += ' ORDER BY a.created_at DESC LIMIT ? OFFSET ?';
        params.push(parseInt(pageSize), parseInt(offset));

        const alerts = all(sql, params);

        res.json({
            success: true,
            data: {
                list: alerts,
                total,
                page: parseInt(page),
                pageSize: parseInt(pageSize)
            }
        });

    } catch (error) {
        console.error('获取警报列表错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.get('/statistics', requireAuth, (req, res) => {
    try {
        const statusCount = all(`
            SELECT status, COUNT(*) as count 
            FROM alerts 
            GROUP BY status
        `);

        const typeCount = all(`
            SELECT alert_type, COUNT(*) as count 
            FROM alerts 
            WHERE date(created_at) = date('now', 'localtime')
            GROUP BY alert_type
        `);

        const avgResponseTime = get(`
            SELECT AVG((julianday(handle_time) - julianday(created_at)) * 24 * 60) as avg_time
            FROM alerts 
            WHERE handle_time IS NOT NULL
        `);

        res.json({
            success: true,
            data: {
                statusCount,
                typeCount,
                avgResponseTime: avgResponseTime.avg_time || 0
            }
        });

    } catch (error) {
        console.error('获取警报统计错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.post('/create', requireAuth, (req, res) => {
    try {
        const alertData = req.body;

        const result = run(
            `INSERT INTO alerts (elderly_id, alert_type, alert_level, title, content, location)
             VALUES (?, ?, ?, ?, ?, ?)`,
            [
                alertData.elderly_id,
                alertData.alert_type,
                alertData.alert_level || 1,
                alertData.title,
                alertData.content,
                alertData.location
            ]
        );

        res.json({
            success: true,
            message: '警报创建成功',
            data: { id: result.lastInsertRowid }
        });

    } catch (error) {
        console.error('创建警报错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.put('/:id/handle', requireAuth, (req, res) => {
    try {
        const { id } = req.params;
        const { handle_result } = req.body;
        const handler_id = req.session.user.id;

        run(
            `UPDATE alerts SET status = '已处理', handler_id = ?, handle_time = datetime('now', 'localtime'), handle_result = ? WHERE id = ?`,
            [handler_id, handle_result, id]
        );

        res.json({
            success: true,
            message: '处理成功'
        });

    } catch (error) {
        console.error('处理警报错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

module.exports = router;

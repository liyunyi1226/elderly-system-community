const express = require('express');
const router = express.Router();
const { get, all, run } = require('../config/database');
const { requireAuth, requireRole } = require('../middleware/auth');

router.get('/list', requireAuth, (req, res) => {
    try {
        const { page = 1, pageSize = 10, status, date } = req.query;
        const offset = (page - 1) * pageSize;

        let sql = `
            SELECT v.*, e.name as elderly_name, e.address, e.phone as elderly_phone,
                   u.real_name as nurse_name
            FROM visits v
            LEFT JOIN elderly e ON v.elderly_id = e.id
            LEFT JOIN users u ON v.nurse_id = u.id
            WHERE 1=1
        `;
        const params = [];

        if (status) {
            sql += ' AND v.status = ?';
            params.push(status);
        }

        if (date) {
            sql += ' AND v.plan_date = ?';
            params.push(date);
        }

        const countSql = sql.replace('SELECT v.*', 'SELECT COUNT(*) as total');
        const countResult = get(countSql, params);
        const total = countResult.total;

        sql += ' ORDER BY v.plan_date ASC, v.plan_time ASC LIMIT ? OFFSET ?';
        params.push(parseInt(pageSize), parseInt(offset));

        const visits = all(sql, params);

        res.json({
            success: true,
            data: {
                list: visits,
                total,
                page: parseInt(page),
                pageSize: parseInt(pageSize)
            }
        });

    } catch (error) {
        console.error('获取巡访列表错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.post('/create', requireAuth, requireRole('admin', 'nurse'), (req, res) => {
    try {
        const visitData = req.body;

        const result = run(
            `INSERT INTO visits (elderly_id, nurse_id, plan_date, plan_time, visit_content)
             VALUES (?, ?, ?, ?, ?)`,
            [
                visitData.elderly_id,
                visitData.nurse_id || req.session.user.id,
                visitData.plan_date,
                visitData.plan_time,
                visitData.visit_content
            ]
        );

        res.json({
            success: true,
            message: '巡访计划创建成功',
            data: { id: result.lastInsertRowid }
        });

    } catch (error) {
        console.error('创建巡访计划错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.put('/:id/complete', requireAuth, requireRole('admin', 'nurse'), (req, res) => {
    try {
        const { id } = req.params;
        const { health_check, medication_check, needs_feedback, next_visit_date } = req.body;

        run(
            `UPDATE visits SET 
                status = '已完成', 
                actual_time = datetime('now', 'localtime'),
                health_check = ?,
                medication_check = ?,
                needs_feedback = ?,
                next_visit_date = ?
             WHERE id = ?`,
            [health_check, medication_check, needs_feedback, next_visit_date, id]
        );

        res.json({
            success: true,
            message: '巡访完成'
        });

    } catch (error) {
        console.error('完成巡访错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

module.exports = router;

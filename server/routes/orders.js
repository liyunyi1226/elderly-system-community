const express = require('express');
const router = express.Router();
const { get, all, run } = require('../config/database');
const { requireAuth, requireRole } = require('../middleware/auth');

const ALLOWED_URGENCY = new Set(['紧急', '一般', '常规']);
const ALLOWED_STATUS = new Set(['待接单', '已接单', '出发中', '已到达', '处置中', '已完成']);

function resolveDoctorIdForUser(user) {
    if (!user) return null;
    const byUserId = get('SELECT id FROM doctors WHERE user_id = ? ORDER BY id DESC LIMIT 1', [user.id]);
    if (byUserId?.id) return byUserId.id;
    const byName = get('SELECT id FROM doctors WHERE name = ? ORDER BY id DESC LIMIT 1', [user.realName || '']);
    if (byName?.id) return byName.id;
    return null;
}

router.get('/list', requireAuth, (req, res) => {
    try {
        const { page = 1, pageSize = 10, status } = req.query;
        const offset = (page - 1) * pageSize;

        let sql = `
            SELECT o.*, e.name as elderly_name, e.address, e.phone as elderly_phone,
                   d.name as doctor_name, d.phone as doctor_phone
            FROM orders o
            LEFT JOIN elderly e ON o.elderly_id = e.id
            LEFT JOIN doctors d ON o.doctor_id = d.id
            WHERE 1=1
        `;
        const params = [];

        if (status) {
            sql += ' AND o.status = ?';
            params.push(status);
        }
        if (req.session.user.role === 'doctor') {
            const doctorId = resolveDoctorIdForUser(req.session.user);
            if (!doctorId) {
                return res.json({
                    success: true,
                    data: { list: [], total: 0, page: parseInt(page), pageSize: parseInt(pageSize) }
                });
            }
            sql += ' AND o.doctor_id = ?';
            params.push(doctorId);
        }

        const countSql = sql.replace('SELECT o.*', 'SELECT COUNT(*) as total');
        const countResult = get(countSql, params);
        const total = countResult.total;

        sql += ' ORDER BY o.created_at DESC LIMIT ? OFFSET ?';
        params.push(parseInt(pageSize), parseInt(offset));

        const orders = all(sql, params);

        res.json({
            success: true,
            data: {
                list: orders,
                total,
                page: parseInt(page),
                pageSize: parseInt(pageSize)
            }
        });

    } catch (error) {
        console.error('获取工单列表错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.post('/create', requireAuth, (req, res) => {
    try {
        if (!['admin', 'service'].includes(req.session.user.role)) {
            return res.status(403).json({
                success: false,
                message: '当前账号无派医权限'
            });
        }
        const orderData = req.body;
        console.log('收到创建工单请求:', orderData);
        
        const orderNo = 'ORD' + Date.now();

        run(
            `INSERT INTO orders (order_no, elderly_id, alert_id, doctor_id, urgency, description)
             VALUES (?, ?, ?, ?, ?, ?)`,
            [
                orderNo,
                orderData.elderly_id,
                orderData.alert_id || null,
                orderData.doctor_id,
                ALLOWED_URGENCY.has(orderData.urgency) ? orderData.urgency : '一般',
                orderData.description
            ]
        );

        const inserted = get('SELECT id FROM orders WHERE order_no = ?', [orderNo]);
        console.log('工单创建成功:', { id: inserted?.id, order_no: orderNo });

        res.json({
            success: true,
            message: '工单创建成功',
            data: { id: inserted?.id, order_no: orderNo }
        });

    } catch (error) {
        console.error('创建工单错误:', error);
        console.error('错误堆栈:', error.stack);
        res.status(500).json({
            success: false,
            message: '服务器错误: ' + error.message
        });
    }
});

router.put('/:id/status', requireAuth, (req, res) => {
    try {
        const { id } = req.params;
        const { status } = req.body;
        const current = get('SELECT * FROM orders WHERE id = ?', [id]);
        if (!current) {
            return res.status(404).json({ success: false, message: '工单不存在' });
        }
        if (req.session.user.role === 'doctor') {
            const doctorId = resolveDoctorIdForUser(req.session.user);
            if (!doctorId || Number(current.doctor_id) !== Number(doctorId)) {
                return res.status(403).json({ success: false, message: '仅可操作本人负责工单' });
            }
            if (!['已接单', '出发中', '已到达', '处置中', '已完成'].includes(status)) {
                return res.status(403).json({ success: false, message: '当前账号无此状态操作权限' });
            }
        } else if (!['admin', 'service'].includes(req.session.user.role)) {
            return res.status(403).json({ success: false, message: '当前账号无工单操作权限' });
        }
        if (!ALLOWED_STATUS.has(status)) {
            return res.status(400).json({
                success: false,
                message: '无效的工单状态'
            });
        }

        let sql = 'UPDATE orders SET status = ?';
        const params = [status];

        if (status === '已接单') {
            sql += ", accept_time = datetime('now', 'localtime')";
        } else if (status === '已到达') {
            sql += ", arrive_time = datetime('now', 'localtime')";
        } else if (status === '已完成') {
            sql += ", complete_time = datetime('now', 'localtime')";
        }

        sql += ' WHERE id = ?';
        params.push(id);

        run(sql, params);
        if (status === '已完成') {
            const order = get('SELECT doctor_id FROM orders WHERE id = ?', [id]);
            if (order?.doctor_id) {
                run("UPDATE doctors SET status = '在线' WHERE id = ?", [order.doctor_id]);
            }
        }

        res.json({
            success: true,
            message: '状态更新成功'
        });

    } catch (error) {
        console.error('更新工单状态错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.put('/:id/complete', requireAuth, (req, res) => {
    try {
        const { id } = req.params;
        const { result } = req.body;
        const current = get('SELECT * FROM orders WHERE id = ?', [id]);
        if (!current) {
            return res.status(404).json({ success: false, message: '工单不存在' });
        }
        if (req.session.user.role === 'doctor') {
            const doctorId = resolveDoctorIdForUser(req.session.user);
            if (!doctorId || Number(current.doctor_id) !== Number(doctorId)) {
                return res.status(403).json({ success: false, message: '仅可完成本人负责工单' });
            }
        } else if (!['admin', 'service'].includes(req.session.user.role)) {
            return res.status(403).json({ success: false, message: '当前账号无工单完成权限' });
        }

        run(
            `UPDATE orders SET status = '已完成', complete_time = datetime('now', 'localtime'), result = ? WHERE id = ?`,
            [result, id]
        );
        const order = get('SELECT doctor_id FROM orders WHERE id = ?', [id]);
        if (order?.doctor_id) {
            run("UPDATE doctors SET status = '在线' WHERE id = ?", [order.doctor_id]);
        }

        res.json({
            success: true,
            message: '工单完成'
        });

    } catch (error) {
        console.error('完成工单错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

module.exports = router;

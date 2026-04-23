const express = require('express');
const router = express.Router();
const { get, all, run } = require('../config/database');
const { requireAuth, requireRole } = require('../middleware/auth');

router.get('/list', requireAuth, (req, res) => {
    try {
        const { page = 1, pageSize = 10, keyword, status, riskLevel } = req.query;
        const offset = (page - 1) * pageSize;

        let sql = 'SELECT * FROM elderly WHERE 1=1';
        const params = [];

        if (keyword) {
            sql += ' AND (name LIKE ? OR phone LIKE ? OR address LIKE ?)';
            params.push(`%${keyword}%`, `%${keyword}%`, `%${keyword}%`);
        }

        if (status) {
            // 处理状态映射
            const statusMap = {
                '健康良好': ['良好', '健康', '健康良好'],
                '需要关注': ['一般', '需要关注'],
                '危重状态': ['较差', '危重状态']
            };
            
            const statusValues = statusMap[status] || [status];
            sql += ' AND health_status IN (' + statusValues.map(() => '?').join(', ') + ')';
            params.push(...statusValues);
        }

        if (riskLevel) {
            sql += ' AND risk_level = ?';
            params.push(riskLevel);
        }

        const countSql = sql.replace('SELECT *', 'SELECT COUNT(*) as total');
        const countResult = get(countSql, params);
        const total = countResult.total;

        sql += ' ORDER BY created_at DESC LIMIT ? OFFSET ?';
        params.push(parseInt(pageSize), parseInt(offset));

        const elderly = all(sql, params);

        res.json({
            success: true,
            data: {
                list: elderly,
                total,
                page: parseInt(page),
                pageSize: parseInt(pageSize)
            }
        });

    } catch (error) {
        console.error('获取老年人列表错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.get('/:id', requireAuth, (req, res) => {
    try {
        const { id } = req.params;

        const elderly = get('SELECT * FROM elderly WHERE id = ?', [id]);

        if (!elderly) {
            return res.status(404).json({
                success: false,
                message: '未找到该老人信息'
            });
        }

        const healthData = all(
            'SELECT * FROM health_data WHERE elderly_id = ? ORDER BY recorded_at DESC LIMIT 10',
            [id]
        );

        const devices = all(
            'SELECT * FROM devices WHERE elderly_id = ?',
            [id]
        );

        const communications = all(
            'SELECT * FROM family_communication WHERE elderly_id = ? ORDER BY created_at DESC LIMIT 5',
            [id]
        );

        res.json({
            success: true,
            data: {
                ...elderly,
                healthData,
                devices,
                communications
            }
        });

    } catch (error) {
        console.error('获取老年人详情错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.post('/create', requireAuth, requireRole('admin', 'service'), (req, res) => {
    try {
        const elderlyData = req.body;

        const result = run(
            `INSERT INTO elderly (name, gender, birth_date, phone, address, emergency_contact, emergency_phone, health_status, risk_level, chronic_diseases, allergies, medications, device_id)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
            [
                elderlyData.name,
                elderlyData.gender,
                elderlyData.birth_date,
                elderlyData.phone,
                elderlyData.address,
                elderlyData.emergency_contact,
                elderlyData.emergency_phone,
                elderlyData.health_status || '良好',
                elderlyData.risk_level || '低风险',
                elderlyData.chronic_diseases,
                elderlyData.allergies,
                elderlyData.medications,
                elderlyData.device_id
            ]
        );

        res.json({
            success: true,
            message: '添加成功',
            data: { id: result.lastInsertRowid }
        });

    } catch (error) {
        console.error('添加老年人错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.put('/:id', requireAuth, requireRole('admin', 'service'), (req, res) => {
    try {
        const { id } = req.params;
        const elderlyData = req.body;

        run(
            `UPDATE elderly SET 
                name = ?, gender = ?, birth_date = ?, phone = ?, address = ?,
                emergency_contact = ?, emergency_phone = ?, health_status = ?,
                risk_level = ?, chronic_diseases = ?, allergies = ?, medications = ?
             WHERE id = ?`,
            [
                elderlyData.name,
                elderlyData.gender,
                elderlyData.birth_date,
                elderlyData.phone,
                elderlyData.address,
                elderlyData.emergency_contact,
                elderlyData.emergency_phone,
                elderlyData.health_status,
                elderlyData.risk_level,
                elderlyData.chronic_diseases,
                elderlyData.allergies,
                elderlyData.medications,
                id
            ]
        );

        res.json({
            success: true,
            message: '更新成功'
        });

    } catch (error) {
        console.error('更新老年人信息错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.delete('/:id', requireAuth, requireRole('admin'), (req, res) => {
    try {
        const { id } = req.params;

        run('DELETE FROM elderly WHERE id = ?', [id]);

        res.json({
            success: true,
            message: '删除成功'
        });

    } catch (error) {
        console.error('删除老年人错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.post('/health-data', requireAuth, requireRole('admin', 'doctor', 'nurse'), (req, res) => {
    try {
        const healthData = req.body;

        run(
            `INSERT INTO health_data (elderly_id, heart_rate, blood_pressure_high, blood_pressure_low, blood_oxygen, temperature, steps, sleep_hours)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
            [
                healthData.elderly_id,
                healthData.heart_rate,
                healthData.blood_pressure_high,
                healthData.blood_pressure_low,
                healthData.blood_oxygen,
                healthData.temperature,
                healthData.steps || 0,
                healthData.sleep_hours
            ]
        );

        res.json({
            success: true,
            message: '健康数据记录成功'
        });

    } catch (error) {
        console.error('记录健康数据错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

module.exports = router;

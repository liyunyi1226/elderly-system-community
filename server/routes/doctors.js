const express = require('express');
const router = express.Router();
const { get, all, run } = require('../config/database');
const { requireAuth, requireRole } = require('../middleware/auth');

router.get('/list', requireAuth, (req, res) => {
    try {
        const { status } = req.query;

        // 历史数据可能存在重复医生（同名同电话），列表接口按 name+phone 去重后返回最新一条
        let sql = `
            SELECT d.*
            FROM doctors d
            INNER JOIN (
                SELECT MAX(id) as id
                FROM doctors
                GROUP BY name, phone
            ) latest ON latest.id = d.id
            WHERE 1=1
        `;
        const params = [];

        if (status) {
            sql += ' AND d.status = ?';
            params.push(status);
        }

        sql += ' ORDER BY d.rating DESC';

        const doctors = all(sql, params);

        res.json({
            success: true,
            data: doctors
        });

    } catch (error) {
        console.error('获取医生列表错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.get('/:id', requireAuth, (req, res) => {
    try {
        const { id } = req.params;
        const doctor = get('SELECT * FROM doctors WHERE id = ?', [id]);

        if (!doctor) {
            return res.status(404).json({
                success: false,
                message: '未找到医生信息'
            });
        }

        res.json({
            success: true,
            data: doctor
        });
    } catch (error) {
        console.error('获取医生详情错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.post('/create', requireAuth, requireRole('admin'), (req, res) => {
    try {
        const doctorData = req.body;
        run(
            `INSERT INTO doctors (name, gender, phone, specialization, hospital, status, current_location, rating)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
            [
                doctorData.name,
                doctorData.gender,
                doctorData.phone,
                doctorData.specialization,
                doctorData.hospital,
                doctorData.status || '离线',
                doctorData.current_location || null,
                doctorData.rating || 5
            ]
        );
        const inserted = get(
            `SELECT id FROM doctors
             WHERE name = ? AND phone = ?
             ORDER BY id DESC LIMIT 1`,
            [doctorData.name, doctorData.phone]
        );

        res.json({
            success: true,
            message: '医生创建成功',
            data: { id: inserted?.id }
        });
    } catch (error) {
        console.error('创建医生错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.put('/:id', requireAuth, requireRole('admin'), (req, res) => {
    try {
        const { id } = req.params;
        const doctorData = req.body;

        run(
            `UPDATE doctors SET
                name = ?, gender = ?, phone = ?, specialization = ?,
                hospital = ?, status = ?, current_location = ?, rating = ?
             WHERE id = ?`,
            [
                doctorData.name,
                doctorData.gender,
                doctorData.phone,
                doctorData.specialization,
                doctorData.hospital,
                doctorData.status || '离线',
                doctorData.current_location || null,
                doctorData.rating || 5,
                id
            ]
        );

        res.json({
            success: true,
            message: '医生信息更新成功'
        });
    } catch (error) {
        console.error('更新医生信息错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.put('/:id/status', requireAuth, requireRole('admin', 'doctor'), (req, res) => {
    try {
        const { id } = req.params;
        const { status, current_location } = req.body;

        let sql = 'UPDATE doctors SET status = ?';
        const params = [status];

        if (current_location) {
            sql += ', current_location = ?';
            params.push(current_location);
        }

        sql += ' WHERE id = ?';
        params.push(id);

        run(sql, params);

        res.json({
            success: true,
            message: '医生状态更新成功'
        });

    } catch (error) {
        console.error('更新医生状态错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.delete('/:id', requireAuth, requireRole('admin'), (req, res) => {
    try {
        const { id } = req.params;
        run('DELETE FROM doctors WHERE id = ?', [id]);

        res.json({
            success: true,
            message: '医生删除成功'
        });
    } catch (error) {
        console.error('删除医生错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

module.exports = router;

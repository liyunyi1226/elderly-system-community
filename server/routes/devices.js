const express = require('express');
const router = express.Router();
const { get, all, run } = require('../config/database');
const { requireAuth, requireRole } = require('../middleware/auth');

router.get('/list', requireAuth, (req, res) => {
    try {
        const { status } = req.query;

        let sql = `
            SELECT d.*, e.name as elderly_name, e.address
            FROM devices d
            LEFT JOIN elderly e ON d.elderly_id = e.id
            WHERE 1=1
        `;
        const params = [];

        if (status) {
            sql += ' AND d.status = ?';
            params.push(status);
        }

        sql += ' ORDER BY d.last_online_at DESC';

        const devices = all(sql, params);

        res.json({
            success: true,
            data: devices
        });

    } catch (error) {
        console.error('获取设备列表错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.get('/:id', requireAuth, (req, res) => {
    try {
        const { id } = req.params;
        const device = get(
            `SELECT d.*, e.name as elderly_name, e.address
             FROM devices d
             LEFT JOIN elderly e ON d.elderly_id = e.id
             WHERE d.id = ?`,
            [id]
        );

        if (!device) {
            return res.status(404).json({
                success: false,
                message: '未找到设备信息'
            });
        }

        res.json({
            success: true,
            data: device
        });
    } catch (error) {
        console.error('获取设备详情错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.post('/create', requireAuth, requireRole('admin', 'nurse'), (req, res) => {
    try {
        const deviceData = req.body;
        run(
            `INSERT INTO devices (device_id, elderly_id, device_type, status, battery_level, last_online_at)
             VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))`,
            [
                deviceData.device_id,
                deviceData.elderly_id || null,
                deviceData.device_type || '手表',
                deviceData.status || '离线',
                deviceData.battery_level ?? 100
            ]
        );
        const inserted = get('SELECT id FROM devices WHERE device_id = ?', [deviceData.device_id]);

        res.json({
            success: true,
            message: '设备创建成功',
            data: { id: inserted?.id }
        });
    } catch (error) {
        console.error('创建设备错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.put('/:id', requireAuth, requireRole('admin', 'nurse'), (req, res) => {
    try {
        const { id } = req.params;
        const deviceData = req.body;

        run(
            `UPDATE devices SET
                device_id = ?, elderly_id = ?, device_type = ?,
                status = ?, battery_level = ?, last_online_at = datetime('now', 'localtime')
             WHERE id = ?`,
            [
                deviceData.device_id,
                deviceData.elderly_id || null,
                deviceData.device_type || '手表',
                deviceData.status || '离线',
                deviceData.battery_level ?? 100,
                id
            ]
        );

        res.json({
            success: true,
            message: '设备信息更新成功'
        });
    } catch (error) {
        console.error('更新设备错误:', error);
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
            FROM devices 
            GROUP BY status
        `);

        const lowBattery = get(`
            SELECT COUNT(*) as count 
            FROM devices 
            WHERE battery_level < 20
        `);

        const offlineDevices = get(`
            SELECT COUNT(*) as count 
            FROM devices 
            WHERE status = '离线' OR last_online_at < datetime('now', '-1 hour', 'localtime')
        `);

        res.json({
            success: true,
            data: {
                statusCount,
                lowBatteryCount: lowBattery.count,
                offlineCount: offlineDevices.count
            }
        });

    } catch (error) {
        console.error('获取设备统计错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.put('/:id/status', requireAuth, requireRole('admin', 'nurse'), (req, res) => {
    try {
        const { id } = req.params;
        const { status, battery_level } = req.body;

        let sql = "UPDATE devices SET last_online_at = datetime('now', 'localtime')";
        const params = [];

        if (status) {
            sql += ', status = ?';
            params.push(status);
        }

        if (battery_level !== undefined) {
            sql += ', battery_level = ?';
            params.push(battery_level);
        }

        sql += ' WHERE id = ?';
        params.push(id);

        run(sql, params);

        res.json({
            success: true,
            message: '设备状态更新成功'
        });

    } catch (error) {
        console.error('更新设备状态错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.delete('/:id', requireAuth, requireRole('admin'), (req, res) => {
    try {
        const { id } = req.params;
        run('DELETE FROM devices WHERE id = ?', [id]);

        res.json({
            success: true,
            message: '设备删除成功'
        });
    } catch (error) {
        console.error('删除设备错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

module.exports = router;

const express = require('express');
const router = express.Router();
const { get, run } = require('../config/database');
const { requireAuth, requireRole } = require('../middleware/auth');

function ensureSettingsTable() {
    run(`
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            config_json TEXT NOT NULL,
            updated_by INTEGER,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);
}

function normalizeSettings(input) {
    const defaults = {
        thresholds: { heartRateMin: 60, heartRateMax: 100, bpMin: 90, bpMax: 140, spo2Min: 95, tempMin: 36.0, tempMax: 37.5 },
        notifications: { system: true, sms: true, email: false, app: true, contacts: '13800000001', emailAddress: 'admin@community.com' },
        features: { autoAlert: true, dispatchSuggestion: true, medicationReminder: true, dataSync: true },
        account: { adminName: '管理员', adminAccount: 'admin', adminCommunity: '阳光社区', adminPhone: '010-****1234' }
    };
    const s = input || {};
    return {
        thresholds: { ...defaults.thresholds, ...(s.thresholds || {}) },
        notifications: { ...defaults.notifications, ...(s.notifications || {}) },
        features: { ...defaults.features, ...(s.features || {}) },
        account: { ...defaults.account, ...(s.account || {}) }
    };
}

function validateSettings(settings) {
    const t = settings.thresholds || {};
    if (Number(t.heartRateMin) < 30 || Number(t.heartRateMax) > 220 || Number(t.heartRateMin) >= Number(t.heartRateMax)) {
        return '心率阈值不合法';
    }
    if (Number(t.bpMin) < 60 || Number(t.bpMax) > 240 || Number(t.bpMin) >= Number(t.bpMax)) {
        return '血压阈值不合法';
    }
    if (Number(t.spo2Min) < 70 || Number(t.spo2Min) > 100) {
        return '血氧阈值不合法';
    }
    if (Number(t.tempMin) < 34 || Number(t.tempMax) > 42 || Number(t.tempMin) >= Number(t.tempMax)) {
        return '体温阈值不合法';
    }

    const contacts = String(settings.notifications?.contacts || '').trim();
    if (contacts) {
        const phones = contacts.split(',').map((x) => x.trim()).filter(Boolean);
        const invalid = phones.find((p) => !/^1\d{10}$/.test(p));
        if (invalid) return `紧急通知名单手机号格式错误: ${invalid}`;
    }
    if (settings.notifications?.email) {
        const email = String(settings.notifications?.emailAddress || '').trim();
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            return '邮件通知已开启，但邮箱地址无效';
        }
    }
    return '';
}

router.get('/current', requireAuth, (req, res) => {
    try {
        ensureSettingsTable();
        const row = get('SELECT config_json, updated_at FROM system_settings WHERE id = 1');
        if (!row) {
            return res.json({ success: true, data: { settings: null, updated_at: null } });
        }
        let settings = null;
        try {
            settings = JSON.parse(row.config_json);
        } catch (_) {
            settings = null;
        }
        res.json({ success: true, data: { settings: normalizeSettings(settings), updated_at: row.updated_at } });
    } catch (error) {
        console.error('获取系统设置失败:', error);
        res.status(500).json({ success: false, message: '获取系统设置失败' });
    }
});

router.put('/current', requireAuth, requireRole('admin'), (req, res) => {
    try {
        ensureSettingsTable();
        const settings = normalizeSettings(req.body || {});
        const errorMsg = validateSettings(settings);
        if (errorMsg) {
            return res.status(400).json({ success: false, message: errorMsg });
        }
        run(
            `INSERT INTO system_settings (id, config_json, updated_by, updated_at)
             VALUES (1, ?, ?, datetime('now', 'localtime'))
             ON CONFLICT(id) DO UPDATE SET
               config_json = excluded.config_json,
               updated_by = excluded.updated_by,
               updated_at = datetime('now', 'localtime')`,
            [JSON.stringify(settings), req.session.user.id]
        );
        res.json({ success: true, message: '系统设置已更新', data: { settings } });
    } catch (error) {
        console.error('保存系统设置失败:', error);
        res.status(500).json({ success: false, message: '保存系统设置失败' });
    }
});

module.exports = router;


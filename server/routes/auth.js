const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const { get } = require('../config/database');
const { rolePermissions } = require('../middleware/auth');

router.post('/login', (req, res) => {
    try {
        const { username, password } = req.body;

        if (!username || !password) {
            return res.status(400).json({
                success: false,
                message: '用户名和密码不能为空'
            });
        }

        const user = get('SELECT * FROM users WHERE username = ? AND status = 1', [username]);

        if (!user) {
            return res.status(401).json({
                success: false,
                message: '用户名或密码错误'
            });
        }

        const isMatch = bcrypt.compareSync(password, user.password);
        if (!isMatch) {
            return res.status(401).json({
                success: false,
                message: '用户名或密码错误'
            });
        }

        req.session.user = {
            id: user.id,
            username: user.username,
            realName: user.real_name,
            role: user.role,
            phone: user.phone,
            email: user.email,
            permissions: rolePermissions[user.role] || []
        };

        res.json({
            success: true,
            message: '登录成功',
            data: req.session.user
        });

    } catch (error) {
        console.error('登录错误:', error);
        res.status(500).json({
            success: false,
            message: '服务器错误'
        });
    }
});

router.post('/logout', (req, res) => {
    req.session.destroy((err) => {
        if (err) {
            return res.status(500).json({
                success: false,
                message: '退出失败'
            });
        }
        res.json({
            success: true,
            message: '已退出登录'
        });
    });
});

router.get('/current', (req, res) => {
    if (req.session && req.session.user) {
        res.json({
            success: true,
            data: req.session.user
        });
    } else {
        res.status(401).json({
            success: false,
            message: '未登录'
        });
    }
});

router.get('/permissions', (req, res) => {
    res.json({
        success: true,
        data: rolePermissions
    });
});

module.exports = router;

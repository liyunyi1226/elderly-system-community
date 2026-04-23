function requireAuth(req, res, next) {
    if (req.session && req.session.user) {
        return next();
    }
    return res.status(401).json({
        success: false,
        message: '请先登录'
    });
}

function requireRole(...roles) {
    return (req, res, next) => {
        if (!req.session || !req.session.user) {
            return res.status(401).json({
                success: false,
                message: '请先登录'
            });
        }

        if (!roles.includes(req.session.user.role)) {
            return res.status(403).json({
                success: false,
                message: '权限不足'
            });
        }

        return next();
    };
}

const rolePermissions = {
    admin: ['dashboard', 'elderly', 'elderly-detail', 'orders', 'alerts', 'visits', 'devices', 'emergency', 'monitor', 'doctors', 'reports', 'ai-risk-warning', 'ai-diagnosis', 'settings'],
    doctor: ['dashboard', 'elderly', 'elderly-detail', 'orders', 'alerts', 'monitor', 'reports', 'ai-risk-warning', 'ai-diagnosis'],
    nurse: ['dashboard', 'elderly', 'elderly-detail', 'visits', 'devices', 'alerts', 'ai-risk-warning', 'ai-diagnosis'],
    service: ['dashboard', 'elderly', 'elderly-detail', 'alerts', 'reports', 'ai-risk-warning', 'ai-diagnosis']
};

function checkPermission(req, res, next) {
    const permission = req.params.permission || req.body.permission;
    
    if (!req.session || !req.session.user) {
        return res.status(401).json({
            success: false,
            message: '请先登录'
        });
    }

    const userPermissions = rolePermissions[req.session.user.role] || [];
    
    if (permission && !userPermissions.includes(permission)) {
        return res.status(403).json({
            success: false,
            message: '无此功能权限'
        });
    }

    return next();
}

module.exports = {
    requireAuth,
    requireRole,
    checkPermission,
    rolePermissions
};
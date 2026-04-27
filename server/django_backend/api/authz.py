from functools import wraps
from django.http import JsonResponse

ROLE_PERMISSIONS = {
    "admin": [
        "dashboard",
        "elderly",
        "elderly-detail",
        "orders",
        "alerts",
        "visits",
        "devices",
        "emergency",
        "monitor",
        "doctors",
        "reports",
        "ai-risk-warning",
        "ai-diagnosis",
        "settings",
    ],
    "doctor": [
        "dashboard",
        "elderly",
        "elderly-detail",
        "orders",
        "alerts",
        "monitor",
        "reports",
        "ai-risk-warning",
        "ai-diagnosis",
    ],
    "nurse": [
        "dashboard",
        "elderly",
        "elderly-detail",
        "visits",
        "devices",
        "alerts",
        "ai-risk-warning",
        "ai-diagnosis",
    ],
    "service": [
        "dashboard",
        "elderly",
        "elderly-detail",
        "alerts",
        "reports",
        "ai-risk-warning",
        "ai-diagnosis",
    ],
}


def require_auth(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("user"):
            return JsonResponse({"success": False, "message": "请先登录"}, status=401)
        return view_func(request, *args, **kwargs)

    return wrapper


def require_role(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.session.get("user")
            if not user:
                return JsonResponse({"success": False, "message": "请先登录"}, status=401)
            if user.get("role") not in roles:
                return JsonResponse({"success": False, "message": "权限不足"}, status=403)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator

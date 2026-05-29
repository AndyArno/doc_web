"""slowapi 限流器实例

提供全局 Limiter 实例，供 main.py 注册和 auth 端点装饰器使用。

key_func 使用三级降级策略：
1. X-Device-Id 请求头（前端注入的设备 ID）
2. JWT Bearer Token 的 sub 声明（已登录用户 ID）
3. IP 地址（兜底）
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings


def get_device_or_user_or_ip_key(request: Request) -> str:
    """三级降级限流键：设备 ID → JWT 用户 ID → IP 地址

    优先级：
    1. X-Device-Id 请求头（前端始终发送，优先按设备限流）
    2. JWT Bearer Token 的 sub 声明（非前端消费者降级：脚本、curl 等）
    3. IP 地址兜底（未认证请求）

    verify_exp=False 是有意设计：
    过期 token 仍按 user_id 限流，防止攻击者用过期 token 绕过限制。
    """
    # 1. Device ID（前端注入）
    device_id = request.headers.get("X-Device-Id")
    if device_id:
        return f"dev:{device_id}"

    # 2. JWT user ID（已登录用户）
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            from jose import jwt as _jwt
            from app.core.config import get_settings
            payload = _jwt.decode(
                auth[7:], get_settings().SECRET_KEY,
                algorithms=["HS256"],
                options={"verify_exp": False},
            )
            uid = payload.get("sub")
            if uid:
                return f"user:{uid}"
        except Exception:
            pass

    # 3. IP 地址兜底
    return f"ip:{get_remote_address(request)}"


settings = get_settings()

limiter = Limiter(
    key_func=get_device_or_user_or_ip_key,
    storage_uri=settings.REDIS_URL,
)

"""
安全模块

提供 JWT Token 创建/验证和密码哈希功能。
"""

from datetime import datetime, timedelta, UTC
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import SettingsDep

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """哈希密码

    Args:
        password: 明文密码

    Returns:
        bcrypt 哈希后的密码
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    settings: SettingsDep,
    expires_delta: timedelta | None = None,
    token_version: int = 0,
) -> str:
    """创建 JWT access token

    Args:
        data: 要编码的数据（通常包含 sub, role）
        settings: 配置实例
        expires_delta: 过期时间增量

    Returns:
        JWT token 字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(UTC),
        }
    )

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return encoded_jwt


def verify_token(
    token: str,
    settings: SettingsDep,
) -> dict[str, Any] | None:
    """验证并解码 JWT token

    Args:
        token: JWT token 字符串
        settings: 配置实例

    Returns:
        解码后的 payload，验证失败返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        return None

"""
依赖注入模块

提供 FastAPI 依赖注入函数和类型别名。
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, SettingsDep, get_settings
from app.core.exceptions import AppException
from app.core.security import verify_token
from app.db.session import get_db
from app.models.user import Role, User
from app.services.permission_service import ROLE_HIERARCHY, check_textbook_permission

# OAuth2 密码模式
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# OAuth2 可选模式（支持游客访问）
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login", auto_error=False
)


# === 数据库依赖 ===

SessionDep = Annotated[AsyncSession, Depends(get_db)]

# 向后兼容别名
get_session = get_db


# === 认证依赖 ===


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep,
    settings: SettingsDep,
) -> User:
    """获取当前认证用户

    Args:
        token: JWT token
        session: 数据库会话
        settings: 配置

    Returns:
        当前用户

    Raises:
        AppException: token 无效或用户不存在
    """
    credentials_exception = AppException(
        code=401,
        message="无法验证凭据",
        data=None,
    )

    payload = verify_token(token, settings)
    if payload is None:
        raise credentials_exception

    username: str | None = payload.get("sub")
    if username is None:
        raise credentials_exception

    # 查询用户
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise AppException(code=403, message="用户已被禁用", data=None)

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_optional_user(
    token: Annotated[str | None, Depends(oauth2_scheme_optional)],
    session: SessionDep,
    settings: SettingsDep,
) -> User | None:
    if token is None:
        return None

    payload = verify_token(token, settings)
    if payload is None:
        return None

    username: str | None = payload.get("sub")
    if username is None:
        return None

    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        return None

    return user


OptionalCurrentUser = Annotated[User | None, Depends(get_optional_user)]


# === 权限依赖 ===

def require_role(required_role: Role):
    """创建角色检查依赖

    Args:
        required_role: 需要的最低角色

    Returns:
        依赖函数
    """

    async def role_checker(current_user: CurrentUser) -> User:
        user_level = ROLE_HIERARCHY.get(current_user.role, 0)
        required_level = ROLE_HIERARCHY.get(required_role, 0)

        if user_level < required_level:
            raise AppException(
                code=403,
                message=f"需要 {required_role.value} 或更高权限",
                data=None,
            )

        return current_user

    return Depends(role_checker)


# 预定义的角色依赖
SuperAdminUser = Annotated[User, require_role(Role.SUPER_ADMIN)]
AdminUser = Annotated[User, require_role(Role.ADMIN)]
EditorUser = Annotated[User, require_role(Role.EDITOR)]


__all__ = [
    "SettingsDep",
    "SessionDep",
    "get_settings",
    "get_db",
    "get_session",
    "get_current_user",
    "CurrentUser",
    "get_optional_user",
    "OptionalCurrentUser",
    "require_role",
    "SuperAdminUser",
    "AdminUser",
    "EditorUser",
    "ROLE_HIERARCHY",
]

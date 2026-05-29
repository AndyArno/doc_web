"""认证服务模块

提供用户注册、认证、密码修改等核心业务逻辑。
"""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import Role, User
from app.schemas.user import (
    ForgotPasswordRequest,
    PasswordChange,
    Token,
    UserCreate,
    UserResponse,
)


async def register_user(session: AsyncSession, user_in: UserCreate) -> User:
    """用户注册

    创建新用户账户，默认角色为 user。

    Args:
        session: 数据库会话
        user_in: 用户注册数据

    Returns:
        创建的用户实例

    Raises:
        AppException: 用户名或邮箱已存在时抛出
    """
    result = await session.execute(
        select(User).where(User.username == user_in.username)
    )
    if result.scalar_one_or_none():
        raise AppException(code=409, message="用户名已被使用", data=None)

    result = await session.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise AppException(code=409, message="邮箱已被注册", data=None)

    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role=Role.USER,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


async def authenticate_user(
    session: AsyncSession,
    account: str,
    password: str,
    settings,
) -> tuple[User, Token]:
    """用户认证

    支持用户名或邮箱登录，验证成功返回用户和 token。

    Args:
        session: 数据库会话
        account: 用户名或邮箱
        password: 密码
        settings: 应用配置

    Returns:
        用户实例和 Token 的元组

    Raises:
        AppException: 认证失败或用户被禁用时抛出
    """
    result = await session.execute(
        select(User).where((User.username == account) | (User.email == account))
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise AppException(code=401, message="账号或密码错误", data=None)

    if not user.is_active:
        raise AppException(code=403, message="用户已被禁用", data=None)

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        settings=settings,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    token = Token(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )

    return user, token


async def change_user_password(
    session: AsyncSession,
    user: User,
    password_in: PasswordChange,
) -> None:
    """修改用户密码

    验证原密码后更新为新密码。

    Args:
        session: 数据库会话
        user: 当前用户
        password_in: 密码修改数据

    Raises:
        AppException: 原密码错误时抛出
    """
    if not verify_password(password_in.old_password, user.hashed_password):
        raise AppException(code=400, message="原密码错误", data=None)

    user.hashed_password = hash_password(password_in.new_password)
    user.must_change_password = False
    await session.commit()


async def forgot_password(
    session: AsyncSession,
    password_in: ForgotPasswordRequest,
) -> None:
    """忘记密码 - 未登录用户修改密码

    通过用户名/邮箱 + 原密码验证身份，然后修改密码。

    Args:
        session: 数据库会话
        password_in: 忘记密码请求

    Raises:
        AppException: 用户不存在或原密码错误
    """
    result = await session.execute(
        select(User).where(
            (User.username == password_in.account) | (User.email == password_in.account)
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise AppException(code=404, message="用户不存在", data=None)

    if not verify_password(password_in.old_password, user.hashed_password):
        raise AppException(code=400, message="原密码错误", data=None)

    user.hashed_password = hash_password(password_in.new_password)
    user.must_change_password = False
    await session.commit()

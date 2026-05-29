"""用户服务模块

提供用户管理相关的核心业务逻辑，包括用户 CRUD、角色管理、密码重置等。
"""

import math
import secrets
from typing import Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.core.security import hash_password
from app.models.permission import UserTextbookPermission
from app.models.user import Role, User
from app.schemas.user import (
    PasswordResetResponse,
    UserCreateByAdmin,
    UserDetailResponse,
    UserListResponse,
    UserResponse,
    UserRoleUpdate,
    UserUpdate,
)
from app.services.permission_service import ROLE_HIERARCHY


def check_user_role_permission(operator: User, target: User) -> None:
    """检查操作者是否有权限修改目标用户

    角色层级规则：
    - super_admin: 可修改所有
    - admin: 可修改 editor, user
    - editor: 不能修改角色

    Args:
        operator: 操作者
        target: 目标用户

    Raises:
        AppException: 权限不足时抛出 403
    """
    operator_level = ROLE_HIERARCHY.get(operator.role, 0)
    target_level = ROLE_HIERARCHY.get(target.role, 0)

    if operator_level <= target_level:
        raise AppException(
            code=403,
            message="权限不足，无法修改同级或更高级角色",
            data=None,
        )


async def get_users_paginated(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    role: Optional[Role] = None,
    keyword: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> UserListResponse:
    """获取用户分页列表

    支持按角色、关键词、状态筛选。

    Args:
        session: 数据库会话
        page: 页码（从 1 开始）
        page_size: 每页数量
        role: 角色筛选
        keyword: 关键词搜索（用户名或邮箱）
        is_active: 状态筛选

    Returns:
        用户分页列表响应
    """
    query = select(User)

    if role:
        query = query.where(User.role == role)

    if keyword:
        lower_keyword = f"%{keyword.lower()}%"
        query = query.where(
            or_(
                User.username.ilike(lower_keyword),
                User.email.ilike(lower_keyword),
            )
        )

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    users = result.scalars().all()

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


async def get_user_by_id(session: AsyncSession, user_id: int) -> User:
    """根据 ID 获取用户详情

    Args:
        session: 数据库会话
        user_id: 用户 ID

    Returns:
        用户实例（含权限列表）

    Raises:
        AppException: 用户不存在时抛出 404
    """
    result = await session.execute(
        select(User)
        .options(
            selectinload(User.permissions).selectinload(UserTextbookPermission.textbook)
        )
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise AppException(code=404, message="用户不存在", data=None)

    return user


async def create_user_by_admin(
    session: AsyncSession,
    user_in: UserCreateByAdmin,
    operator: User,
) -> User:
    """管理员创建用户

    只能创建不高于自己角色的用户。

    Args:
        session: 数据库会话
        user_in: 用户创建数据
        operator: 操作者（管理员）

    Returns:
        创建的用户实例

    Raises:
        AppException: 权限不足、用户名或邮箱已存在时抛出
    """
    if user_in.role == Role.SUPER_ADMIN:
        raise AppException(code=403, message="禁止创建超级管理员", data=None)

    if operator.role != Role.SUPER_ADMIN:
        new_user_level = ROLE_HIERARCHY.get(user_in.role, 0)
        operator_level = ROLE_HIERARCHY.get(operator.role, 0)
        if new_user_level >= operator_level:
            raise AppException(
                code=403,
                message="无法创建同级或更高级角色的用户",
                data=None,
            )

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
        role=user_in.role,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


async def update_user(
    session: AsyncSession,
    user_id: int,
    user_in: UserUpdate,
    operator: User,
) -> User:
    """更新用户信息

    只能修改自己，或作为管理员修改下级用户。

    Args:
        session: 数据库会话
        user_id: 目标用户 ID
        user_in: 用户更新数据
        operator: 操作者

    Returns:
        更新后的用户实例

    Raises:
        AppException: 用户不存在、权限不足、用户名或邮箱已存在时抛出
    """
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise AppException(code=404, message="用户不存在", data=None)

    if operator.id != user.id:
        check_user_role_permission(operator, user)

    if user_in.username is not None:
        result = await session.execute(
            select(User).where(User.username == user_in.username, User.id != user_id)
        )
        if result.scalar_one_or_none():
            raise AppException(code=409, message="用户名已被使用", data=None)
        user.username = user_in.username

    if user_in.email is not None:
        result = await session.execute(
            select(User).where(User.email == user_in.email, User.id != user_id)
        )
        if result.scalar_one_or_none():
            raise AppException(code=409, message="邮箱已被注册", data=None)
        user.email = user_in.email

    if user_in.is_active is not None:
        if operator.id != user.id:
            check_user_role_permission(operator, user)
        user.is_active = user_in.is_active

    await session.commit()
    await session.refresh(user)

    return user


async def delete_user(
    session: AsyncSession,
    user_id: int,
    operator: User,
) -> None:
    """删除用户

    不能删除自己，只能删除下级用户。

    Args:
        session: 数据库会话
        user_id: 目标用户 ID
        operator: 操作者（管理员）

    Raises:
        AppException: 用户不存在、尝试删除自己、权限不足时抛出
    """
    if user_id == operator.id:
        raise AppException(code=400, message="无法删除自己", data=None)

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise AppException(code=404, message="用户不存在", data=None)

    check_user_role_permission(operator, user)

    await session.delete(user)
    await session.commit()


async def update_user_role(
    session: AsyncSession,
    user_id: int,
    role_in: UserRoleUpdate,
    operator: User,
) -> Tuple[User, Role]:
    """修改用户角色

    只能修改下级用户；超管自降级时需保证系统中仍有其他超级管理员，且不能赋予同级或更高级角色。

    Args:
        session: 数据库会话
        user_id: 目标用户 ID
        role_in: 角色更新数据
        operator: 操作者（管理员）

    Returns:
        更新后的用户实例和原角色的元组

    Raises:
        AppException: 用户不存在、权限不足、禁止提升为超级管理员或最后一个超管降级时抛出
    """
    if role_in.role == Role.SUPER_ADMIN:
        raise AppException(code=403, message="禁止提升为超级管理员", data=None)

    if user_id == operator.id and operator.role != Role.SUPER_ADMIN:
        raise AppException(code=400, message="无法修改自己的角色", data=None)

    if user_id == operator.id and operator.role == Role.SUPER_ADMIN:
        new_role_level = ROLE_HIERARCHY.get(role_in.role, 0)
        operator_level = ROLE_HIERARCHY.get(operator.role, 0)
        if new_role_level < operator_level:
            result = await session.execute(
                select(func.count())
                .select_from(User)
                .where(User.role == Role.SUPER_ADMIN)
            )
            super_admin_count = result.scalar() or 0
            if super_admin_count <= 1:
                raise AppException(
                    code=400,
                    message="最后一个超级管理员，无法降级",
                    data=None,
                )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise AppException(code=404, message="用户不存在", data=None)

    if user_id != operator.id:
        check_user_role_permission(operator, user)

    new_role_level = ROLE_HIERARCHY.get(role_in.role, 0)
    operator_level = ROLE_HIERARCHY.get(operator.role, 0)
    if new_role_level >= operator_level:
        raise AppException(
            code=403,
            message="无法赋予同级或更高级角色",
            data=None,
        )

    old_role = user.role
    user.role = role_in.role
    await session.commit()

    return user, old_role


async def reset_user_password(
    session: AsyncSession,
    user_id: int,
    operator: User,
) -> PasswordResetResponse:
    """重置用户密码

    只能重置下级用户的密码。使用固定默认密码。

    Args:
        session: 数据库会话
        user_id: 目标用户 ID
        operator: 操作者（管理员）

    Returns:
        包含新密码和标志的响应

    Raises:
        AppException: 用户不存在、权限不足时抛出
    """
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise AppException(code=404, message="用户不存在", data=None)

    check_user_role_permission(operator, user)

    default_password = secrets.token_urlsafe(12)
    user.hashed_password = hash_password(default_password)
    user.must_change_password = True
    await session.commit()

    return PasswordResetResponse(
        must_change_password=True,
    )


__all__ = [
    "check_user_role_permission",
    "get_users_paginated",
    "get_user_by_id",
    "create_user_by_admin",
    "update_user",
    "delete_user",
    "update_user_role",
    "reset_user_password",
]

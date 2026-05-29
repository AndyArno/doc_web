"""用户管理 API 端点

提供用户 CRUD、角色管理、权限分配等接口。
"""

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, SessionDep
from app.core.exceptions import AppException
from app.models.textbook import Textbook
from app.models.user import Role
from app.schemas.user import (
    PermissionCreate,
    PermissionHistoryResponse,
    PermissionResponse,
    UserCreateByAdmin,
    UserDetailResponse,
    UserListResponse,
    PasswordResetResponse,
    UserResponse,
    UserRoleUpdate,
    UserUpdate,
)
from app.services import user_service
from app.services.permission_service import (
    assign_user_permission,
    get_permission_history,
    revoke_user_permission,
)

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("", response_model=dict)
async def get_users(
    session: SessionDep,
    current_user: AdminUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Role | None = None,
    keyword: str | None = None,
    is_active: bool | None = None,
) -> dict:
    """获取用户列表（分页）

    支持按角色、关键词、状态筛选。

    Returns:
        用户分页列表
    """
    result = await user_service.get_users_paginated(
        session=session,
        page=page,
        page_size=page_size,
        role=role,
        keyword=keyword,
        is_active=is_active,
    )
    return {
        "code": 200,
        "message": "success",
        "data": result.model_dump(),
    }


@router.get("/{user_id}", response_model=dict)
async def get_user(user_id: int, session: SessionDep, current_user: AdminUser) -> dict:
    """获取用户详情

    Returns:
        用户详情（含权限列表）
    """
    user = await user_service.get_user_by_id(session, user_id)
    return {
        "code": 200,
        "message": "success",
        "data": UserDetailResponse.model_validate(user).model_dump(),
    }


@router.post("", response_model=dict)
async def create_user(
    user_in: UserCreateByAdmin,
    session: SessionDep,
    current_user: AdminUser,
) -> dict:
    """创建用户（管理员）

    Returns:
        新创建的用户信息
    """
    user = await user_service.create_user_by_admin(session, user_in, current_user)
    return {
        "code": 200,
        "message": "创建成功",
        "data": UserResponse.model_validate(user).model_dump(),
    }


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """更新用户信息

    Returns:
        更新后的用户信息
    """
    user = await user_service.update_user(session, user_id, user_in, current_user)
    return {
        "code": 200,
        "message": "更新成功",
        "data": UserResponse.model_validate(user).model_dump(),
    }


@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    session: SessionDep,
    current_user: AdminUser,
) -> dict:
    """删除用户（管理员）

    Returns:
        成功响应
    """
    await user_service.delete_user(session, user_id, current_user)
    return {"code": 200, "message": "删除成功", "data": None}


@router.put("/{user_id}/role", response_model=dict)
async def update_user_role(
    user_id: int,
    role_in: UserRoleUpdate,
    session: SessionDep,
    current_user: AdminUser,
) -> dict:
    """修改用户角色（管理员）

    Returns:
        更新后的用户信息
    """
    user, old_role = await user_service.update_user_role(
        session, user_id, role_in, current_user
    )
    return {
        "code": 200,
        "message": "角色修改成功",
        "data": {
            "id": user.id,
            "username": user.username,
            "old_role": old_role.value,
            "new_role": role_in.role.value,
        },
    }


@router.post("/{user_id}/reset-password", response_model=dict)
async def reset_user_password(
    user_id: int,
    session: SessionDep,
    current_user: AdminUser,
) -> dict:
    """重置用户密码（管理员）

    使用固定默认密码重置用户密码，用户下次登录必须修改密码。

    Returns:
        包含新密码的响应
    """
    result = await user_service.reset_user_password(session, user_id, current_user)
    return {
        "code": 200,
        "message": "密码重置成功",
        "data": result.model_dump(),
    }


@router.post("/{user_id}/permissions", response_model=dict)
async def assign_user_permissions(
    user_id: int,
    permission_in: PermissionCreate,
    session: SessionDep,
    current_user: AdminUser,
) -> dict:
    """分配用户教材权限

    Returns:
        权限信息
    """
    user = await user_service.get_user_by_id(session, user_id)
    user_service.check_user_role_permission(current_user, user)

    result = await session.execute(
        select(Textbook).where(Textbook.id == permission_in.textbook_id)
    )
    textbook = result.scalar_one_or_none()
    if not textbook:
        raise AppException(code=404, message="教材不存在", data=None)

    permission = await assign_user_permission(
        session=session,
        user_id=user_id,
        textbook_id=permission_in.textbook_id,
        can_access=permission_in.can_access,
        operator_id=current_user.id,
    )

    return {
        "code": 200,
        "message": "权限分配成功",
        "data": PermissionResponse.model_validate(permission).model_dump(),
    }


@router.delete("/{user_id}/permissions/{textbook_id}", response_model=dict)
async def revoke_user_permissions(
    user_id: int,
    textbook_id: int,
    session: SessionDep,
    current_user: AdminUser,
) -> dict:
    """撤销用户教材权限

    Returns:
        成功响应
    """
    user = await user_service.get_user_by_id(session, user_id)
    user_service.check_user_role_permission(current_user, user)

    await revoke_user_permission(
        session=session,
        user_id=user_id,
        textbook_id=textbook_id,
        operator_id=current_user.id,
    )

    return {"code": 200, "message": "权限撤销成功", "data": None}


@router.get("/{user_id}/permissions/history", response_model=dict)
async def get_user_permission_history(
    user_id: int,
    session: SessionDep,
    current_user: AdminUser,
    textbook_id: int | None = Query(None, description="教材ID，可选"),
) -> dict:
    """获取用户权限变更历史

    Returns:
        权限变更历史列表
    """
    await user_service.get_user_by_id(session, user_id)

    history = await get_permission_history(
        session=session,
        user_id=user_id,
        textbook_id=textbook_id,
    )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": [
                PermissionHistoryResponse.model_validate(log).model_dump()
                for log in history
            ],
            "total": len(history),
        },
    }

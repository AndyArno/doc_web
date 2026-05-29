"""
权限服务模块

提供权限检查和管理功能，支持审计日志记录。
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.audit_log import AuditLog
from app.models.permission import UserTextbookPermission
from app.models.textbook import Textbook
from app.models.user import Role, User


ROLE_HIERARCHY = {
    Role.SUPER_ADMIN: 4,
    Role.ADMIN: 3,
    Role.EDITOR: 2,
    Role.USER: 1,
}


PERMISSION_FIELDS = {
    "edit": UserTextbookPermission.can_access,
    "create": UserTextbookPermission.can_access,
    "delete": UserTextbookPermission.can_access,
    "manage_users": UserTextbookPermission.can_access,
}


def check_role_permission(user: User, required_role: Role) -> bool:
    """检查用户是否具有指定角色或更高权限

    Args:
        user: 当前用户
        required_role: 需要的最低角色

    Returns:
        是否有权限
    """
    user_level = ROLE_HIERARCHY.get(user.role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 0)
    return user_level >= required_level


async def check_textbook_permission(
    session: AsyncSession,
    user: User,
    textbook_id: int,
    permission_type: str,
) -> None:
    """检查用户对指定教材的操作权限

    Args:
        session: 数据库会话
        user: 当前用户
        textbook_id: 教材 ID
        permission_type: 权限类型 (edit/create/delete/manage_users)

    Raises:
        AppException: 无权限时抛出 403 错误

    Note:
        权限范围说明:
        - super_admin: 全局权限，可操作所有教材（符合设计预期）
        - admin: 当前实现为全局权限，可操作所有教材
          设计预期应为"按教材授权"，需要 admin_textbooks 关联表实现范围限制。
          目前由于缺少该表，admin 暂时拥有全局权限，待后续迭代完善。
        - editor: 按 UserTextbookPermission 表中的具体权限授权
        - user: 无操作权限，仅只读
    """
    # super_admin 拥有全局权限
    # admin 当前也拥有全局权限（设计待完善，见函数文档说明）
    if user.role in (Role.SUPER_ADMIN, Role.ADMIN):
        return

    # editor 需要检查具体权限
    if user.role == Role.EDITOR:
        if permission_type not in PERMISSION_FIELDS:
            raise AppException(
                code=400,
                message=f"无效的权限类型: {permission_type}",
                data=None,
            )

        result = await session.execute(
            select(UserTextbookPermission).where(
                UserTextbookPermission.user_id == user.id,
                UserTextbookPermission.textbook_id == textbook_id,
                PERMISSION_FIELDS[permission_type].is_(True),
            )
        )
        permission = result.scalar_one_or_none()

        if permission is None:
            raise AppException(
                code=403,
                message="无权执行此操作",
                data=None,
            )
        return

    # 其他角色无操作权限
    raise AppException(
        code=403,
        message="无权执行此操作",
        data=None,
    )


async def assign_user_permission(
    session: AsyncSession,
    user_id: int,
    textbook_id: int,
    can_access: bool = False,
    operator_id: Optional[int] = None,
) -> UserTextbookPermission:
    """为用户分配教材权限并记录审计日志

    Args:
        session: 数据库会话
        user_id: 用户 ID
        textbook_id: 教材 ID
        can_access: 访问权限
        operator_id: 操作者 ID（用于审计日志）

    Returns:
        创建或更新后的权限记录
    """
    result = await session.execute(
        select(UserTextbookPermission).where(
            UserTextbookPermission.user_id == user_id,
            UserTextbookPermission.textbook_id == textbook_id,
        )
    )
    permission = result.scalar_one_or_none()
    is_update = permission is not None

    if permission:
        old_permissions = {
            "can_access": permission.can_access,
        }
        permission.can_access = can_access
    else:
        old_permissions = None
        permission = UserTextbookPermission(
            user_id=user_id,
            textbook_id=textbook_id,
            can_access=can_access,
        )
        session.add(permission)

    await session.commit()
    await session.refresh(permission)

    audit_log = AuditLog(
        action="permission_update" if is_update else "permission_assign",
        target_user_id=user_id,
        operator_id=operator_id,
        details={
            "textbook_id": textbook_id,
            "can_access": can_access,
        },
    )
    if is_update and old_permissions:
        audit_log.details["old_permissions"] = old_permissions
        audit_log.details["new_permissions"] = {
            "can_access": can_access,
        }

    session.add(audit_log)
    await session.commit()

    return permission


async def revoke_user_permission(
    session: AsyncSession,
    user_id: int,
    textbook_id: int,
    operator_id: Optional[int] = None,
) -> None:
    """撤销用户对教材的权限并记录审计日志

    Args:
        session: 数据库会话
        user_id: 用户 ID
        textbook_id: 教材 ID
        operator_id: 操作者 ID（用于审计日志）

    Raises:
        AppException: 权限记录不存在时抛出 404 错误
    """
    result = await session.execute(
        select(UserTextbookPermission).where(
            UserTextbookPermission.user_id == user_id,
            UserTextbookPermission.textbook_id == textbook_id,
        )
    )
    permission = result.scalar_one_or_none()

    if permission is None:
        raise AppException(
            code=404,
            message="权限记录不存在",
            data=None,
        )

    await session.delete(permission)

    audit_log = AuditLog(
        action="permission_revoke",
        target_user_id=user_id,
        operator_id=operator_id,
        details={
            "textbook_id": textbook_id,
        },
    )
    session.add(audit_log)
    await session.commit()


async def get_permission_history(
    session: AsyncSession,
    user_id: int,
    textbook_id: Optional[int] = None,
) -> List[AuditLog]:
    """获取用户权限变更历史

    Args:
        session: 数据库会话
        user_id: 用户 ID
        textbook_id: 可选的教材 ID，指定则只返回该教材的权限变更历史

    Returns:
        审计日志列表（按时间倒序）
    """
    query = (
        select(AuditLog)
        .where(
            AuditLog.target_user_id == user_id,
            AuditLog.action.in_(
                [
                    "permission_assign",
                    "permission_update",
                    "permission_revoke",
                ]
            ),
        )
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    )

    result = await session.execute(query)
    logs = list(result.scalars().all())

    if textbook_id is not None:
        logs = [
            log
            for log in logs
            if log.details and log.details.get("textbook_id") == textbook_id
        ]

    return logs


async def get_user_permissions(
    session: AsyncSession,
    user_id: int,
    textbook_id: Optional[int] = None,
) -> List[UserTextbookPermission]:
    """获取用户的权限列表

    Args:
        session: 数据库会话
        user_id: 用户 ID
        textbook_id: 可选的教材 ID，指定则只返回该教材的权限

    Returns:
        权限列表
    """
    query = select(UserTextbookPermission).where(
        UserTextbookPermission.user_id == user_id
    )

    if textbook_id:
        query = query.where(UserTextbookPermission.textbook_id == textbook_id)

    result = await session.execute(query)
    return list(result.scalars().all())


async def has_permission(
    session: AsyncSession,
    user: User,
    textbook_id: int,
    permission_type: str,
) -> bool:
    """检查用户是否具有指定教材的特定权限（不抛异常版本）

    Args:
        session: 数据库会话
        user: 当前用户
        textbook_id: 教材 ID
        permission_type: 权限类型

    Returns:
        是否有权限

    Note:
        权限范围说明同 check_textbook_permission 函数。
        admin 当前拥有全局权限，设计预期为按教材授权（待完善）。
    """
    # super_admin 拥有全局权限
    # admin 当前也拥有全局权限（设计待完善）
    if user.role in (Role.SUPER_ADMIN, Role.ADMIN):
        return True

    # 检查权限类型是否有效
    if permission_type not in PERMISSION_FIELDS:
        return False

    # editor 检查具体权限
    if user.role == Role.EDITOR:
        result = await session.execute(
            select(UserTextbookPermission).where(
                UserTextbookPermission.user_id == user.id,
                UserTextbookPermission.textbook_id == textbook_id,
                PERMISSION_FIELDS[permission_type].is_(True),
            )
        )
        permission = result.scalar_one_or_none()
        return permission is not None

    # 其他角色无权限
    return False


async def get_authorized_textbook_ids(
    session: AsyncSession,
    user: User,
) -> List[int]:
    """获取用户被授权的教材 ID 列表

    Args:
        session: 数据库会话
        user: 当前用户

    Returns:
        用户被授权的教材 ID 列表

    Note:
        权限范围说明:
        - super_admin: 返回所有教材 ID
        - admin/editor: 返回 UserTextbookPermission 中有记录的教材 ID
        - user: 返回空列表
    """
    if user.role == Role.SUPER_ADMIN:
        # 返回所有教材 ID
        result = await session.execute(select(Textbook.id))
        return [row[0] for row in result.all()]

    if user.role in (Role.ADMIN, Role.EDITOR):
        # 返回授权教材 ID
        result = await session.execute(
            select(UserTextbookPermission.textbook_id).where(
                UserTextbookPermission.user_id == user.id,
                UserTextbookPermission.can_access == True,
            )
        )
        return [row[0] for row in result.all()]

    # user 角色
    return []


__all__ = [
    "ROLE_HIERARCHY",
    "PERMISSION_FIELDS",
    "check_role_permission",
    "check_textbook_permission",
    "assign_user_permission",
    "revoke_user_permission",
    "get_user_permissions",
    "get_permission_history",
    "has_permission",
    "get_authorized_textbook_ids",
]

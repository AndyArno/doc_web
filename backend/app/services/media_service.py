"""媒体资源服务模块

提供媒体管理的业务逻辑，包括列表查询、软删除、回收站等功能。
"""

import logging
import math
import os
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models.media import Media
from app.models.user import User
from app.schemas.media import MediaListResponse, MediaResponse, TrashListResponse
from app.services.permission_service import check_textbook_permission

logger = logging.getLogger(__name__)


async def get_media_list_paginated(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    textbook_id: Optional[int] = None,
    chapter_id: Optional[int] = None,
    file_type: Optional[str] = None,
) -> MediaListResponse:
    """获取媒体分页列表

    只返回未删除的媒体，支持按教材、章节、文件类型筛选。

    Args:
        session: 数据库会话
        page: 当前页码（从1开始）
        page_size: 每页数量
        textbook_id: 可选的教材 ID 筛选
        chapter_id: 可选的章节 ID 筛选
        file_type: 可选的文件类型筛选（模糊匹配）

    Returns:
        分页响应对象
    """
    query = (
        select(Media)
        .options(selectinload(Media.textbook))
        .where(Media.is_deleted == False)
    )

    if textbook_id:
        query = query.where(Media.textbook_id == textbook_id)

    if chapter_id:
        query = query.where(Media.chapter_id == chapter_id)

    if file_type:
        query = query.where(Media.file_type.ilike(f"%{file_type}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Media.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    media_list = result.scalars().all()

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return MediaListResponse(
        items=[MediaResponse.model_validate(m) for m in media_list],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


async def get_trash_list(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
) -> TrashListResponse:
    """获取回收站媒体列表

    只返回已软删除的媒体，包含总大小统计。

    Args:
        session: 数据库会话
        page: 当前页码（从1开始）
        page_size: 每页数量

    Returns:
        回收站列表响应对象
    """
    query = (
        select(Media)
        .options(selectinload(Media.textbook))
        .where(Media.is_deleted.is_(True))
    )

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    size_query = select(func.sum(Media.file_size)).where(Media.is_deleted.is_(True))
    size_result = await session.execute(size_query)
    total_size = size_result.scalar() or 0
    total_size_mb = round(total_size / (1024 * 1024), 2)

    query = query.order_by(Media.deleted_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    media_list = result.scalars().all()

    return TrashListResponse(
        items=[MediaResponse.model_validate(m) for m in media_list],
        total=total,
        total_size_mb=total_size_mb,
    )


async def get_media_by_id(
    session: AsyncSession,
    media_id: int,
) -> Media:
    """根据 ID 获取媒体

    Args:
        session: 数据库会话
        media_id: 媒体 ID

    Returns:
        媒体对象

    Raises:
        AppException: 媒体不存在时抛出 404 错误
    """
    result = await session.execute(
        select(Media).options(selectinload(Media.textbook)).where(Media.id == media_id)
    )
    media = result.scalar_one_or_none()

    if not media:
        raise AppException(code=404, message="媒体不存在", data=None)

    return media


async def soft_delete_media(
    session: AsyncSession,
    media_id: int,
    user: Optional[User] = None,
) -> Media:
    """软删除媒体（移入回收站）

    如果提供了用户对象，会检查删除权限。

    Args:
        session: 数据库会话
        media_id: 媒体 ID
        user: 可选的用户对象（用于权限检查）

    Returns:
        被删除的媒体对象

    Raises:
        AppException: 媒体不存在或已在回收站或无权限时抛出错误
    """
    media = await get_media_by_id(session, media_id)

    # 权限检查
    if user and media.textbook_id:
        await check_textbook_permission(session, user, media.textbook_id, "delete")

    if media.is_deleted:
        raise AppException(code=400, message="媒体已在回收站中", data=None)

    media.soft_delete()
    await session.commit()
    await session.refresh(media)

    return media


async def restore_media(
    session: AsyncSession,
    media_id: int,
    user: Optional[User] = None,
) -> Media:
    """从回收站恢复媒体

    如果提供了用户对象，会检查编辑权限。

    Args:
        session: 数据库会话
        media_id: 媒体 ID
        user: 可选的用户对象（用于权限检查）

    Returns:
        恢复的媒体对象

    Raises:
        AppException: 媒体不存在或不在回收站或无权限时抛出错误
    """
    media = await get_media_by_id(session, media_id)

    # 权限检查
    if user and media.textbook_id:
        await check_textbook_permission(session, user, media.textbook_id, "edit")

    if not media.is_deleted:
        raise AppException(code=400, message="媒体不在回收站中", data=None)

    media.restore()
    await session.commit()
    await session.refresh(media)

    return media


async def permanently_delete_media(
    session: AsyncSession,
    media_id: int,
) -> None:
    """永久删除媒体

    同时删除物理文件。只能删除已在回收站中的媒体。

    Args:
        session: 数据库会话
        media_id: 媒体 ID

    Raises:
        AppException: 媒体不存在或未在回收站时抛出错误
    """
    media = await get_media_by_id(session, media_id)

    if not media.is_deleted:
        raise AppException(code=400, message="请先移入回收站", data=None)

    # 删除物理文件
    file_path = media.file_path
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info("已删除文件: %s", file_path)
        except OSError as e:
            logger.warning("删除文件失败: %s, 错误: %s", file_path, e)

    await session.delete(media)
    await session.commit()


async def clear_trash(
    session: AsyncSession,
) -> int:
    """清空回收站

    永久删除所有回收站中的媒体及其物理文件。

    Args:
        session: 数据库会话

    Returns:
        删除的数量
    """
    result = await session.execute(select(Media).where(Media.is_deleted.is_(True)))
    media_list = result.scalars().all()

    deleted_count = 0
    for media in media_list:
        file_path = media.file_path
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info("已删除文件: %s", file_path)
            except OSError as e:
                logger.warning("删除文件失败: %s, 错误: %s", file_path, e)

        await session.delete(media)
        deleted_count += 1

    await session.commit()

    return deleted_count


async def delete_media_by_textbook(
    session: AsyncSession,
    textbook_id: int,
) -> int:
    """删除教材关联的所有媒体

    包括已软删除的媒体，彻底清理数据库记录和物理文件。
    用于教材删除时的级联清理。

    Args:
        session: 数据库会话
        textbook_id: 教材 ID

    Returns:
        删除的数量
    """
    result = await session.execute(
        select(Media).where(Media.textbook_id == textbook_id)
    )
    media_list = result.scalars().all()

    deleted_count = 0
    for media in media_list:
        file_path = media.file_path
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info("已删除文件: %s", file_path)
            except OSError as e:
                logger.warning("删除文件失败: %s, 错误: %s", file_path, e)

        await session.delete(media)
        deleted_count += 1

    await session.commit()

    return deleted_count


__all__ = [
    "get_media_list_paginated",
    "get_trash_list",
    "get_media_by_id",
    "soft_delete_media",
    "restore_media",
    "permanently_delete_media",
    "clear_trash",
    "delete_media_by_textbook",
]

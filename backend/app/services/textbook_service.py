"""教材服务模块

提供教材管理的业务逻辑，包括 CRUD、发布管理、文件清理等功能。
"""

import logging
import math
import os
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.chapter import Chapter, generate_slug
from app.models.media import Media
from app.models.textbook import Textbook, TextbookStatus
from app.models.user import Role
from app.schemas.textbook import (
    TextbookCreate,
    TextbookListResponse,
    TextbookResponse,
    TextbookUpdate,
)
from app.services import search_service
from app.services.permission_service import check_textbook_permission
from app.utils.chapter import build_chapter_tree

if TYPE_CHECKING:
    from app.models.user import User

logger = logging.getLogger(__name__)


async def generate_unique_slug(title: str, session: AsyncSession) -> str:
    """生成唯一的 slug

    支持中文标题，通过递增数字后缀确保唯一性。

    Args:
        title: 教材标题
        session: 数据库会话

    Returns:
        唯一的 slug 字符串
    """
    base_slug = generate_slug(title)
    if not base_slug:
        base_slug = f"textbook-{uuid.uuid4().hex[:8]}"

    slug = base_slug
    counter = 1

    while True:
        result = await session.execute(select(Textbook).where(Textbook.slug == slug))
        if not result.scalar_one_or_none():
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


async def get_textbooks_paginated(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    status: Optional[TextbookStatus] = None,
    user: Optional["User"] = None,
    for_management: bool = False,
) -> TextbookListResponse:
    """获取教材分页列表

    Args:
        session: 数据库会话
        page: 当前页码（从1开始）
        page_size: 每页数量
        keyword: 搜索关键词（模糊匹配标题）
        status: 状态筛选
        user: 当前用户（用于权限过滤）
        for_management: 是否为管理模式
            - True: 管理页面，按权限过滤
            - False: 首页，返回所有已发布教材

    Returns:
        分页响应对象
    """
    query = select(Textbook)

    if keyword:
        lower_keyword = f"%{keyword.lower()}%"
        query = query.where(Textbook.title.ilike(lower_keyword))

    if for_management:
        from app.services.permission_service import get_authorized_textbook_ids

        if user:
            if user.role == Role.SUPER_ADMIN:
                pass  # super_admin 看所有教材
            elif user.role in (Role.ADMIN, Role.EDITOR):
                authorized_ids = await get_authorized_textbook_ids(session, user)
                if authorized_ids:
                    query = query.where(Textbook.id.in_(authorized_ids))
                else:
                    query = query.where(Textbook.id == -1)
            else:
                query = query.where(Textbook.id == -1)

        if status:
            query = query.where(Textbook.status == status)
    else:
        if user and user.role == Role.USER:
            query = query.where(Textbook.status == TextbookStatus.PUBLISHED)
            if status:
                query = query.where(Textbook.status == status)
        elif status:
            query = query.where(Textbook.status == status)
        else:
            query = query.where(Textbook.status == TextbookStatus.PUBLISHED)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Textbook.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    textbooks = result.scalars().all()

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return TextbookListResponse(
        items=[TextbookResponse.model_validate(t) for t in textbooks],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


async def get_textbook_by_id(
    session: AsyncSession,
    textbook_id: int,
) -> Optional[Textbook]:
    """根据 ID 获取教材

    Args:
        session: 数据库会话
        textbook_id: 教材 ID

    Returns:
        教材对象，不存在则返回 None

    Raises:
        AppException: 教材不存在时抛出 404 错误
    """
    result = await session.execute(select(Textbook).where(Textbook.id == textbook_id))
    textbook = result.scalar_one_or_none()

    if not textbook:
        raise AppException(code=404, message="教材不存在", data=None)

    return textbook


async def get_textbook_with_chapters(
    session: AsyncSession,
    textbook_id: int,
) -> dict:
    """获取教材详情（含章节树）

    Args:
        session: 数据库会话
        textbook_id: 教材 ID

    Returns:
        包含教材信息和章节树的字典

    Raises:
        AppException: 教材不存在时抛出 404 错误
    """
    textbook = await get_textbook_by_id(session, textbook_id)

    chapters_result = await session.execute(
        select(Chapter)
        .where(Chapter.textbook_id == textbook_id)
        .order_by(Chapter.order_index)
    )
    chapters = list(chapters_result.scalars().all())

    chapter_tree = build_chapter_tree(chapters)

    return {
        **TextbookResponse.model_validate(textbook).model_dump(),
        "chapters": [node.model_dump() for node in chapter_tree],
    }


async def create_textbook(
    session: AsyncSession,
    textbook_in: TextbookCreate,
) -> Textbook:
    """创建教材

    Args:
        session: 数据库会话
        textbook_in: 创建数据

    Returns:
        新创建的教材对象
    """
    slug = await generate_unique_slug(textbook_in.title, session)

    textbook = Textbook(
        title=textbook_in.title,
        description=textbook_in.description,
        cover_image=textbook_in.cover_image,
        slug=slug,
        status=textbook_in.status,
    )

    session.add(textbook)
    await session.commit()
    await session.refresh(textbook)

    return textbook


async def update_textbook(
    session: AsyncSession,
    textbook_id: int,
    textbook_in: TextbookUpdate,
    user_id: Optional[int] = None,
) -> Textbook:
    """更新教材

    如果提供了 user_id，会检查编辑权限。

    Args:
        session: 数据库会话
        textbook_id: 教材 ID
        textbook_in: 更新数据
        user_id: 可选的用户 ID（用于权限检查）

    Returns:
        更新后的教材对象

    Raises:
        AppException: 教材不存在或无权限时抛出错误
    """
    from app.models.user import User

    textbook = await get_textbook_by_id(session, textbook_id)

    # 可选权限检查：若提供了 user_id 则验证编辑权限
    if user_id:
        user_result = await session.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            await check_textbook_permission(session, user, textbook_id, "edit")

    if textbook_in.title is not None:
        textbook.title = textbook_in.title
        slug = await generate_unique_slug(textbook_in.title, session)
        textbook.slug = slug

    if textbook_in.description is not None:
        textbook.description = textbook_in.description

    if textbook_in.cover_image is not None:
        textbook.cover_image = textbook_in.cover_image

    if textbook_in.status is not None:
        textbook.status = textbook_in.status

    await session.commit()
    await session.refresh(textbook)

    return textbook


async def delete_textbook(
    session: AsyncSession,
    textbook_id: int,
) -> None:
    """删除教材

    删除前清理关联的 media 文件（磁盘文件和数据库记录）。

    Args:
        session: 数据库会话
        textbook_id: 教材 ID

    Raises:
        AppException: 教材不存在时抛出 404 错误
    """
    textbook = await get_textbook_by_id(session, textbook_id)

    # 删除搜索索引（最佳努力，失败不影响主流程）
    try:
        await search_service.delete_textbook_indexes(session, textbook_id)
    except Exception as e:
        logger.warning("删除教材搜索索引失败: %s", e)

    # 包括已软删除的 media，确保彻底清理
    media_result = await session.execute(
        select(Media).where(Media.textbook_id == textbook_id)
    )
    media_list = media_result.scalars().all()

    # 删除磁盘文件，失败时仅记录警告不中断流程
    for media in media_list:
        file_path = media.file_path
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info("已删除文件: %s", file_path)
            except OSError as e:
                logger.warning("删除文件失败: %s, 错误: %s", file_path, e)

        await session.delete(media)

    await session.delete(textbook)
    await session.commit()


async def publish_textbook(
    session: AsyncSession,
    textbook_id: int,
) -> Textbook:
    """发布教材

    Args:
        session: 数据库会话
        textbook_id: 教材 ID

    Returns:
        更新后的教材对象

    Raises:
        AppException: 教材不存在时抛出 404 错误
    """
    textbook = await get_textbook_by_id(session, textbook_id)

    textbook.status = TextbookStatus.PUBLISHED
    await session.commit()
    await session.refresh(textbook)

    return textbook


async def unpublish_textbook(
    session: AsyncSession,
    textbook_id: int,
) -> Textbook:
    """取消发布教材

    Args:
        session: 数据库会话
        textbook_id: 教材 ID

    Returns:
        更新后的教材对象

    Raises:
        AppException: 教材不存在时抛出 404 错误
    """
    textbook = await get_textbook_by_id(session, textbook_id)

    # 删除搜索索引（最佳努力，失败不影响主流程）
    try:
        await search_service.delete_textbook_indexes(session, textbook_id)
    except Exception as e:
        logger.warning("删除教材搜索索引失败: %s", e)

    textbook.status = TextbookStatus.DRAFT
    await session.commit()
    await session.refresh(textbook)

    return textbook


__all__ = [
    "generate_unique_slug",
    "get_textbooks_paginated",
    "get_textbook_by_id",
    "get_textbook_with_chapters",
    "create_textbook",
    "update_textbook",
    "delete_textbook",
    "publish_textbook",
    "unpublish_textbook",
]

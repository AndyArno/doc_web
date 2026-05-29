"""
章节服务模块

提供章节 CRUD、排序、导航等功能。
"""

import logging
import re
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.chapter import Chapter, NodeType, generate_slug
from app.models.textbook import Textbook
from app.models.user import User
from app.schemas.chapter import (
    ChapterCreate,
    ChapterNavigation,
    ChapterReorderRequest,
    ChapterResponse,
    ChapterTreeResponse,
    ChapterTreeNode,
    ChapterUpdate,
)
from app.services import search_service, version_service
from app.services.permission_service import check_textbook_permission
from app.utils.chapter import build_chapter_tree, flatten_chapters

logger = logging.getLogger(__name__)

# 最大章节层级
MAX_LEVEL = 3


async def _ensure_unique_slug(
    session: AsyncSession,
    textbook_id: int,
    slug: str,
    exclude_chapter_id: Optional[int] = None,
) -> str:
    """确保 slug 在同一教材内唯一

    如果 slug 已存在，自动添加数字后缀。

    Args:
        session: 数据库会话
        textbook_id: 教材 ID
        slug: 原始 slug
        exclude_chapter_id: 排除的章节 ID（用于更新时排除自身）

    Returns:
        唯一的 slug 字符串
    """
    # 查询同一教材内相同 slug 的章节
    query = select(Chapter).where(
        Chapter.textbook_id == textbook_id,
        Chapter.slug == slug,
    )
    if exclude_chapter_id:
        query = query.where(Chapter.id != exclude_chapter_id)

    result = await session.execute(query)
    existing = result.scalar_one_or_none()

    if not existing:
        return slug

    # slug 已存在，添加数字后缀
    base_slug = slug
    counter = 1
    while True:
        new_slug = f"{base_slug}-{counter}"
        query = select(Chapter).where(
            Chapter.textbook_id == textbook_id,
            Chapter.slug == new_slug,
        )
        if exclude_chapter_id:
            query = query.where(Chapter.id != exclude_chapter_id)

        result = await session.execute(query)
        if not result.scalar_one_or_none():
            return new_slug
        counter += 1


async def get_chapters_tree(
    session: AsyncSession,
    textbook_id: int,
) -> ChapterTreeResponse:
    """获取教材的章节树结构

    Args:
        session: 数据库会话
        textbook_id: 教材 ID

    Returns:
        章节树响应对象

    Raises:
        AppException: 教材不存在时抛出 404 错误
    """
    # 检查教材是否存在
    result = await session.execute(select(Textbook).where(Textbook.id == textbook_id))
    textbook = result.scalar_one_or_none()

    if not textbook:
        raise AppException(code=404, message="教材不存在", data=None)

    # 获取教材的所有章节
    chapters_result = await session.execute(
        select(Chapter)
        .where(Chapter.textbook_id == textbook_id)
        .order_by(Chapter.order_index)
    )
    chapters = list(chapters_result.scalars().all())

    # 构建章节树
    chapter_tree = build_chapter_tree(chapters)

    return ChapterTreeResponse(
        textbook_id=textbook_id,
        textbook_title=textbook.title,
        chapters=chapter_tree,
    )


async def get_chapter_by_id(
    session: AsyncSession,
    chapter_id: int,
) -> Chapter:
    """根据 ID 获取章节

    Args:
        session: 数据库会话
        chapter_id: 章节 ID

    Returns:
        章节对象

    Raises:
        AppException: 章节不存在时抛出 404 错误
    """
    result = await session.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()

    if not chapter:
        raise AppException(code=404, message="章节不存在", data=None)

    return chapter


async def get_chapter_with_navigation(
    session: AsyncSession,
    chapter_id: int,
) -> ChapterResponse:
    """获取章节详情及其导航信息（上一章/下一章）

    Args:
        session: 数据库会话
        chapter_id: 章节 ID

    Returns:
        包含导航信息的章节响应对象

    Raises:
        AppException: 章节不存在时抛出 404 错误
    """
    # 获取章节
    chapter = await get_chapter_by_id(session, chapter_id)

    # 获取同一教材的所有章节
    chapters_result = await session.execute(
        select(Chapter)
        .where(Chapter.textbook_id == chapter.textbook_id)
        .order_by(Chapter.order_index)
    )
    all_chapters = list(chapters_result.scalars().all())

    # 扁平化章节树
    flat_chapters = flatten_chapters(all_chapters)

    # 找到当前章节在扁平列表中的位置
    current_index = next(
        (i for i, ch in enumerate(flat_chapters) if ch.id == chapter_id), -1
    )

    # 构建导航信息
    navigation = ChapterNavigation()
    if current_index > 0:
        prev_chapter = flat_chapters[current_index - 1]
        navigation.prev = {"id": prev_chapter.id, "title": prev_chapter.title}
    if current_index < len(flat_chapters) - 1:
        next_chapter = flat_chapters[current_index + 1]
        navigation.next = {"id": next_chapter.id, "title": next_chapter.title}

    return ChapterResponse(
        id=chapter.id,
        textbook_id=chapter.textbook_id,
        parent_id=chapter.parent_id,
        title=chapter.title,
        slug=chapter.slug,
        level=chapter.level,
        order_index=chapter.order_index,
        node_type=chapter.node_type,
        content=chapter.content,
        created_at=chapter.created_at,
        updated_at=chapter.updated_at,
        navigation=navigation,
    )


async def create_chapter(
    session: AsyncSession,
    user: User,
    chapter_in: ChapterCreate,
) -> Chapter:
    """创建新章节

    包含层级验证和权限检查。

    Args:
        session: 数据库会话
        user: 当前用户
        chapter_in: 章节创建数据

    Returns:
        创建的章节对象

    Raises:
        AppException: 教材不存在时抛出 404 错误
        AppException: 父章节不存在时抛出 404 错误
        AppException: 父章节不属于该教材时抛出 400 错误
        AppException: 层级超过限制时抛出 400 错误
        AppException: 无权限时抛出 403 错误
    """
    # 检查教材是否存在
    result = await session.execute(
        select(Textbook).where(Textbook.id == chapter_in.textbook_id)
    )
    textbook = result.scalar_one_or_none()

    if not textbook:
        raise AppException(code=404, message="教材不存在", data=None)

    # 检查权限
    await check_textbook_permission(session, user, chapter_in.textbook_id, "create")

    # 计算层级
    level = 1
    if chapter_in.parent_id:
        parent_result = await session.execute(
            select(Chapter).where(Chapter.id == chapter_in.parent_id)
        )
        parent = parent_result.scalar_one_or_none()

        if not parent:
            raise AppException(code=404, message="父章节不存在", data=None)

        if parent.textbook_id != chapter_in.textbook_id:
            raise AppException(code=400, message="父章节不属于该教材", data=None)

        if parent.node_type != NodeType.FOLDER:
            raise AppException(code=400, message="文章节点不能包含子节点", data=None)

        level = parent.level + 1

        if level > MAX_LEVEL:
            raise AppException(
                code=400,
                message=f"章节层级不能超过 {MAX_LEVEL} 层",
                data=None,
            )

    # 生成 slug 并确保唯一
    slug = generate_slug(chapter_in.title)
    slug = await _ensure_unique_slug(session, chapter_in.textbook_id, slug)

    content = None if chapter_in.node_type == NodeType.FOLDER else chapter_in.content

    # 创建章节
    chapter = Chapter(
        textbook_id=chapter_in.textbook_id,
        parent_id=chapter_in.parent_id,
        title=chapter_in.title,
        content=content,
        slug=slug,
        level=level,
        order_index=chapter_in.order_index,
        node_type=chapter_in.node_type,
    )

    session.add(chapter)
    await session.commit()
    await session.refresh(chapter)

    # 同步搜索索引（最佳努力，失败不影响主流程）
    try:
        await search_service.index_chapter(
            session=session,
            chapter_id=chapter.id,
            title=chapter.title,
            content=chapter.content,
            textbook_id=chapter.textbook_id,
            textbook_title=textbook.title,
        )
    except Exception as e:
        logger.error(f"Failed to index chapter {chapter.id}: {e}")
        # 回滚将连接从 aborted 状态恢复，避免后续操作失败
        await session.rollback()

    return chapter


async def update_chapter(
    session: AsyncSession,
    user: User,
    chapter_id: int,
    chapter_in: ChapterUpdate,
) -> Chapter:
    """更新章节

    Args:
        session: 数据库会话
        user: 当前用户
        chapter_id: 章节 ID
        chapter_in: 章节更新数据

    Returns:
        更新后的章节对象

    Raises:
        AppException: 章节不存在时抛出 404 错误
        AppException: 无权限时抛出 403 错误
    """
    # 获取章节
    chapter = await get_chapter_by_id(session, chapter_id)

    # 检查权限
    await check_textbook_permission(session, user, chapter.textbook_id, "edit")

    # 更新字段
    if chapter_in.title is not None:
        chapter.title = chapter_in.title
        new_slug = generate_slug(chapter_in.title)
        chapter.slug = await _ensure_unique_slug(
            session, chapter.textbook_id, new_slug, exclude_chapter_id=chapter.id
        )

    # 更新内容：只有 ARTICLE 类型可以更新 content
    if chapter_in.content is not None:
        if chapter.node_type == NodeType.ARTICLE:
            chapter.content = chapter_in.content
        # FOLDER 类型忽略 content 更新

    # 更新 parent_id
    old_parent_id = chapter.parent_id

    if chapter_in.parent_id is not None:
        # 移动到指定父节点
        if chapter_in.parent_id != old_parent_id:
            # 1. 查询父节点是否存在
            parent_result = await session.execute(
                select(Chapter).where(Chapter.id == chapter_in.parent_id)
            )
            parent = parent_result.scalar_one_or_none()

            if not parent:
                raise AppException(
                    code=404,
                    message=f"父章节 {chapter_in.parent_id} 不存在",
                    data=None,
                )

            # 2. 检查父节点是否属于同一教材
            if parent.textbook_id != chapter.textbook_id:
                raise AppException(
                    code=400,
                    message="父章节不属于该教材",
                    data=None,
                )

            # 3. 检查父节点是否为 FOLDER 类型
            if parent.node_type != NodeType.FOLDER:
                raise AppException(
                    code=400,
                    message="文章节点不能包含子节点",
                    data=None,
                )

            # 4. 检查循环引用
            await _check_circular_reference(
                session, chapter.id, chapter_in.parent_id, chapter.textbook_id
            )

            # 5. 计算新层级，检查是否超过 MAX_LEVEL
            new_level = parent.level + 1
            if new_level > MAX_LEVEL:
                raise AppException(
                    code=400,
                    message=f"章节层级不能超过 {MAX_LEVEL} 层",
                    data=None,
                )

            # 6. 更新 chapter.parent_id 和 chapter.level
            chapter.parent_id = chapter_in.parent_id
            chapter.level = new_level

            # 7. 设置 order_index 为目标父节点子节点末尾
            siblings_result = await session.execute(
                select(Chapter).where(
                    Chapter.parent_id == chapter_in.parent_id,
                    Chapter.textbook_id == chapter.textbook_id,
                )
            )
            siblings = list(siblings_result.scalars().all())
            max_order = max((sib.order_index for sib in siblings), default=-1)
            chapter.order_index = max_order + 1

            # 8. 调用 _update_descendant_levels 更新后代层级
            all_chapters_result = await session.execute(
                select(Chapter).where(Chapter.textbook_id == chapter.textbook_id)
            )
            all_chapters_map = {ch.id: ch for ch in all_chapters_result.scalars().all()}
            all_chapters_map[chapter.id] = chapter
            await _update_descendant_levels(session, chapter, all_chapters_map)
    elif chapter_in.parent_id is None and old_parent_id is not None:
        # 移动到根级别
        chapter.parent_id = None
        chapter.level = 1

        # 更新 order_index（放在根级别末尾）
        siblings_result = await session.execute(
            select(Chapter).where(
                Chapter.parent_id.is_(None),
                Chapter.textbook_id == chapter.textbook_id,
            )
        )
        siblings = list(siblings_result.scalars().all())
        max_order = max((sib.order_index for sib in siblings), default=-1)
        chapter.order_index = max_order + 1

        # 更新后代层级
        all_chapters_result = await session.execute(
            select(Chapter).where(Chapter.textbook_id == chapter.textbook_id)
        )
        all_chapters_map = {ch.id: ch for ch in all_chapters_result.scalars().all()}
        all_chapters_map[chapter.id] = chapter
        await _update_descendant_levels(session, chapter, all_chapters_map)

    # 保存版本：只在更新内容且为 ARTICLE 类型时保存
    if chapter_in.content is not None and chapter.node_type == NodeType.ARTICLE:
        await version_service.save_version(
            session=session,
            chapter_id=chapter.id,
            content=chapter.content,
            user_id=user.id,
        )

    await session.commit()
    await session.refresh(chapter)

    # 同步搜索索引（最佳努力，失败不影响主流程）
    try:
        textbook = await session.get(Textbook, chapter.textbook_id)
        if textbook:
            await search_service.update_chapter_index(
                session=session,
                chapter_id=chapter.id,
                title=chapter.title,
                content=chapter.content,
                textbook_id=chapter.textbook_id,
                textbook_title=textbook.title,
            )
    except Exception as e:
        logger.error(f"Failed to update chapter index {chapter.id}: {e}")

    return chapter


async def delete_chapter(
    session: AsyncSession,
    user: User,
    chapter_id: int,
) -> None:
    """删除章节

    由于模型定义了级联删除，删除父章节会同时删除所有子章节。

    Args:
        session: 数据库会话
        user: 当前用户
        chapter_id: 章节 ID

    Raises:
        AppException: 章节不存在时抛出 404 错误
        AppException: 无权限时抛出 403 错误
    """
    # 获取章节
    chapter = await get_chapter_by_id(session, chapter_id)

    # 检查权限
    await check_textbook_permission(session, user, chapter.textbook_id, "delete")

    # 删除搜索索引（最佳努力，失败不影响主流程）
    try:
        await search_service.delete_chapter_index(session, chapter_id)
    except Exception as e:
        logger.error(f"Failed to delete chapter index {chapter_id}: {e}")

    # 删除章节（级联删除子章节）
    await session.delete(chapter)
    await session.commit()


async def _check_circular_reference(
    session: AsyncSession,
    chapter_id: int,
    target_parent_id: int,
    textbook_id: int,
) -> None:
    """检查是否会造成循环引用

    如果将章节移动到其子孙节点下，会形成循环引用。

    Args:
        session: 数据库会话
        chapter_id: 被移动的章节 ID
        target_parent_id: 目标父章节 ID
        textbook_id: 教材 ID

    Raises:
        AppException: 如果目标父节点是被移动章节的后代节点
    """
    # 获取该教材所有章节
    result = await session.execute(
        select(Chapter).where(Chapter.textbook_id == textbook_id)
    )
    all_chapters = list(result.scalars().all())

    # 构建 parent_id -> [children] 映射
    children_map: dict[int | None, list[int]] = {}
    for ch in all_chapters:
        if ch.parent_id not in children_map:
            children_map[ch.parent_id] = []
        children_map[ch.parent_id].append(ch.id)

    # 递归获取所有后代节点 ID
    descendant_ids: set[int] = set()

    def collect_descendants(node_id: int) -> None:
        """递归收集所有后代节点"""
        for child_id in children_map.get(node_id, []):
            descendant_ids.add(child_id)
            collect_descendants(child_id)

    collect_descendants(chapter_id)

    # 检查目标父节点是否是后代节点
    if target_parent_id in descendant_ids:
        raise AppException(
            code=400,
            message="不能将章节移动到其子节点下",
            data=None,
        )


async def _update_descendant_levels(
    session: AsyncSession,
    chapter: Chapter,
    chapters_map: dict[int, Chapter],
) -> None:
    """递归更新所有后代节点的 level

    当章节的 parent_id 改变时，需要更新其所有后代节点的 level。
    新 level = 父节点.level + 1

    Args:
        session: 数据库会话
        chapter: 已更新 level 的章节
        chapters_map: 章节 ID 到章节对象的映射（用于查找子节点）

    Raises:
        AppException: 如果更新后的 level 超过 MAX_LEVEL
    """
    children = [ch for ch in chapters_map.values() if ch.parent_id == chapter.id]

    for child in children:
        new_level = chapter.level + 1
        if new_level > MAX_LEVEL:
            raise AppException(
                code=400,
                message=f"移动后子章节 '{child.title}' 的层级将超过 {MAX_LEVEL} 层",
                data=None,
            )
        child.level = new_level
        await _update_descendant_levels(session, child, chapters_map)


async def reorder_chapters(
    session: AsyncSession,
    user: User,
    reorder_in: ChapterReorderRequest,
) -> None:
    """重新排序章节

    支持批量更新章节的排序和层级关系。

    Args:
        session: 数据库会话
        user: 当前用户
        reorder_in: 排序请求数据

    Raises:
        AppException: 教材不存在时抛出 404 错误
        AppException: 章节不属于该教材时抛出 400 错误
        AppException: 父章节不存在时抛出 404 错误
        AppException: 父章节不属于该教材时抛出 400 错误
        AppException: 层级超过限制时抛出 400 错误
        AppException: 循环引用时抛出 400 错误
    """
    await check_textbook_permission(session, user, reorder_in.textbook_id, "edit")

    result = await session.execute(
        select(Textbook).where(Textbook.id == reorder_in.textbook_id)
    )
    textbook = result.scalar_one_or_none()

    if not textbook:
        raise AppException(code=404, message="教材不存在", data=None)

    chapter_ids = [item.id for item in reorder_in.orders]

    chapters_result = await session.execute(
        select(Chapter).where(Chapter.id.in_(chapter_ids))
    )
    chapters = {ch.id: ch for ch in chapters_result.scalars().all()}

    all_chapters_result = await session.execute(
        select(Chapter).where(Chapter.textbook_id == reorder_in.textbook_id)
    )
    all_chapters_map = {ch.id: ch for ch in all_chapters_result.scalars().all()}

    chapters_to_update_descendants: list[Chapter] = []

    for item in reorder_in.orders:
        chapter = chapters.get(item.id)
        if not chapter:
            continue

        if chapter.textbook_id != reorder_in.textbook_id:
            raise AppException(
                code=400,
                message=f"章节 {item.id} 不属于该教材",
                data=None,
            )

        chapter.order_index = item.order_index

        old_parent_id = chapter.parent_id

        if item.parent_id is not None:
            parent_result = await session.execute(
                select(Chapter).where(Chapter.id == item.parent_id)
            )
            parent = parent_result.scalar_one_or_none()

            if not parent:
                raise AppException(
                    code=404,
                    message=f"父章节 {item.parent_id} 不存在",
                    data=None,
                )

            if parent.textbook_id != reorder_in.textbook_id:
                raise AppException(
                    code=400,
                    message="父章节不属于该教材",
                    data=None,
                )

            if parent.node_type != NodeType.FOLDER:
                raise AppException(
                    code=400, message="文章节点不能包含子节点", data=None
                )

            await _check_circular_reference(
                session, chapter.id, item.parent_id, reorder_in.textbook_id
            )

            new_level = parent.level + 1
            if new_level > MAX_LEVEL:
                raise AppException(
                    code=400,
                    message=f"章节层级不能超过 {MAX_LEVEL} 层",
                    data=None,
                )

            chapter.parent_id = item.parent_id
            chapter.level = new_level
        else:
            chapter.parent_id = None
            chapter.level = 1

        if chapter.parent_id != old_parent_id:
            all_chapters_map[chapter.id] = chapter
            chapters_to_update_descendants.append(chapter)

    for chapter in chapters_to_update_descendants:
        await _update_descendant_levels(session, chapter, all_chapters_map)

    await session.commit()


__all__ = [
    "MAX_LEVEL",
    "get_chapters_tree",
    "get_chapter_by_id",
    "get_chapter_with_navigation",
    "create_chapter",
    "update_chapter",
    "delete_chapter",
    "reorder_chapters",
]

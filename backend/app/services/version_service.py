"""
章节版本服务模块

提供版本保存、历史查询、差异对比和版本恢复功能。
"""

import difflib
from typing import List

from sqlalchemy import desc, func, select, tuple_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from app.core.exceptions import AppException
from app.models.chapter import Chapter
from app.models.chapter_version import ChapterVersion
from app.schemas.version import (
    VersionDiffLine,
    VersionDiffResponse,
    VersionListResponse,
    VersionResponse,
)


async def save_version(
    session: AsyncSession,
    chapter_id: int,
    content: str | None,
    user_id: int | None = None,
) -> ChapterVersion:
    """保存章节版本（带并发重试）

    创建新的版本记录，版本号自动递增。并发场景下通过唯一约束检测冲突并自动重试。

    Args:
        session: 数据库会话
        chapter_id: 章节 ID
        content: 章节内容
        user_id: 创建者 ID（可选）

    Returns:
        创建的版本对象

    Raises:
        AppException: 章节不存在时抛出 404 错误
        AppException: 并发冲突重试次数耗尽时抛出 409 错误
    """
    max_retries = 3

    for attempt in range(max_retries):
        result = await session.execute(
            select(
                Chapter.id,
                func.coalesce(func.max(ChapterVersion.version_num), 0).label("max_version"),
            )
            .outerjoin(
                ChapterVersion,
                (ChapterVersion.chapter_id == Chapter.id),
            )
            .where(Chapter.id == chapter_id)
            .group_by(Chapter.id)
        )
        row = result.first()

        if not row:
            raise AppException(code=404, message="章节不存在", data=None)

        max_version = row.max_version

        new_version = ChapterVersion(
            chapter_id=chapter_id,
            content=content,
            version_num=max_version + 1,
            created_by=user_id,
        )

        session.add(new_version)

        try:
            await session.flush()
            await session.refresh(new_version)
            return new_version
        except IntegrityError:
            await session.rollback()
            if attempt == max_retries - 1:
                raise AppException(
                    code=409,
                    message="版本保存冲突，请稍后重试",
                    data=None,
                )

    raise AppException(code=500, message="版本保存失败", data=None)


async def get_version_history(
    session: AsyncSession,
    chapter_id: int,
    page: int = 1,
    page_size: int = 20,
) -> VersionListResponse:
    """获取章节版本历史

    分页获取指定章节的所有历史版本，按版本号降序排列。

    Args:
        session: 数据库会话
        chapter_id: 章节 ID
        page: 页码（从 1 开始）
        page_size: 每页数量

    Returns:
        版本列表响应对象

    Raises:
        AppException: 章节不存在时抛出 404 错误
    """
    # 检查章节是否存在
    chapter_result = await session.execute(
        select(Chapter).where(Chapter.id == chapter_id)
    )
    chapter = chapter_result.scalar_one_or_none()

    if not chapter:
        raise AppException(code=404, message="章节不存在", data=None)

    # 获取总数
    count_result = await session.execute(
        select(func.count())
        .select_from(ChapterVersion)
        .where(ChapterVersion.chapter_id == chapter_id)
    )
    total = count_result.scalar() or 0

    # 分页查询
    offset = (page - 1) * page_size
    versions_result = await session.execute(
        select(ChapterVersion)
        .where(ChapterVersion.chapter_id == chapter_id)
        .order_by(desc(ChapterVersion.version_num))
        .offset(offset)
        .limit(page_size)
    )
    versions = list(versions_result.scalars().all())

    return VersionListResponse(
        chapter_id=chapter_id,
        total=total,
        versions=[VersionResponse.model_validate(v) for v in versions],
    )


async def get_version_by_id(
    session: AsyncSession,
    version_id: int,
) -> ChapterVersion:
    """根据 ID 获取版本

    Args:
        session: 数据库会话
        version_id: 版本 ID

    Returns:
        版本对象

    Raises:
        AppException: 版本不存在时抛出 404 错误
    """
    result = await session.execute(
        select(ChapterVersion).where(ChapterVersion.id == version_id)
    )
    version = result.scalar_one_or_none()

    if not version:
        raise AppException(code=404, message="版本不存在", data=None)

    return version


async def compare_versions(
    session: AsyncSession,
    old_version_id: int,
    new_version_id: int,
) -> VersionDiffResponse:
    """对比两个版本的内容差异

    使用 difflib 进行逐行对比，返回差异详情。

    Args:
        session: 数据库会话
        old_version_id: 旧版本 ID
        new_version_id: 新版本 ID

    Returns:
        版本差异对比响应对象

    Raises:
        AppException: 版本不存在时抛出 404 错误
        AppException: 版本不属于同一章节时抛出 400 错误
    """
    # 单次查询获取两个版本
    result = await session.execute(
        select(ChapterVersion).where(
            ChapterVersion.id.in_([old_version_id, new_version_id])
        )
    )
    versions = {v.id: v for v in result.scalars().all()}

    if old_version_id not in versions:
        raise AppException(code=404, message="旧版本不存在", data=None)
    if new_version_id not in versions:
        raise AppException(code=404, message="新版本不存在", data=None)

    old_version = versions[old_version_id]
    new_version = versions[new_version_id]

    # 检查是否属于同一章节
    if old_version.chapter_id != new_version.chapter_id:
        raise AppException(
            code=400,
            message="两个版本不属于同一章节",
            data=None,
        )

    # 获取内容行
    old_lines = (old_version.content or "").splitlines(keepends=True)
    new_lines = (new_version.content or "").splitlines(keepends=True)

    # 使用 difflib 进行对比
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

    diff_lines: List[VersionDiffLine] = []
    old_line_num = 0
    new_line_num = 0
    added_count = 0
    removed_count = 0
    changed_count = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for i in range(i1, i2):
                old_line_num += 1
                new_line_num += 1
                diff_lines.append(
                    VersionDiffLine(
                        type="unchanged",
                        content=old_lines[i].rstrip("\n\r"),
                        old_line_num=old_line_num,
                        new_line_num=new_line_num,
                    )
                )
        elif tag == "replace":
            for i in range(i1, i2):
                old_line_num += 1
                diff_lines.append(
                    VersionDiffLine(
                        type="removed",
                        content=old_lines[i].rstrip("\n\r"),
                        old_line_num=old_line_num,
                        new_line_num=None,
                    )
                )
                removed_count += 1
            for j in range(j1, j2):
                new_line_num += 1
                diff_lines.append(
                    VersionDiffLine(
                        type="added",
                        content=new_lines[j].rstrip("\n\r"),
                        old_line_num=None,
                        new_line_num=new_line_num,
                    )
                )
                added_count += 1
            changed_count += 1
        elif tag == "delete":
            for i in range(i1, i2):
                old_line_num += 1
                diff_lines.append(
                    VersionDiffLine(
                        type="removed",
                        content=old_lines[i].rstrip("\n\r"),
                        old_line_num=old_line_num,
                        new_line_num=None,
                    )
                )
                removed_count += 1
        elif tag == "insert":
            for j in range(j1, j2):
                new_line_num += 1
                diff_lines.append(
                    VersionDiffLine(
                        type="added",
                        content=new_lines[j].rstrip("\n\r"),
                        old_line_num=None,
                        new_line_num=new_line_num,
                    )
                )
                added_count += 1

    return VersionDiffResponse(
        from_version=VersionResponse.model_validate(old_version),
        to_version=VersionResponse.model_validate(new_version),
        diff=diff_lines,
        summary={
            "added": added_count,
            "removed": removed_count,
            "changed": changed_count,
        },
    )


async def restore_version(
    session: AsyncSession,
    chapter_id: int,
    version_id: int,
    user_id: int | None = None,
) -> Chapter:
    """恢复章节到指定版本

    将章节内容恢复到历史版本，并创建新版本记录。

    Args:
        session: 数据库会话
        chapter_id: 章节 ID
        version_id: 目标版本 ID
        user_id: 操作者 ID（可选）

    Returns:
        更新后的章节对象

    Raises:
        AppException: 章节不存在时抛出 404 错误
        AppException: 版本不存在时抛出 404 错误
        AppException: 版本不属于该章节时抛出 400 错误
    """
    # 合并查询：同时获取章节和版本
    chapter_result = await session.execute(
        select(Chapter).where(Chapter.id == chapter_id)
    )
    chapter = chapter_result.scalar_one_or_none()

    if not chapter:
        raise AppException(code=404, message="章节不存在", data=None)

    version_result = await session.execute(
        select(ChapterVersion).where(ChapterVersion.id == version_id)
    )
    version = version_result.scalar_one_or_none()

    if not version:
        raise AppException(code=404, message="版本不存在", data=None)

    # 检查版本是否属于该章节
    if version.chapter_id != chapter_id:
        raise AppException(
            code=400,
            message="版本不属于该章节",
            data=None,
        )

    # 获取当前最大版本号（内联逻辑，避免重复查询章节）
    max_version_result = await session.execute(
        select(func.max(ChapterVersion.version_num)).where(
            ChapterVersion.chapter_id == chapter_id
        )
    )
    max_version = max_version_result.scalar() or 0

    current_version = ChapterVersion(
        chapter_id=chapter_id,
        content=chapter.content,
        version_num=max_version + 1,
        created_by=user_id,
    )
    session.add(current_version)

    # 恢复内容
    chapter.content = version.content
    await session.commit()
    await session.refresh(chapter)

    return chapter


__all__ = [
    "save_version",
    "get_version_history",
    "get_version_by_id",
    "compare_versions",
    "restore_version",
]

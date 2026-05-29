"""章节管理 API 端点

提供章节 CRUD、排序、导航等接口。
"""

from fastapi import APIRouter, Query, Request
from sqlalchemy import select

from app.api.deps import CurrentUser, OptionalCurrentUser, SessionDep
from app.core.exceptions import AppException
from app.core.limiter import limiter
from app.models.textbook import Textbook, TextbookStatus
from app.models.chapter import Chapter
from app.schemas.chapter import (
    ChapterCreate,
    ChapterReorderRequest,
    ChapterResponse,
    ChapterUpdate,
    SortApplyRequest,
    SortPreviewRequest,
    SortUndoRequest,
)
from app.schemas.version import VersionResponse
from app.services import chapter_service
from app.services import chapter_sort_service
from app.services import textbook_service
from app.services import version_service
from app.services.permission_service import check_textbook_permission

router = APIRouter(prefix="/chapters", tags=["章节管理"])


@router.get("/textbook/{textbook_id}", response_model=dict)
@limiter.limit("30/minute")
async def get_chapters_tree(
    request: Request,
    textbook_id: int,
    session: SessionDep,
    current_user: OptionalCurrentUser,
) -> dict:
    # 安全检查：游客只能访问已发布教材的章节
    if current_user is None:
        result = await session.execute(
            select(Textbook).where(Textbook.id == textbook_id)
        )
        textbook = result.scalar_one_or_none()
        if textbook is None or textbook.status != TextbookStatus.PUBLISHED:
            raise AppException(code=404, message="教材不存在或无权访问", data=None)

    result = await chapter_service.get_chapters_tree(session, textbook_id)
    return {
        "code": 200,
        "message": "success",
        "data": result.model_dump(),
    }


@router.put("/reorder", response_model=dict)
async def reorder_chapters(
    reorder_in: ChapterReorderRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    await chapter_service.reorder_chapters(session, current_user, reorder_in)
    return {"code": 200, "message": "排序更新成功", "data": None}


@router.post("/sort/preview", response_model=dict)
async def preview_sort(
    preview_in: SortPreviewRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """预览章节排序结果

    Args:
        preview_in: 排序预览请求（包含教材 ID 和选中的章节 ID）
        session: 数据库会话
        current_user: 当前用户

    Returns:
        排序预览结果（包含预览树、变更数量、新建文件夹列表）
    """
    await check_textbook_permission(
        session, current_user, preview_in.textbook_id, "edit"
    )
    result = await chapter_sort_service.preview_sort(
        preview_in.textbook_id, preview_in.selected_ids, session
    )
    return {"code": 200, "message": "success", "data": result}


@router.post("/sort/apply", response_model=dict)
async def apply_sort(
    apply_in: SortApplyRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """应用章节排序并保存快照

    Args:
        apply_in: 排序应用请求（包含教材 ID、选中的章节 ID 和可选的排序结果）
        session: 数据库会话
        current_user: 当前用户

    Returns:
        排序应用结果（包含成功标志、变更数量、新建文件夹列表）
    """
    await check_textbook_permission(session, current_user, apply_in.textbook_id, "edit")
    result = await chapter_sort_service.apply_sort(
        apply_in.textbook_id,
        apply_in.selected_ids,
        apply_in.orders,
        session,
        current_user,
        deleted_ids=apply_in.deleted_ids if apply_in.deleted_ids else None,
        deleted_folder_numbers=apply_in.deleted_folder_numbers
        if apply_in.deleted_folder_numbers
        else None,
    )
    return {"code": 200, "message": "排序应用成功", "data": result}


@router.post("/sort/undo", response_model=dict)
async def undo_sort(
    undo_in: SortUndoRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """撤回最近一次章节排序

    Args:
        undo_in: 排序撤回请求（包含教材 ID）
        session: 数据库会话
        current_user: 当前用户

    Returns:
        撤回结果
    """
    await check_textbook_permission(session, current_user, undo_in.textbook_id, "edit")
    await chapter_sort_service.undo_sort(undo_in.textbook_id, session)
    return {"code": 200, "message": "排序撤回成功", "data": None}


@router.get("/{chapter_id}", response_model=dict)
@limiter.limit("60/minute")
async def get_chapter(
    request: Request,
    chapter_id: int,
    session: SessionDep,
    current_user: OptionalCurrentUser,
) -> dict:
    # 获取章节以确定所属教材
    chapter_query = await session.execute(
        select(Chapter).where(Chapter.id == chapter_id)
    )
    chapter = chapter_query.scalar_one_or_none()
    if chapter is None:
        raise AppException(code=404, message="章节不存在", data=None)

    # 检查教材状态：草稿教材需要编辑权限
    textbook_result = await session.execute(
        select(Textbook).where(Textbook.id == chapter.textbook_id)
    )
    textbook = textbook_result.scalar_one_or_none()
    if textbook is None:
        raise AppException(code=404, message="教材不存在", data=None)

    if textbook.status == TextbookStatus.DRAFT:
        if current_user is None:
            raise AppException(code=404, message="教材不存在或无权访问", data=None)
        await check_textbook_permission(session, current_user, chapter.textbook_id, "edit")

    result = await chapter_service.get_chapter_with_navigation(session, chapter_id)
    return {
        "code": 200,
        "message": "success",
        "data": result.model_dump(),
    }


@router.post("", response_model=dict)
async def create_chapter(
    chapter_in: ChapterCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    chapter = await chapter_service.create_chapter(session, current_user, chapter_in)
    return {
        "code": 200,
        "message": "创建成功",
        "data": ChapterResponse.model_validate(chapter).model_dump(),
    }


@router.put("/{chapter_id}", response_model=dict)
async def update_chapter(
    chapter_id: int,
    chapter_in: ChapterUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    chapter = await chapter_service.update_chapter(
        session, current_user, chapter_id, chapter_in
    )
    return {
        "code": 200,
        "message": "更新成功",
        "data": ChapterResponse.model_validate(chapter).model_dump(),
    }


@router.delete("/{chapter_id}", response_model=dict)
async def delete_chapter(
    chapter_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    await chapter_service.delete_chapter(session, current_user, chapter_id)
    return {"code": 200, "message": "删除成功", "data": None}


# ==================== 版本管理端点 ====================


@router.get("/{chapter_id}/versions", response_model=dict)
async def get_version_history(
    chapter_id: int,
    session: SessionDep,
    current_user: CurrentUser,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> dict:
    """获取章节版本历史

    Args:
        chapter_id: 章节 ID
        session: 数据库会话
        current_user: 当前用户
        page: 页码（从 1 开始）
        page_size: 每页数量

    Returns:
        版本列表响应
    """
    result = await version_service.get_version_history(
        session, chapter_id, page, page_size
    )
    return {
        "code": 200,
        "message": "success",
        "data": result.model_dump(),
    }


@router.get("/{chapter_id}/versions/compare", response_model=dict)
async def compare_chapter_versions(
    chapter_id: int,
    session: SessionDep,
    current_user: CurrentUser,
    from_version_id: int = Query(..., description="起始版本 ID"),
    to_version_id: int = Query(..., description="目标版本 ID"),
) -> dict:
    """对比两个版本的内容差异"""
    result = await version_service.compare_versions(
        session, from_version_id, to_version_id
    )
    return {
        "code": 200,
        "message": "success",
        "data": result.model_dump(),
    }


@router.get("/{chapter_id}/versions/{version_id}", response_model=dict)
async def get_version_detail(
    chapter_id: int,
    version_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """获取版本详情

    Args:
        chapter_id: 章节 ID
        version_id: 版本 ID
        session: 数据库会话
        current_user: 当前用户

    Returns:
        版本详情响应
    """
    version = await version_service.get_version_by_id(session, version_id)

    # 检查版本是否属于该章节
    if version.chapter_id != chapter_id:
        return {
            "code": 400,
            "message": "版本不属于该章节",
            "data": None,
        }

    return {
        "code": 200,
        "message": "success",
        "data": VersionResponse.model_validate(version).model_dump(),
    }


@router.post("/{chapter_id}/versions/{version_id}/restore", response_model=dict)
async def restore_version(
    chapter_id: int,
    version_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """恢复章节到指定版本

    Args:
        chapter_id: 章节 ID
        version_id: 目标版本 ID
        session: 数据库会话
        current_user: 当前用户

    Returns:
        恢复结果响应
    """
    # 检查编辑权限
    chapter = await chapter_service.get_chapter_by_id(session, chapter_id)
    await check_textbook_permission(session, current_user, chapter.textbook_id, "edit")

    # 恢复版本
    updated_chapter = await version_service.restore_version(
        session, chapter_id, version_id, current_user.id
    )

    return {
        "code": 200,
        "message": "版本恢复成功",
        "data": ChapterResponse.model_validate(updated_chapter).model_dump(),
    }


@router.post("/{chapter_id}/versions/save", response_model=dict)
async def save_chapter_version(
    chapter_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """手动保存章节版本

    Args:
        chapter_id: 章节 ID
        session: 数据库会话
        current_user: 当前用户

    Returns:
        版本保存结果响应
    """
    chapter = await chapter_service.get_chapter_by_id(session, chapter_id)

    await check_textbook_permission(session, current_user, chapter.textbook_id, "edit")

    version = await version_service.save_version(
        session, chapter_id, chapter.content, current_user.id
    )

    return {
        "code": 200,
        "message": "版本保存成功",
        "data": VersionResponse.model_validate(version).model_dump(),
    }

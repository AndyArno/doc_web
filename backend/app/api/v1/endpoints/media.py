"""媒体资源 API 端点

提供媒体 CRUD、回收站等接口。
"""

from fastapi import APIRouter, Query

from app.api.deps import AdminUser, CurrentUser, SessionDep
from app.schemas.media import MediaResponse
from app.services import media_service

router = APIRouter(prefix="/media", tags=["媒体资源"])


@router.get("", response_model=dict)
async def get_media_list(
    session: SessionDep,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    textbook_id: int | None = None,
    chapter_id: int | None = None,
    file_type: str | None = None,
) -> dict:
    """获取媒体列表（分页）

    只返回未删除的媒体。

    Returns:
        媒体分页列表
    """
    result = await media_service.get_media_list_paginated(
        session=session,
        page=page,
        page_size=page_size,
        textbook_id=textbook_id,
        chapter_id=chapter_id,
        file_type=file_type,
    )
    return {
        "code": 200,
        "message": "success",
        "data": result.model_dump(),
    }


@router.get("/trash", response_model=dict)
async def get_trash_list(
    session: SessionDep,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """获取回收站媒体列表

    只返回已删除的媒体。

    Returns:
        回收站列表
    """
    result = await media_service.get_trash_list(
        session=session,
        page=page,
        page_size=page_size,
    )
    return {
        "code": 200,
        "message": "success",
        "data": result.model_dump(),
    }


@router.get("/{media_id}", response_model=dict)
async def get_media(
    media_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """获取媒体详情

    Returns:
        媒体详情
    """
    media = await media_service.get_media_by_id(session, media_id)
    return {
        "code": 200,
        "message": "success",
        "data": MediaResponse.model_validate(media).model_dump(),
    }


@router.delete("/{media_id}", response_model=dict)
async def delete_media(
    media_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """软删除媒体（移入回收站）

    Returns:
        成功响应
    """
    await media_service.soft_delete_media(session, media_id, user=current_user)
    return {"code": 200, "message": "已移入回收站", "data": None}


@router.post("/{media_id}/restore", response_model=dict)
async def restore_media(
    media_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """从回收站恢复媒体

    Returns:
        成功响应
    """
    await media_service.restore_media(session, media_id, user=current_user)
    return {"code": 200, "message": "已恢复", "data": None}


@router.delete("/{media_id}/permanent", response_model=dict)
async def permanently_delete_media(
    media_id: int,
    session: SessionDep,
    current_user: AdminUser,
) -> dict:
    """永久删除媒体

    同时删除物理文件。

    Returns:
        成功响应
    """
    await media_service.permanently_delete_media(session, media_id)
    return {"code": 200, "message": "已永久删除", "data": None}


@router.delete("/trash/clear", response_model=dict)
async def clear_trash(
    session: SessionDep,
    current_user: AdminUser,
) -> dict:
    """清空回收站

    永久删除所有回收站中的媒体。

    Returns:
        删除数量
    """
    deleted_count = await media_service.clear_trash(session)
    return {
        "code": 200,
        "message": f"已清空回收站，共删除 {deleted_count} 个文件",
        "data": {"deleted_count": deleted_count},
    }

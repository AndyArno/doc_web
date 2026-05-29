"""教材管理 API 端点

提供教材 CRUD、发布管理等接口。
"""

from fastapi import APIRouter, Query, Request

from app.core.limiter import limiter
from app.api.deps import (
    AdminUser,
    CurrentUser,
    OptionalCurrentUser,
    SessionDep,
    SuperAdminUser,
)
from app.models.textbook import TextbookStatus
from app.schemas.textbook import (
    TextbookCreate,
    TextbookResponse,
    TextbookUpdate,
)
from app.services import textbook_service

router = APIRouter(prefix="/textbooks", tags=["教材管理"])


@router.get("", response_model=dict)
@limiter.limit("30/minute")
async def get_textbooks(
    request: Request,
    session: SessionDep,
    current_user: OptionalCurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    status: TextbookStatus | None = None,
    for_management: bool = Query(False),
) -> dict:
    """获取教材列表（分页）

    支持按关键词、状态筛选。

    Args:
        for_management: 是否为管理模式。True 时按权限过滤，False 时返回所有已发布教材。

    Returns:
        教材分页列表
    """
    result = await textbook_service.get_textbooks_paginated(
        session=session,
        page=page,
        page_size=page_size,
        keyword=keyword,
        status=status,
        user=current_user,
        for_management=for_management,
    )
    return {
        "code": 200,
        "message": "success",
        "data": result.model_dump(),
    }


@router.get("/{textbook_id}", response_model=dict)
@limiter.limit("30/minute")
async def get_textbook(
    request: Request,
    textbook_id: int,
    session: SessionDep,
    current_user: OptionalCurrentUser,
) -> dict:
    """获取教材详情

    游客只能访问已发布的教材。

    Returns:
        教材详情（含章节树）
    """
    from app.core.exceptions import AppException

    data = await textbook_service.get_textbook_with_chapters(session, textbook_id)

    # 游客只能访问已发布教材
    if current_user is None:
        if data.get("status") != TextbookStatus.PUBLISHED:
            raise AppException(code=404, message="教材不存在或无权访问", data=None)

    return {
        "code": 200,
        "message": "success",
        "data": data,
    }


@router.post("", response_model=dict)
async def create_textbook(
    textbook_in: TextbookCreate,
    session: SessionDep,
    current_user: SuperAdminUser,
) -> dict:
    """创建教材（仅超级管理员）

    Returns:
        新创建的教材信息
    """
    textbook = await textbook_service.create_textbook(session, textbook_in)
    return {
        "code": 200,
        "message": "创建成功",
        "data": TextbookResponse.model_validate(textbook).model_dump(),
    }


@router.put("/{textbook_id}", response_model=dict)
async def update_textbook(
    textbook_id: int,
    textbook_in: TextbookUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """更新教材

    Returns:
        更新后的教材信息
    """
    textbook = await textbook_service.update_textbook(
        session, textbook_id, textbook_in, user_id=current_user.id
    )
    return {
        "code": 200,
        "message": "更新成功",
        "data": TextbookResponse.model_validate(textbook).model_dump(),
    }


@router.delete("/{textbook_id}", response_model=dict)
async def delete_textbook(
    textbook_id: int,
    session: SessionDep,
    current_user: SuperAdminUser,
) -> dict:
    """删除教材（仅超级管理员）

    删除前清理关联的 media 文件（磁盘文件和数据库记录）。

    Returns:
        成功响应
    """
    await textbook_service.delete_textbook(session, textbook_id)
    return {"code": 200, "message": "删除成功", "data": None}


@router.put("/{textbook_id}/publish", response_model=dict)
async def publish_textbook(
    textbook_id: int,
    session: SessionDep,
    current_user: AdminUser,
) -> dict:
    """发布教材（管理员及以上）

    Returns:
        更新后的教材信息
    """
    textbook = await textbook_service.publish_textbook(session, textbook_id)
    return {
        "code": 200,
        "message": "发布成功",
        "data": TextbookResponse.model_validate(textbook).model_dump(),
    }


@router.put("/{textbook_id}/unpublish", response_model=dict)
async def unpublish_textbook(
    textbook_id: int,
    session: SessionDep,
    current_user: AdminUser,
) -> dict:
    """取消发布教材（管理员及以上）

    Returns:
        更新后的教材信息
    """
    textbook = await textbook_service.unpublish_textbook(session, textbook_id)
    return {
        "code": 200,
        "message": "已取消发布",
        "data": TextbookResponse.model_validate(textbook).model_dump(),
    }

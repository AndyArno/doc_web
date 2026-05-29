"""搜索 API 端点

提供全文搜索接口。
"""

import math

from fastapi import APIRouter, Query, Request

from sqlalchemy import select

from app.api.deps import CurrentUser, OptionalCurrentUser, SessionDep
from app.core.exceptions import AppException
from app.core.limiter import limiter
from app.models.textbook import Textbook, TextbookStatus
from app.schemas.search import SearchResultItem, SearchResponseData
from app.services import permission_service, search_service

router = APIRouter(prefix="/search", tags=["搜索"])


@router.get("", response_model=dict)
@limiter.limit("20/minute")
async def search(
    request: Request,
    session: SessionDep,
    current_user: OptionalCurrentUser,
    q: str = Query(..., min_length=1, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    textbook_id: int | None = Query(None, description="限定教材ID"),
) -> dict:
    """搜索章节内容

    游客只能搜索已发布教材的内容。

    Returns:
        搜索结果分页数据
    """
    if textbook_id is not None:
        result = await session.execute(
            select(Textbook).where(Textbook.id == textbook_id)
        )
        textbook = result.scalar_one_or_none()
        if textbook is None:
            raise AppException(code=404, message="教材不存在", data=None)
        if textbook.status != TextbookStatus.PUBLISHED:
            # 游客访问未发布教材返回 404
            if current_user is None:
                raise AppException(code=404, message="教材不存在", data=None)
            # 已登录用户检查权限
            await permission_service.check_textbook_permission(
                session=session,
                user=current_user,
                textbook_id=textbook_id,
                permission_type="edit",
            )

    offset = (page - 1) * page_size

    result = await search_service.search_chapters(
        session=session,
        query=q,
        textbook_id=textbook_id,
        limit=page_size,
        offset=offset,
    )

    total_pages = math.ceil(result.total / page_size) if result.total > 0 else 1

    results = [
        SearchResultItem(
            doc_id=r.doc_id,
            doc_type=r.doc_type,
            title=r.title,
            textbook_id=r.textbook_id,
            textbook_title=r.textbook_title,
            rank=r.rank,
        )
        for r in result.results
    ]

    return {
        "code": 200,
        "message": "success",
        "data": SearchResponseData(
            query=result.query,
            results=results,
            total=result.total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ).model_dump(),
    }

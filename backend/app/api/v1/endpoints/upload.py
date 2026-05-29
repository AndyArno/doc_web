"""文件上传 API 端点

提供图片上传、Markdown ZIP 上传等接口。
"""

import asyncio
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from sqlalchemy import select

from app.api.deps import CurrentUser, SessionDep
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.services import upload_service
from app.utils.task_manager import task_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["文件上传"])


async def _process_upload_background(
    task_id: str, file_path: str, filename: str, title: str,
    auto_publish: bool, textbook_id: int | None, user_id: int,
) -> None:
    """后台处理 Markdown ZIP 上传任务。

    从临时文件读取内容，使用独立数据库会话执行上传，
    通过 progress_callback 将进度更新推送到 task_manager。

    Args:
        task_id: 任务 ID
        file_path: 临时文件路径（处理完成后自动删除）
        filename: 原始文件名
        title: 教材标题
        auto_publish: 是否自动发布
        textbook_id: 可选的现有教材 ID
        user_id: 操作用户 ID
    """
    try:
        content = Path(file_path).read_bytes()
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one()

            def on_progress(stage: str, pct: int):
                asyncio.ensure_future(
                    task_manager.update(task_id, stage=stage, progress=pct)
                )

            result_data = await upload_service.upload_markdown_zip(
                session=session, user=user, file_content=content,
                filename=filename, title=title, auto_publish=auto_publish,
                textbook_id=textbook_id, progress_callback=on_progress,
            )
            await task_manager.update(
                task_id, status="done", stage="done", progress=100, result=result_data,
            )
    except Exception as e:
        logger.exception(f"Upload task {task_id} failed: {e}")
        try:
            await task_manager.update(task_id, status="failed", error=str(e))
        except Exception:
            pass
    finally:
        Path(file_path).unlink(missing_ok=True)


@router.post("/image", response_model=dict)
async def upload_image(
    file: UploadFile = File(...),
    textbook_id: int = Form(...),
    chapter_id: int | None = Form(None),
    session: SessionDep = None,
    current_user: CurrentUser = None,
) -> dict:
    """上传图片

    Returns:
        上传响应
    """
    content = await file.read()
    result = await upload_service.upload_image(
        session=session,
        user=current_user,
        file_content=content,
        filename=file.filename or "image.jpg",
        content_type=file.content_type,
        textbook_id=textbook_id,
        chapter_id=chapter_id,
    )
    return {
        "code": 200,
        "message": "上传成功",
        "data": result.model_dump(),
    }


@router.post("/markdown", response_model=dict)
async def upload_markdown(
    file: UploadFile = File(...),
    title: str = Form(...),
    auto_publish: bool = Form(False),
    textbook_id: int | None = Form(None),
    session: SessionDep = None,
    current_user: CurrentUser = None,
) -> dict:
    """上传 Markdown ZIP（异步后台处理）

    文件保存到临时位置后立即返回 task_id，
    实际处理在后台异步执行，通过 GET /upload/status/{task_id} 查询进度。

    Returns:
        包含 task_id 的响应
    """
    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".upload") as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    task_id = await task_manager.create()
    asyncio.create_task(_process_upload_background(
        task_id=task_id, file_path=tmp_path,
        filename=file.filename or "upload.zip",
        title=title, auto_publish=auto_publish,
        textbook_id=textbook_id, user_id=current_user.id,
    ))
    return {
        "code": 200,
        "message": "任务已创建",
        "data": {"task_id": task_id},
    }


@router.post("/markdown-single", response_model=dict)
async def upload_single_markdown_file(
    file: UploadFile = File(...),
    textbook_id: int = Form(...),
    parent_id: int | None = Form(None),
    session: SessionDep = None,
    current_user: CurrentUser = None,
) -> dict:
    content = await file.read()
    result = await upload_service.upload_single_markdown(
        session=session,
        file_content=content,
        filename=file.filename or "chapter.md",
        textbook_id=textbook_id,
        parent_id=parent_id,
        current_user=current_user,
    )
    return {
        "code": 200,
        "message": "上传成功",
        "data": result,
    }


@router.get("/status/{task_id}", response_model=dict)
async def get_upload_status(task_id: str) -> dict:
    """获取上传任务状态"""
    from app.utils.task_manager import task_manager

    status = await task_manager.get(task_id)
    if status is None:
        return {"code": 404, "message": "任务不存在或已过期", "data": None}
    return {
        "code": 200,
        "message": "success",
        "data": {
            "task_id": status.task_id,
            "status": status.status,
            "stage": status.stage,
            "progress": status.progress,
            "result": status.result,
            "error": status.error,
        },
    }

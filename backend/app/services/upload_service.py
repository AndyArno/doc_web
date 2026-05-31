"""文件上传服务模块

提供图片上传、Markdown 压缩包上传等业务逻辑。
支持 ZIP、TAR、TAR.GZ、TAR.BZ2、TAR.XZ、7z、RAR 格式。
"""

import logging
import os
import io
import mimetypes
import shutil
import tempfile
import urllib.parse
import uuid
from pathlib import Path
from typing import Callable, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.chapter import Chapter, NodeType, generate_slug
from app.models.media import Media
from app.models.textbook import Textbook, TextbookStatus
from app.models.user import Role, User
from app.schemas.chapter import ChapterCreate
from app.schemas.media import UploadResponse
from app.services import chapter_service
from app.services import chapter_sort_service
from app.services import version_service
from app.services.permission_service import check_textbook_permission
from app.utils.archive_extractor import ArchiveExtractor
from app.utils.image_processor import ImageProcessor
from app.utils.chapter_sort import parse_folder_number


# === 常量定义 ===

MAX_IMAGE_SIZE = 100 * 1024 * 1024
MAX_ZIP_SIZE = 100 * 1024 * 1024

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
(UPLOAD_DIR / "images").mkdir(exist_ok=True)

# 文件类型白名单
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ARCHIVE_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}

logger = logging.getLogger(__name__)


class UploadZipResult(dict):
    def __getattr__(self, key: str):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc


# === 辅助函数 ===


def get_file_extension(filename: str) -> str:
    """获取文件扩展名，清理路径遍历字符。

    用于防止路径遍历攻击，返回清理后的文件扩展名。

    Args:
        filename: 文件名（可能包含路径）

    Returns:
        清理后的扩展名（小写），无效时返回空字符串

    Examples:
        >>> get_file_extension("image.jpg")
        'jpg'
        >>> get_file_extension("../../etc/passwd")
        ''
        >>> get_file_extension("file.TXT")
        'txt'
    """
    # 先提取基本文件名，防止路径遍历攻击
    basename = os.path.basename(filename)
    # 获取扩展名
    ext = basename.rsplit(".", 1)[-1].lower() if "." in basename else ""
    # 清理扩展名中的路径字符（双重防护）
    ext = ext.replace("/", "").replace("\\", "").replace("..", "")
    return ext


# === 上传服务函数 ===


async def upload_image(
    session: AsyncSession,
    user: User,
    file_content: bytes,
    filename: str,
    content_type: Optional[str],
    textbook_id: int,
    chapter_id: Optional[int] = None,
) -> UploadResponse:
    """上传图片

    验证文件类型和大小，保存文件到磁盘，创建 Media 记录。
    如果存在同名文件，返回警告信息。

    Args:
        session: 数据库会话
        user: 当前用户
        file_content: 文件内容（字节）
        filename: 原始文件名
        content_type: MIME 类型
        textbook_id: 教材 ID
        chapter_id: 可选的章节 ID

    Returns:
        上传响应对象（可能包含 warning 字段）

    Raises:
        AppException: 文件类型不支持、文件过大、无权限等错误
    """
    # 验证文件扩展名
    ext = get_file_extension(filename or "")
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise AppException(code=400, message="不支持的文件类型", data=None)

    # 验证 content-type
    if not content_type or content_type not in ALLOWED_CONTENT_TYPES:
        raise AppException(code=400, message="只支持图片文件", data=None)

    # 检查教材编辑权限
    await check_textbook_permission(session, user, textbook_id, "edit")

    # 检查文件大小
    if len(file_content) > MAX_IMAGE_SIZE:
        raise AppException(code=400, message="图片大小不能超过 100MB", data=None)

    warning: Optional[str] = None
    existing_result = await session.execute(
        select(Media).where(
            Media.original_name == (filename or "image.jpg"),
            Media.textbook_id == textbook_id,
            Media.is_deleted == False,
        )
    )
    if existing_result.scalar_one_or_none():
        warning = "same_name_exists"

    # 生成唯一文件名
    ext = get_file_extension(filename or "image.jpg")
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = UPLOAD_DIR / "images" / unique_filename

    # 保存文件到磁盘
    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
    except OSError as e:
        raise AppException(code=500, message=f"文件写入失败: {e}", data=None)

    # 创建 Media 记录
    media = Media(
        textbook_id=textbook_id,
        chapter_id=chapter_id,
        filename=unique_filename,
        original_name=filename or unique_filename,
        file_path=str(file_path),
        file_size=len(file_content),
        file_type=content_type,
    )

    session.add(media)
    await session.commit()
    await session.refresh(media)

    return UploadResponse(
        id=media.id,
        filename=media.filename,
        original_name=media.original_name,
        file_path=media.file_path,
        file_size=media.file_size,
        file_type=media.file_type,
        url=f"/uploads/images/{unique_filename}",
        warning=warning,
    )


async def upload_markdown_zip(
    session: AsyncSession,
    user: User,
    file_content: bytes,
    filename: str,
    title: str,
    auto_publish: bool = False,
    textbook_id: Optional[int] = None,
    progress_callback: Callable[[str, int], None] | None = None,
) -> dict:
    """上传 Markdown ZIP

    V2 阶段：执行 ZIP 安全校验，递归解析目录并创建章节/媒体记录。

    Args:
        session: 数据库会话
        user: 当前用户
        file_content: 文件内容（字节）
        filename: 原始文件名
        title: 教材标题（创建新教材时使用）
        auto_publish: 是否自动发布
        textbook_id: 可选的现有教材 ID

    Returns:
        Markdown 上传响应对象

    Raises:
        AppException: 文件格式错误、文件过大、无权限等错误
    """
    # 验证文件名非空
    if not filename:
        raise AppException(code=400, message="文件名不能为空", data=None)

    # 检查文件大小
    if len(file_content) > MAX_ZIP_SIZE:
        raise AppException(code=400, message="文件大小不能超过 100MB", data=None)

    # 使用 ArchiveExtractor 检测格式
    extractor: ArchiveExtractor | None = None
    try:
        extractor = ArchiveExtractor(io.BytesIO(file_content), filename)
        extractor.detect_format()
    except (ValueError, FileNotFoundError):
        raise AppException(
            code=400,
            message="不支持的压缩格式。支持: ZIP, TAR, TAR.GZ, TAR.BZ2, TAR.XZ, 7z, RAR",
            data=None,
        )

    if progress_callback:
        progress_callback("extracting", 10)

    chapters_count = 0
    warnings: list[str] = []
    textbook: Textbook
    is_new_textbook = False

    if textbook_id:
        result = await session.execute(
            select(Textbook).where(Textbook.id == textbook_id)
        )
        textbook = result.scalar_one_or_none()

        if not textbook:
            extractor.cleanup()
            raise AppException(code=404, message="教材不存在", data=None)

    else:
        is_new_textbook = True
        if user.role != Role.SUPER_ADMIN:
            extractor.cleanup()
            raise AppException(
                code=403, message="只有超级管理员可以创建新教材", data=None
            )

        slug = generate_slug(title)
        if not slug:
            slug = f"textbook-{uuid.uuid4().hex[:8]}"

        counter = 1
        original_slug = slug
        while True:
            result = await session.execute(
                select(Textbook).where(Textbook.slug == slug)
            )
            if not result.scalar_one_or_none():
                break
            slug = f"{original_slug}-{counter}"
            counter += 1

        textbook = Textbook(
            title=title,
            slug=slug,
            description="",
            status=TextbookStatus.PUBLISHED if auto_publish else TextbookStatus.DRAFT,
        )

        session.add(textbook)
        await session.commit()
        await session.refresh(textbook)

    await check_textbook_permission(session, user, textbook.id, "create")

    temp_dir = tempfile.mkdtemp(prefix="markdown_archive_")
    media_records: list[Media] = []
    image_processor = ImageProcessor(
        storage_dir=str(UPLOAD_DIR / "images"),
        base_url="/uploads/images",
    )

    try:
        # 使用 ArchiveExtractor 解压
        extracted_files = extractor.extract(Path(temp_dir))
    except ValueError as e:
        # 路径遍历攻击或其他安全问题
        raise AppException(code=400, message=str(e), data=None)

    if progress_callback:
        progress_callback("extracting", 30)

    try:
        # 检查是否有 Markdown 文件
        md_files = [f for f in extracted_files if f.suffix.lower() == ".md"]
        if not md_files:
            raise AppException(
                code=400, message="压缩包中未找到 Markdown 文件", data=None
            )

        # ===== 两阶段处理：先收集所有图片，再处理 Markdown =====
        # 解决 BUG：当 Markdown 在根目录、图片在子目录时，路径无法替换

        # 数据结构：存储图片和 Markdown 文件信息
        # image_info: (file_path, depth, chapter_id, relative_path)
        collected_images: list[tuple[Path, int, Optional[int], str]] = []
        # md_info: (file_path, depth, chapter_id, relative_path)
        collected_mds: list[tuple[Path, int, Optional[int], str]] = []

        async def scan_directory(
            directory: Path,
            depth: int,
            parent_chapter_id: Optional[int],
        ) -> None:
            """第一阶段：扫描目录，创建文件夹章节，收集图片和 Markdown 文件。

            Args:
                directory: 当前扫描目录
                depth: 当前深度（1-3）
                parent_chapter_id: 父章节 ID
            """
            nonlocal chapters_count
            order_index = 1

            items = sorted(directory.iterdir(), key=lambda x: x.name)
            image_items = []
            md_items = []
            dir_items = []

            for item in items:
                if item.is_dir():
                    dir_items.append(item)
                elif item.suffix.lower() == ".md":
                    md_items.append(item)
                elif item.suffix.lstrip(".").lower() in ARCHIVE_IMAGE_EXTENSIONS:
                    image_items.append(item)

            # 收集图片文件信息
            for item in image_items:
                relative_path = str(item.relative_to(Path(temp_dir)))
                if depth > 3:
                    warnings.append(f"忽略超过3层图片: {relative_path}")
                    continue

                if not parent_chapter_id:
                    warnings.append(
                        f"根目录图片未关联章节，已按教材资源保存: {relative_path}"
                    )

                collected_images.append((item, depth, parent_chapter_id, relative_path))

            # 收集 Markdown 文件信息
            for item in md_items:
                relative_path = str(item.relative_to(Path(temp_dir)))
                if depth > 3:
                    warnings.append(f"忽略超过3层文件: {relative_path}")
                    continue

                collected_mds.append((item, depth, parent_chapter_id, relative_path))

            # 创建文件夹章节并递归扫描
            for item in dir_items:
                relative_path = str(item.relative_to(Path(temp_dir)))
                if depth > 3:
                    warnings.append(f"忽略超过3层目录: {relative_path}")
                    continue

                chapter = await chapter_service.create_chapter(
                    session=session,
                    user=user,
                    chapter_in=ChapterCreate(
                        textbook_id=textbook.id,
                        parent_id=parent_chapter_id,
                        title=item.name,
                        content="",
                        order_index=order_index,
                        node_type=NodeType.FOLDER,
                    ),
                )
                chapters_count += 1
                order_index += 1

                # 递归扫描子目录
                await scan_directory(item, depth + 1, chapter.id)

        async def process_markdown_files() -> None:
            """第三阶段：处理所有 Markdown 文件，替换图片路径。"""
            nonlocal chapters_count

            # 按 depth 和 parent_id 分组，计算 order_index
            order_counters: dict[tuple[int, Optional[int]], int] = {}

            for item, depth, chapter_id, relative_path in collected_mds:
                key = (depth, chapter_id)
                if key not in order_counters:
                    order_counters[key] = 1
                order_index = order_counters[key]
                order_counters[key] += 1

                try:
                    content = item.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    raise AppException(
                        code=400,
                        message=f"Markdown 文件编码不支持，请使用 UTF-8: {relative_path}",
                        data=None,
                    )

                # 此时所有图片的 Media 记录都已创建
                processed_content, _ = image_processor.process_with_media_records(
                    content=content,
                    md_file_path=relative_path,
                    media_records=media_records,
                )

                chapter = await chapter_service.create_chapter(
                    session=session,
                    user=user,
                    chapter_in=ChapterCreate(
                        textbook_id=textbook.id,
                        parent_id=chapter_id,
                        title=item.stem,
                        content=processed_content,
                        order_index=order_index,
                        node_type=NodeType.ARTICLE,
                    ),
                )
                # 为 ARTICLE 类型章节保存初始版本
                await version_service.save_version(
                    session=session,
                    chapter_id=chapter.id,
                    content=processed_content,
                    user_id=user.id,
                )
                chapters_count += 1

        # ===== 执行两阶段处理 =====

        # 智能包装文件夹判断：单顶层目录 + 无章节标识 → 跳过包装层
        scan_root = Path(temp_dir)
        SYSTEM_FILES = {"Thumbs.db", "desktop.ini", ".DS_Store"}
        try:
            root_items = list(Path(temp_dir).iterdir())
            root_dirs = [i for i in root_items if i.is_dir() and not i.name.startswith(".")]
            root_files = [
                i for i in root_items
                if i.is_file()
                and not i.name.startswith(".")
                and i.name not in SYSTEM_FILES
            ]
            if len(root_dirs) == 1 and len(root_files) == 0:
                folder_name = root_dirs[0].name
                if parse_folder_number(folder_name) is None:
                    scan_root = root_dirs[0]
                    warnings.append(
                        f"已跳过非章节包装文件夹: {folder_name}（其内容已作为根级章节导入）"
                    )
        except OSError:
            pass

        # 第一阶段：扫描目录，创建文件夹章节，收集文件
        await scan_directory(scan_root, 1, None)

        # 第二阶段：批量创建所有图片的 Media 记录
        for item, depth, chapter_id, relative_path in collected_images:
            media = await _create_media_record(
                session=session,
                textbook_id=textbook.id,
                chapter_id=chapter_id,
                source_file=item,
            )
            media_records.append(media)

        if progress_callback:
            progress_callback("importing", 60)

        # 第三阶段：处理所有 Markdown 文件
        await process_markdown_files()

        if progress_callback:
            progress_callback("importing", 80)

        await session.commit()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        if extractor:
            extractor.cleanup()

    sort_preview = None
    try:
        sort_preview = await chapter_sort_service.preview_sort(
            textbook_id=textbook.id,
            selected_ids=None,
            db=session,
        )
    except Exception as e:
        logger.warning(f"Failed to generate sort preview: {e}")

    if progress_callback:
        progress_callback("sorting", 95)

    return UploadZipResult(
        {
            "textbook_id": textbook.id,
            "title": textbook.title,
            "chapters_count": chapters_count,
            "warnings": warnings,
            "sort_preview": sort_preview,
            "task_id": None,
            "message": "上传成功",
        }
    )


async def _create_media_record(
    session: AsyncSession,
    textbook_id: int,
    chapter_id: Optional[int],
    source_file: Path,
) -> Media:
    """保存图片文件并创建 Media 记录。

    Args:
        session: 数据库会话
        textbook_id: 教材 ID
        chapter_id: 章节 ID（可选）
        source_file: 源文件路径

    Returns:
        创建的 Media 对象
    """
    ext = get_file_extension(source_file.name or "")
    unique_filename = f"{uuid.uuid4().hex}.{ext or 'bin'}"
    dest_path = UPLOAD_DIR / "images" / unique_filename
    shutil.copy2(source_file, dest_path)

    mime_type = mimetypes.guess_type(source_file.name)[0] or "application/octet-stream"
    media = Media(
        textbook_id=textbook_id,
        chapter_id=chapter_id,
        filename=unique_filename,
        original_name=source_file.name,
        file_path=str(dest_path),
        file_size=source_file.stat().st_size,
        file_type=mime_type,
    )
    session.add(media)
    await session.flush()  # 获取 ID 但不提交
    await session.refresh(media)
    return media


async def upload_single_markdown(
    session: AsyncSession,
    file_content: bytes,
    filename: str,
    textbook_id: int,
    parent_id: Optional[int],
    current_user: User,
) -> dict:
    """上传单个 Markdown 文件并创建章节

    验证文件扩展名，从文件名提取标题，检查教材与权限，
    计算同级 order_index，调用 chapter_service 创建章节并写入内容。

    Args:
        session: 数据库会话
        file_content: 文件内容（字节）
        filename: 原始文件名
        textbook_id: 目标教材 ID
        parent_id: 父章节 ID（None 表示根章节）
        current_user: 当前操作用户

    Returns:
        包含 id, title, level, order_index, textbook_id 的字典

    Raises:
        AppException: 文件扩展名不为 .md 时抛出 400
        AppException: 文件编码非 UTF-8 时抛出 400
        AppException: 教材不存在时抛出 404
        AppException: 无创建权限时抛出 403
    """
    ext = get_file_extension(filename or "")
    if ext != "md":
        raise AppException(code=400, message="只支持 .md 文件", data=None)

    # 先 URL 解码再去掉 .md 后缀，保证中文文件名（如 %E7%AB%A0%E8%8A%82.md）能正确提取标题
    basename = urllib.parse.unquote(os.path.basename(filename))
    title = basename[:-3] if basename.lower().endswith(".md") else basename
    title = title.strip() or "未命名章节"

    try:
        content_str = file_content.decode("utf-8")
    except UnicodeDecodeError:
        raise AppException(
            code=400, message="文件编码不支持，请使用 UTF-8 编码", data=None
        )

    # create_chapter 内部也会检查教材，但提前校验可以返回更明确的 404
    result = await session.execute(select(Textbook).where(Textbook.id == textbook_id))
    if not result.scalar_one_or_none():
        raise AppException(code=404, message="教材不存在", data=None)

    # 取同级最大 order_index + 1，保证新章节排在末尾而不覆盖现有排序
    order_result = await session.execute(
        select(func.max(Chapter.order_index))
        .where(Chapter.textbook_id == textbook_id)
        .where(Chapter.parent_id == parent_id)
    )
    max_order = order_result.scalar() or 0
    order_index = max_order + 1

    chapter_in = ChapterCreate(
        textbook_id=textbook_id,
        parent_id=parent_id,
        title=title,
        content=content_str,
        order_index=order_index,
        node_type=NodeType.ARTICLE,
    )
    chapter = await chapter_service.create_chapter(
        session=session,
        user=current_user,
        chapter_in=chapter_in,
    )
    # 为 ARTICLE 类型章节保存初始版本
    await version_service.save_version(
        session=session,
        chapter_id=chapter.id,
        content=content_str,
        user_id=current_user.id,
    )

    return {
        "id": chapter.id,
        "title": chapter.title,
        "level": chapter.level,
        "order_index": chapter.order_index,
        "textbook_id": chapter.textbook_id,
    }


__all__ = [
    "get_file_extension",
    "upload_image",
    "upload_markdown_zip",
    "upload_single_markdown",
    "MAX_IMAGE_SIZE",
    "MAX_ZIP_SIZE",
    "ALLOWED_IMAGE_EXTENSIONS",
    "ALLOWED_CONTENT_TYPES",
]

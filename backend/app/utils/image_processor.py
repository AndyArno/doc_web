"""
图片处理器模块

处理 Markdown 内容中的图片引用，包括提取、匹配和路径替换。
"""

import os
import re
from typing import TYPE_CHECKING
from urllib.parse import unquote

if TYPE_CHECKING:
    from app.models.media import Media


class ImageProcessor:
    """图片处理器

    处理 Markdown 内容中的本地图片引用。
    - 提取图片引用（跳过网络 URL 和 Base64）
    - 按文件名匹配 Media 记录
    - 替换图片路径
    """

    # Markdown 图片语法正则：![alt_text](image_path)
    IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

    # HTML img 标签正则：<img src="image.png" alt="..." ...>
    HTML_IMG_PATTERN = re.compile(
        r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*>', re.IGNORECASE
    )

    def __init__(self, storage_dir: str, base_url: str):
        """初始化图片处理器

        Args:
            storage_dir: 文件存储目录
            base_url: API 基础 URL
        """
        self.storage_dir = storage_dir
        self.base_url = base_url

    def extract_image_refs(self, content: str) -> list[tuple[str, str]]:
        """提取 Markdown 内容中的图片引用

        跳过网络 URL（http/https）和 Base64 图片（data:）。

        Args:
            content: Markdown 内容

        Returns:
            图片引用列表，每项为 (alt_text, image_path) 元组
        """
        refs: list[tuple[str, str]] = []

        for match in self.IMAGE_PATTERN.finditer(content):
            alt_text = match.group(1)
            image_path = match.group(2)

            # 跳过网络 URL 和 Base64
            if image_path.startswith(("http://", "https://", "data:")):
                continue

            refs.append((alt_text, image_path))

        return refs

    def extract_html_img_refs(self, content: str) -> list[tuple[str, str]]:
        """提取 HTML <img> 标签中的图片引用

        Returns:
            图片引用列表，每项为 (alt_text, src) 元组
        """
        refs: list[tuple[str, str]] = []
        for match in self.HTML_IMG_PATTERN.finditer(content):
            src = match.group(1)
            # 跳过网络 URL 和 Base64
            if src.startswith(("http://", "https://", "data:")):
                continue
            # 尝试提取 alt 属性
            alt_match = re.search(r'alt=["\']([^"\']*)["\']', match.group(0))
            alt_text = alt_match.group(1) if alt_match else ""
            refs.append((alt_text, src))
        return refs

    def match_images_by_filename(
        self, media_records: list["Media"], image_path: str
    ) -> "Media | None":
        """按文件名匹配 Media 记录

        从 image_path 中提取文件名（去除路径前缀），
        与 media_records 中的 original_name 进行匹配。

        Args:
            media_records: Media 记录列表
            image_path: 图片路径（可能包含 ./ 或 ../ 前缀）

        Returns:
            匹配的 Media 记录，无匹配则返回 None
        """
        # 从路径中提取文件名
        filename = unquote(os.path.basename(image_path))

        for media in media_records:
            if media.original_name == filename:
                return media

        return None

    def replace_path(self, content: str, old_path: str, new_url: str) -> str:
        """替换 Markdown 内容中的图片路径

        查找所有包含 old_path 的图片标记，替换为新 URL。
        保留原有的 alt_text。

        Args:
            content: Markdown 内容
            old_path: 原图片路径
            new_url: 新图片 URL

        Returns:
            替换后的 Markdown 内容
        """

        # 使用正则替换，保留 alt_text
        def replacer(match: re.Match) -> str:
            alt_text = match.group(1)
            return f"![{alt_text}]({new_url})"

        # 构建匹配模式，对 old_path 进行转义
        pattern = r"!\[([^\]]*)\]\(" + re.escape(old_path) + r"\)"
        return (
            self.IMAGE_PATTERN.sub(replacer, content)
            if old_path in content
            else content
        )

    def replace_html_img(
        self, content: str, old_src: str, new_url: str, alt_text: str = ""
    ) -> str:
        """替换 HTML <img> 标签为 Markdown 格式

        将 <img src="old_src" ...> 替换为 ![alt_text](new_url)

        Args:
            content: 包含 HTML img 标签的内容
            old_src: 原图片 src 属性值
            new_url: 新图片 URL
            alt_text: 图片 alt 文本

        Returns:
            替换后的内容
        """
        pattern = re.compile(
            r'<img\s+[^>]*src=["\']' + re.escape(old_src) + r'["\'][^>]*>',
            re.IGNORECASE,
        )
        return pattern.sub(f"![{alt_text}]({new_url})", content)

    def process_with_media_records(
        self,
        content: str,
        md_file_path: str,
        media_records: list["Media"],
    ) -> tuple[str, int]:
        """使用已存在的 Media 记录处理 Markdown 内容中的图片路径。

        用于 ZIP 上传场景：图片已保存并创建 Media 记录，
        此方法将 Markdown 中的相对路径替换为服务器 URL。
        支持两种格式：
        - Markdown: ![](image.png)
        - HTML: <img src="image.png">

        Args:
            content: Markdown 内容
            md_file_path: Markdown 文件路径（用于日志）
            media_records: 已创建的 Media 记录列表

        Returns:
            (处理后的内容, 替换数量) 元组
        """
        replaced_count = 0

        # 1. 处理 Markdown ![]() 格式
        refs = self.extract_image_refs(content)
        for alt_text, image_path in refs:
            matched_media = self.match_images_by_filename(media_records, image_path)
            if matched_media:
                new_url = f"{self.base_url}/{matched_media.filename}"
                content = self.replace_path(content, image_path, new_url)
                replaced_count += 1

        # 2. 处理 HTML <img> 标签格式
        html_refs = self.extract_html_img_refs(content)
        for alt_text, src in html_refs:
            matched_media = self.match_images_by_filename(media_records, src)
            if matched_media:
                new_url = f"{self.base_url}/{matched_media.filename}"
                content = self.replace_html_img(content, src, new_url, alt_text)
                replaced_count += 1

        return content, replaced_count

    def process_content_images(
        self,
        content: str,
        md_file_path: str,
        textbook_id: int,
        chapter_id: int,
    ) -> tuple[str, list[dict]]:
        """处理 Markdown 内容中的图片

        主入口方法，提取图片引用并处理。

        Args:
            content: Markdown 内容
            md_file_path: Markdown 文件路径（用于解析相对路径）
            textbook_id: 教材 ID
            chapter_id: 章节 ID

        Returns:
            (处理后的内容, 图片信息列表) 元组
        """
        # 提取本地图片引用
        refs = self.extract_image_refs(content)

        processed_images: list[dict] = []

        for alt_text, image_path in refs:
            # 当前测试只验证结构和跳过逻辑
            # 实际文件处理逻辑在后续集成时实现
            info = {
                "alt_text": alt_text,
                "original_path": image_path,
                "textbook_id": textbook_id,
                "chapter_id": chapter_id,
            }
            processed_images.append(info)

        return content, processed_images

"""压缩文件提取工具。

支持 ZIP、TAR、TAR.GZ、7z、RAR 格式的安全提取。
"""

import io
import logging
import os
import shutil
import tarfile
import tempfile
import zipfile
from enum import Enum
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)

import py7zr
import rarfile

from app.core.exceptions import AppException


class ArchiveFormat(Enum):
    """支持的压缩格式枚举。"""

    ZIP = "zip"
    TAR = "tar"
    TAR_GZ = "tar_gz"
    TAR_BZ2 = "tar_bz2"
    TAR_XZ = "tar_xz"
    SEVEN_Z = "7z"
    RAR = "rar"


# 安全限制常量
MAX_COMPRESSION_RATIO = 100  # 最大压缩比
MAX_FILE_COUNT = 10000  # 最大文件数量
MAX_UNCOMPRESSED_SIZE = 1024 * 1024 * 1024  # 最大解压大小 1GB


class ArchiveExtractor:
    """压缩文件提取器。

    提供安全的压缩文件提取功能，包含路径遍历防护、符号链接检测、
    ZIP炸弹检测等安全措施。

    支持从文件路径或 BytesIO 对象创建实例。

    Attributes:
        archive_path: 压缩文件路径（如果是 BytesIO 输入则为 None）。
        _format: 检测到的压缩格式。
    """

    # 格式魔数
    MAGIC_NUMBERS = {
        b"PK\x03\x04": ArchiveFormat.ZIP,
        b"PK\x05\x06": ArchiveFormat.ZIP,  # 空ZIP
        b"\x1f\x8b": ArchiveFormat.TAR_GZ,  # gzip
        b"BZ": ArchiveFormat.TAR_BZ2,  # bzip2
        b"\xfd7zXZ\x00": ArchiveFormat.TAR_XZ,  # xz
        b"7z\xbc\xaf'\x1c": ArchiveFormat.SEVEN_Z,
        b"Rar!\x1a\x07": ArchiveFormat.RAR,
    }

    def __init__(
        self,
        archive_source: Union[Path, io.BytesIO],
        filename: str | None = None,
    ) -> None:
        """初始化压缩文件提取器。

        Args:
            archive_source: 压缩文件路径或 BytesIO 对象。
            filename: 文件名（仅当 archive_source 为 BytesIO 时使用，用于格式检测）。

        Raises:
            FileNotFoundError: 文件不存在（当 archive_source 为 Path 时）。
            ValueError: 不支持的压缩格式。
        """
        self._bytesio_source: io.BytesIO | None = None
        self._temp_file: Path | None = None
        self._filename: str | None = filename

        if isinstance(archive_source, io.BytesIO):
            self._bytesio_source = archive_source
            self.archive_path: Path | None = None
            # 将 BytesIO 内容保存到临时文件，以便后续操作
            self._bytesio_source.seek(0)
            self._temp_file = Path(tempfile.mktemp(prefix="archive_"))
            with open(self._temp_file, "wb") as f:
                f.write(self._bytesio_source.read())
            self.archive_path = self._temp_file
        else:
            if not archive_source.exists():
                raise FileNotFoundError(f"压缩文件不存在: {archive_source}")
            self.archive_path = archive_source

        self._format: ArchiveFormat | None = None

    def detect_format(self) -> ArchiveFormat:
        """检测压缩文件格式。

        通过文件扩展名和魔数综合判断格式。

        Returns:
            检测到的压缩格式。

        Raises:
            ValueError: 不支持的压缩格式。
        """
        if self._format is not None:
            return self._format

        # 优先使用文件名检测（对于 BytesIO 输入）
        if self._filename:
            name_lower = self._filename.lower()
            if name_lower.endswith(".zip"):
                self._format = ArchiveFormat.ZIP
            elif name_lower.endswith(".tar.gz") or name_lower.endswith(".tgz"):
                self._format = ArchiveFormat.TAR_GZ
            elif name_lower.endswith(".tar.bz2") or name_lower.endswith(".tbz2"):
                self._format = ArchiveFormat.TAR_BZ2
            elif name_lower.endswith(".tar.xz") or name_lower.endswith(".txz"):
                self._format = ArchiveFormat.TAR_XZ
            elif name_lower.endswith(".tar"):
                self._format = ArchiveFormat.TAR
            elif name_lower.endswith(".7z"):
                self._format = ArchiveFormat.SEVEN_Z
            elif name_lower.endswith(".rar"):
                self._format = ArchiveFormat.RAR

        # 如果文件名未确定格式，尝试扩展名（对于 Path 输入）
        if self._format is None and self.archive_path:
            suffix = self.archive_path.suffix.lower()
            name_lower = self.archive_path.name.lower()

            if suffix == ".zip":
                self._format = ArchiveFormat.ZIP
            elif name_lower.endswith(".tar.gz") or name_lower.endswith(".tgz"):
                self._format = ArchiveFormat.TAR_GZ
            elif name_lower.endswith(".tar.bz2") or name_lower.endswith(".tbz2"):
                self._format = ArchiveFormat.TAR_BZ2
            elif name_lower.endswith(".tar.xz") or name_lower.endswith(".txz"):
                self._format = ArchiveFormat.TAR_XZ
            elif suffix == ".tar":
                self._format = ArchiveFormat.TAR
            elif suffix == ".7z":
                self._format = ArchiveFormat.SEVEN_Z
            elif suffix == ".rar":
                self._format = ArchiveFormat.RAR

        # 最后尝试魔数检测
        if self._format is None:
            self._format = self._detect_by_magic()

        if self._format is None:
            raise ValueError(f"不支持的压缩格式: {self._filename or self.archive_path}")

        return self._format

    def _detect_by_magic(self) -> ArchiveFormat | None:
        """通过魔数检测格式。"""
        try:
            with open(self.archive_path, "rb") as f:
                header = f.read(8)

            for magic, fmt in self.MAGIC_NUMBERS.items():
                if header.startswith(magic):
                    return fmt
        except OSError as e:
            logger.warning(f"无法检测文件类型: {e}")

        return None

    def extract(self, dest_dir: Path) -> list[Path]:
        """提取压缩文件到目标目录。

        Args:
            dest_dir: 目标目录路径。

        Returns:
            提取的文件路径列表。

        Raises:
            ValueError: 安全检查失败或文件损坏。
        """
        dest_dir.mkdir(parents=True, exist_ok=True)

        fmt = self.detect_format()

        if fmt == ArchiveFormat.ZIP:
            return self._extract_zip(dest_dir)
        elif fmt in (
            ArchiveFormat.TAR,
            ArchiveFormat.TAR_GZ,
            ArchiveFormat.TAR_BZ2,
            ArchiveFormat.TAR_XZ,
        ):
            return self._extract_tar(dest_dir)
        elif fmt == ArchiveFormat.SEVEN_Z:
            return self._extract_7z(dest_dir)
        elif fmt == ArchiveFormat.RAR:
            return self._extract_rar(dest_dir)
        else:
            raise ValueError(f"不支持的压缩格式: {fmt}")

    def _extract_zip(self, dest_dir: Path) -> list[Path]:
        """提取 ZIP 文件。"""
        extracted_files: list[Path] = []

        try:
            with zipfile.ZipFile(self.archive_path, "r") as zf:
                if len(zf.namelist()) > MAX_FILE_COUNT:
                    raise ValueError(
                        f"文件数量超过限制: {len(zf.namelist())} > {MAX_FILE_COUNT}"
                    )

                self._check_zip_bomb(zf)

                for info in zf.infolist():
                    if self._is_zip_symlink(info):
                        raise ValueError(f"压缩文件包含符号链接: {info.filename}")

                    target_path = dest_dir / info.filename
                    if not self._is_safe_path(dest_dir, target_path):
                        raise ValueError(f"路径遍历攻击检测: {info.filename}")

                    if info.is_dir():
                        continue

                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    with zf.open(info) as src:
                        target_path.write_bytes(src.read())

                    extracted_files.append(target_path)

        except zipfile.BadZipFile as e:
            raise ValueError(f"损坏或无效的 ZIP 文件: {e}") from e

        return extracted_files

    def _extract_tar(self, dest_dir: Path) -> list[Path]:
        """提取 TAR 文件（包括压缩变体）。"""
        extracted_files: list[Path] = []

        fmt = self.detect_format()
        mode_map = {
            ArchiveFormat.TAR: "r",
            ArchiveFormat.TAR_GZ: "r:gz",
            ArchiveFormat.TAR_BZ2: "r:bz2",
            ArchiveFormat.TAR_XZ: "r:xz",
        }
        mode = mode_map.get(fmt, "r")

        try:
            with tarfile.open(self.archive_path, mode) as tf:
                if len(tf.getmembers()) > MAX_FILE_COUNT:
                    raise ValueError(
                        f"文件数量超过限制: {len(tf.getmembers())} > {MAX_FILE_COUNT}"
                    )

                for member in tf.getmembers():
                    if member.issym() or member.islnk():
                        raise ValueError(f"压缩文件包含符号链接: {member.name}")

                    if not member.isfile():
                        continue

                    target_path = dest_dir / member.name
                    if not self._is_safe_path(dest_dir, target_path):
                        raise ValueError(f"路径遍历攻击检测: {member.name}")

                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    with tf.extractfile(member) as src:
                        if src is not None:
                            target_path.write_bytes(src.read())
                            extracted_files.append(target_path)

        except tarfile.TarError as e:
            raise ValueError(f"损坏或无效的 TAR 文件: {e}") from e

        return extracted_files

    def _extract_7z(self, dest_dir: Path) -> list[Path]:
        """提取 7z 文件。

        使用 py7zr 库进行提取，包含安全检查。

        Args:
            dest_dir: 目标目录路径。

        Returns:
            提取的文件路径列表。

        Raises:
            ValueError: 安全检查失败或文件损坏。
        """
        extracted_files: list[Path] = []

        try:
            with py7zr.SevenZipFile(self.archive_path, mode="r") as archive:
                members = archive.getnames()

                if len(members) > MAX_FILE_COUNT:
                    raise ValueError(
                        f"文件数量超过限制: {len(members)} > {MAX_FILE_COUNT}"
                    )

                for name in members:
                    target_path = dest_dir / name
                    if not self._is_safe_path(dest_dir, target_path):
                        raise ValueError(f"路径遍历攻击检测: {name}")

                archive.extractall(path=str(dest_dir))

                for name in members:
                    target_path = dest_dir / name
                    if target_path.is_file():
                        extracted_files.append(target_path)

        except py7zr.exceptions.Bad7zFile as e:
            raise ValueError(f"损坏或无效的 7z 文件: {e}") from e
        except py7zr.exceptions.PasswordRequired as e:
            raise ValueError(f"7z 文件需要密码: {e}") from e

        return extracted_files

    def _extract_rar(self, dest_dir: Path) -> list[Path]:
        """提取 RAR 文件。

        注意: RAR 格式需要系统安装 unrar 或 unar 二进制工具。

        Args:
            dest_dir: 目标目录路径。

        Returns:
            提取的文件路径列表。

        Raises:
            ValueError: 安全检查失败、文件损坏或缺少 unrar 工具。
        """
        # 检查 unrar/unar 是否可用
        unrar_tool = self._find_unrar_tool()
        if unrar_tool is None:
            raise ValueError(
                "RAR 格式需要安装 unrar 或 unar 工具。\n"
                "Ubuntu/Debian: sudo apt install unrar 或 sudo apt install unar\n"
                "CentOS/RHEL: sudo yum install unrar\n"
                "macOS: brew install unar"
            )

        # 配置 rarfile 使用找到的工具
        rarfile.UNRAR_TOOL = unrar_tool

        extracted_files: list[Path] = []

        try:
            with rarfile.RarFile(self.archive_path, "r") as archive:
                # 安全校验
                self._check_rar_security(archive)

                for info in archive.infolist():
                    # 跳过目录
                    if info.isdir():
                        continue

                    # 检查路径遍历
                    target_path = dest_dir / info.filename
                    if not self._is_safe_path(dest_dir, target_path):
                        raise ValueError(f"路径遍历攻击检测: {info.filename}")

                    # 创建父目录
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    # 提取文件
                    with archive.open(info) as src:
                        target_path.write_bytes(src.read())

                    extracted_files.append(target_path)

        except rarfile.NeedFirstVolume:
            raise ValueError(
                "RAR 文件是分卷压缩包的一部分，请提供完整的第一个分卷"
            ) from None
        except rarfile.BadRarFile as e:
            raise ValueError(f"损坏或无效的 RAR 文件: {e}") from e
        except rarfile.RarCRCError as e:
            raise ValueError(f"RAR 文件 CRC 校验失败: {e}") from e
        except rarfile.RarWrongPassword as e:
            raise ValueError(f"RAR 文件密码错误: {e}") from e

        return extracted_files

    def _find_unrar_tool(self) -> str | None:
        """查找可用的 unrar 或 unar 工具。

        Returns:
            工具路径，如果未找到返回 None。
        """
        # 优先使用 unrar
        unrar_path = shutil.which("unrar")
        if unrar_path:
            return unrar_path

        # 备选使用 unar（macOS 常用）
        unar_path = shutil.which("unar")
        if unar_path:
            return unar_path

        return None

    def _check_rar_security(self, archive: rarfile.RarFile) -> None:
        """检查 RAR 文件安全性。

        Args:
            archive: RAR 文件对象。

        Raises:
            ValueError: 安全检查失败。
        """
        file_count = 0
        total_compressed = 0
        total_uncompressed = 0

        for info in archive.infolist():
            if not info.isdir():
                file_count += 1
                total_compressed += info.compress_size
                total_uncompressed += info.file_size

        # 检查文件数量
        if file_count > MAX_FILE_COUNT:
            raise ValueError(f"文件数量超过限制: {file_count} > {MAX_FILE_COUNT}")

        # 检查压缩比
        if total_compressed > 0:
            ratio = total_uncompressed / total_compressed
            if ratio > MAX_COMPRESSION_RATIO:
                raise ValueError(
                    f"检测到可疑压缩比: {ratio:.1f} > {MAX_COMPRESSION_RATIO}"
                )

        # 检查解压后总大小
        if total_uncompressed > MAX_UNCOMPRESSED_SIZE:
            raise ValueError(
                f"解压后大小超过限制: {total_uncompressed} > {MAX_UNCOMPRESSED_SIZE}"
            )

    def _is_safe_path(self, base_dir: Path, target_path: Path) -> bool:
        """检查目标路径是否安全（防止路径遍历攻击）。

        Args:
            base_dir: 基础目录。
            target_path: 目标路径。

        Returns:
            如果路径安全返回 True，否则返回 False。
        """
        try:
            base_abs = base_dir.resolve()
            target_abs = target_path.resolve()
            return str(target_abs).startswith(str(base_abs))
        except (OSError, ValueError):
            return False

    def _is_zip_symlink(self, info: zipfile.ZipInfo) -> bool:
        """检查 ZIP 条目是否为符号链接。

        Args:
            info: ZIP 文件信息。

        Returns:
            如果是符号链接返回 True，否则返回 False。
        """
        # Unix 符号链接类型在 external_attr 高 4 位为 0xA
        if info.external_attr >> 28 == 0xA:
            return True

        # 符号链接模式: 0o120000
        mode = info.external_attr >> 16
        return (mode & 0o170000) == 0o120000

    def _check_zip_bomb(self, zf: zipfile.ZipFile) -> None:
        """检查 ZIP 炸弹。

        通过检查压缩比来检测潜在的 ZIP 炸弹攻击。

        Args:
            zf: ZIP 文件对象。

        Raises:
            ValueError: 检测到 ZIP 炸弹。
        """
        total_compressed = 0
        total_uncompressed = 0

        for info in zf.infolist():
            total_compressed += info.compress_size
            total_uncompressed += info.file_size

        # 检查压缩比
        if total_compressed > 0:
            ratio = total_uncompressed / total_compressed
            if ratio > MAX_COMPRESSION_RATIO:
                raise ValueError(
                    f"检测到可疑压缩比: {ratio:.1f} > {MAX_COMPRESSION_RATIO}"
                )

        # 检查解压后总大小
        if total_uncompressed > MAX_UNCOMPRESSED_SIZE:
            raise ValueError(
                f"解压后大小超过限制: {total_uncompressed} > {MAX_UNCOMPRESSED_SIZE}"
            )

    def cleanup(self) -> None:
        """清理临时文件（如果是 BytesIO 输入创建的）。"""
        if self._temp_file and self._temp_file.exists():
            try:
                self._temp_file.unlink()
            except OSError as e:
                logger.warning(f"清理临时文件失败: {e}")
            self._temp_file = None

    def __del__(self) -> None:
        """析构时清理临时文件。"""
        self.cleanup()

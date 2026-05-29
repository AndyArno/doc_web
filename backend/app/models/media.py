"""
媒体资源模型模块

定义媒体文件表结构，支持软删除。
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base, TimestampMixin, int_pk
import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.models.textbook import Textbook
    from app.models.chapter import Chapter


class Media(Base, TimestampMixin):
    """媒体资源模型

    存储上传的图片和文件信息，支持软删除（回收站功能）。
    """

    __tablename__ = "media"

    id: Mapped[int_pk]
    textbook_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("textbooks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    chapter_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # 文件信息
    filename: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # 存储文件名（唯一）
    original_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # 原始文件名
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)  # 绝对路径（磁盘位置，仅服务端使用）
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # 字节数
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)  # MIME 类型

    # 软删除字段
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    # 关系
    textbook: Mapped[Optional["Textbook"]] = relationship(
        "Textbook", back_populates="media_files"
    )
    chapter: Mapped[Optional["Chapter"]] = relationship(
        "Chapter", back_populates="media_files"
    )

    def __repr__(self) -> str:
        return f"<Media(id={self.id}, filename='{self.filename}', is_deleted={self.is_deleted})>"

    @property
    def file_size_mb(self) -> float:
        """文件大小（MB）"""
        return self.file_size / (1024 * 1024)

    @property
    def textbook_title(self) -> str | None:
        """关联教材的标题"""
        return self.textbook.title if self.textbook else None

    def soft_delete(self) -> None:
        """软删除"""
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)

    def restore(self) -> None:
        """从回收站恢复"""
        self.is_deleted = False
        self.deleted_at = None

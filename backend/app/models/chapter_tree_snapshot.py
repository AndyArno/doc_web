"""
章节树快照模型模块

定义章节树快照表结构，用于存储排序前的章节结构快照，支持撤回功能。
"""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, int_pk

if TYPE_CHECKING:
    from app.models.textbook import Textbook


class ChapterTreeSnapshot(Base, TimestampMixin):
    """章节树快照模型

    存储教材章节结构的快照，用于排序或导入操作的撤回功能。
    快照记录章节的 id, order_index, parent_id 三元组信息。
    """

    __tablename__ = "chapter_tree_snapshots"

    # 复合索引：优化按教材和时间查询快照
    __table_args__ = (
        Index("ix_chapter_tree_snapshots_textbook_created", "textbook_id", "created_at"),
    )

    id: Mapped[int_pk]
    textbook_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("textbooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    snapshot_data: Mapped[dict | list] = mapped_column(
        JSON,
        nullable=False,
        comment="章节树快照数据，包含所有章节的 {id, order_index, parent_id}",
    )
    operation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="操作类型，如 sort, zip_import",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="快照是否有效，撤回后设为 False",
    )

    def __repr__(self) -> str:
        return f"<ChapterTreeSnapshot(id={self.id}, textbook_id={self.textbook_id}, operation_type='{self.operation_type}')>"

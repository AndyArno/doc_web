"""
章节模型模块

定义章节表结构，支持三级自关联树结构。
"""

import enum
import re
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, int_pk

if TYPE_CHECKING:
    from app.models.chapter_version import ChapterVersion
    from app.models.media import Media
    from app.models.textbook import Textbook


class NodeType(str, enum.Enum):
    """节点类型枚举

    - FOLDER: 目录节点，可展开，没有 content
    - ARTICLE: 文章节点，有 content，不能有子节点
    """

    FOLDER = "folder"
    ARTICLE = "article"


def generate_slug(title: str) -> str:
    """根据标题生成 slug

    转小写，替换空格为连字符，移除特殊字符。
    保留中文字符（URL会自动编码）。

    Args:
        title: 章节标题

    Returns:
        生成的 slug 字符串
    """
    slug = title.lower().strip()
    slug = re.sub(r"[\s]+", "-", slug)
    # 保留中文基本汉字 \u4e00-\u9fff，URL会自动编码
    slug = re.sub(r"[^a-z0-9\u4e00-\u9fff\-]", "", slug)
    return slug


class Chapter(Base, TimestampMixin):
    """章节模型

    支持三级结构：章（level=1）→ 节（level=2）→ 小节（level=3）
    通过 parent_id 实现自关联。
    """

    __tablename__ = "chapters"

    # 复合索引：优化教材章节列表查询
    __table_args__ = (
        Index("ix_chapters_textbook_order", "textbook_id", "order_index"),
    )

    id: Mapped[int_pk]
    textbook_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("textbooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    node_type: Mapped[NodeType] = mapped_column(
        Enum(NodeType),
        nullable=False,
        default=NodeType.FOLDER,
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    textbook: Mapped["Textbook"] = relationship("Textbook", back_populates="chapters")
    media_files: Mapped[List["Media"]] = relationship(
        "Media",
        back_populates="chapter",
    )
    versions: Mapped[List["ChapterVersion"]] = relationship(
        "ChapterVersion",
        back_populates="chapter",
        cascade="all, delete-orphan",
        order_by="desc(ChapterVersion.version_num)",
    )

    def __repr__(self) -> str:
        return f"<Chapter(id={self.id}, title='{self.title}', level={self.level}, node_type={self.node_type.value})>"

    @property
    def has_content(self) -> bool:
        return bool(self.content and self.content.strip())


Chapter.parent = relationship(
    "Chapter",
    remote_side=Chapter.id,
    back_populates="children",
)
Chapter.children = relationship(
    "Chapter",
    back_populates="parent",
    cascade="all, delete-orphan",
    order_by=Chapter.order_index,
)

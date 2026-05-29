"""
章节版本模型模块

定义章节版本历史表结构，用于保存章节内容的历史版本。
"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, int_pk

if TYPE_CHECKING:
    from app.models.chapter import Chapter
    from app.models.user import User


class ChapterVersion(Base, TimestampMixin):
    """章节版本模型

    保存章节内容的历史版本，支持版本回退和查看历史修改。
    """

    __tablename__ = "chapter_versions"

    # 复合唯一约束：确保同一章节的版本号唯一
    __table_args__ = (
        UniqueConstraint("chapter_id", "version_num", name="uq_chapter_version"),
    )

    id: Mapped[int_pk]
    chapter_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    version_num: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # 关系
    chapter: Mapped["Chapter"] = relationship(
        "Chapter",
        back_populates="versions",
    )
    creator: Mapped["User | None"] = relationship(
        "User",
        back_populates="chapter_versions",
    )

    def __repr__(self) -> str:
        return f"<ChapterVersion(id={self.id}, chapter_id={self.chapter_id}, version_num={self.version_num})>"

"""
教材模型模块

定义教材表结构和状态枚举。
"""

import enum
from typing import TYPE_CHECKING, List

from sqlalchemy import Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, int_pk


class TextbookStatus(str, enum.Enum):
    """教材状态枚举"""

    DRAFT = "draft"
    PUBLISHED = "published"


if TYPE_CHECKING:
    from app.models.chapter import Chapter
    from app.models.media import Media
    from app.models.permission import UserTextbookPermission


class Textbook(Base, TimestampMixin):
    """教材模型

    存储教材基本信息。
    """

    __tablename__ = "textbooks"

    id: Mapped[int_pk]
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    slug: Mapped[str] = mapped_column(
        String(200), unique=True, index=True, nullable=False
    )
    status: Mapped[TextbookStatus] = mapped_column(
        Enum(TextbookStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=TextbookStatus.DRAFT,
        nullable=False,
    )

    # 关系
    chapters: Mapped[List["Chapter"]] = relationship(
        "Chapter",
        back_populates="textbook",
        cascade="all, delete-orphan",
        order_by="Chapter.order_index",
    )
    permissions: Mapped[List["UserTextbookPermission"]] = relationship(
        "UserTextbookPermission",
        back_populates="textbook",
        cascade="all, delete-orphan",
    )
    media_files: Mapped[List["Media"]] = relationship(
        "Media",
        back_populates="textbook",
    )

    def __repr__(self) -> str:
        return f"<Textbook(id={self.id}, title='{self.title}', status={self.status})>"

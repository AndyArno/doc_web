"""
用户模型模块

定义用户表结构和角色枚举。
"""

import enum
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, int_pk

if TYPE_CHECKING:
    from app.models.chapter_version import ChapterVersion
    from app.models.permission import UserTextbookPermission
    from app.models.textbook import Textbook


class Role(str, enum.Enum):
    """用户角色枚举"""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    EDITOR = "editor"
    USER = "user"


class User(Base, TimestampMixin):
    """用户模型

    存储用户账户信息和角色。
    """

    __tablename__ = "users"

    id: Mapped[int_pk]
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    must_change_password: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # 关系
    permissions: Mapped[List["UserTextbookPermission"]] = relationship(
        "UserTextbookPermission",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    chapter_versions: Mapped[List["ChapterVersion"]] = relationship(
        "ChapterVersion",
        back_populates="creator",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role={self.role})>"

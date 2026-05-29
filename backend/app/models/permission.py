"""
权限模型模块

定义用户教材权限表结构。
"""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, int_pk

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.textbook import Textbook


class UserTextbookPermission(Base, TimestampMixin):
    """用户教材权限模型

    定义用户对特定教材的操作权限。
    """

    __tablename__ = "user_textbook_permissions"

    id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    textbook_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("textbooks.id", ondelete="CASCADE"), nullable=False
    )

    # 权限字段
    can_access: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="permissions")
    textbook: Mapped["Textbook"] = relationship(
        "Textbook", back_populates="permissions"
    )

    def __repr__(self) -> str:
        return f"<UserTextbookPermission(user_id={self.user_id}, textbook_id={self.textbook_id}, can_access={self.can_access})>"

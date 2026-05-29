"""
审计日志模型模块

记录用户操作审计日志，用于追踪系统中的关键操作。
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, int_pk, timestamp

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base):
    """审计日志模型

    记录系统中的关键操作，包括用户管理、权限变更、内容修改等。
    """

    __tablename__ = "audit_logs"

    id: Mapped[int_pk]
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    operator_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[timestamp]

    target_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[target_user_id]
    )
    operator: Mapped["User | None"] = relationship("User", foreign_keys=[operator_id])

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', operator_id={self.operator_id})>"

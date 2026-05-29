"""
系统配置模型模块

定义系统级键值对配置表。
"""

from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class SystemConfig(Base, TimestampMixin):
    """系统配置模型

    存储系统级键值对配置，以 key 为主键。
    """

    __tablename__ = "system_config"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SystemConfig(key='{self.key}')>"

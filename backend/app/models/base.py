"""
SQLAlchemy 基础模型模块

提供声明式基类和通用字段定义。
"""

from datetime import datetime
from typing import Annotated

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 整数主键类型别名
int_pk = Annotated[int, mapped_column(Integer, primary_key=True, autoincrement=True)]

# 时间戳类型别名
timestamp = Annotated[
    datetime, mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
]
updated_at = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    ),
]


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类

    所有模型类都应继承此类。
    """

    pass


class TimestampMixin:
    """时间戳混入类

    提供 created_at 和 updated_at 字段。
    """

    created_at: Mapped[timestamp]
    updated_at: Mapped[updated_at]

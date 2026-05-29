"""
系统初始化状态模块

提供检查系统是否已初始化以及标记为已初始化的功能。
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_config import SystemConfig


async def is_initialized(session: AsyncSession) -> bool:
    """检查系统是否已完成初始化。

    查询 SystemConfig 表中 key 为 "setup_complete" 的记录，
    若存在且 value 为 "true" 则返回 True，否则返回 False。

    Args:
        session: 数据库异步会话。

    Returns:
        bool: 系统是否已初始化。
    """
    result = await session.execute(
        select(SystemConfig).where(SystemConfig.key == "setup_complete")
    )
    row = result.scalar_one_or_none()
    return row is not None and row.value == "true"


async def mark_initialized(session: AsyncSession) -> None:
    """将系统标记为已初始化。

    在 SystemConfig 表中 upsert key 为 "setup_complete" 的记录，
    value 设为 "true"。如记录已存在则更新，否则新建。

    Args:
        session: 数据库异步会话。
    """
    result = await session.execute(
        select(SystemConfig).where(SystemConfig.key == "setup_complete")
    )
    row = result.scalar_one_or_none()

    if row:
        row.value = "true"
    else:
        session.add(SystemConfig(key="setup_complete", value="true"))

    await session.commit()

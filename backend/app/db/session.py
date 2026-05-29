"""
数据库会话管理模块

提供 SQLAlchemy 异步会话工厂和依赖注入函数。
"""

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_settings = get_settings()

from collections import deque
import time as _time
from sqlalchemy import event as _event

_pool_events: deque = deque(maxlen=100000)
_pool_checked_out: int = 0
_pool_connected: int = 0
_pool_total_checkouts: int = 0

engine = create_async_engine(
    _settings.DATABASE_URL,
    echo=_settings.DEBUG,
    future=True,
    pool_size=20,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
)

@_event.listens_for(engine.sync_engine, "checkout")
def _on_checkout(dbapi_connection, connection_record, connection_proxy):
    _pool_events.append({"ts": _time.time(), "type": "checkout"})
    global _pool_checked_out, _pool_total_checkouts
    _pool_checked_out += 1
    _pool_total_checkouts += 1

@_event.listens_for(engine.sync_engine, "checkin")
def _on_checkin(dbapi_connection, connection_record):
    _pool_events.append({"ts": _time.time(), "type": "checkin"})
    global _pool_checked_out
    _pool_checked_out -= 1

@_event.listens_for(engine.sync_engine, "connect")
def _on_connect(dbapi_connection, connection_record):
    _pool_events.append({"ts": _time.time(), "type": "connect"})
    global _pool_connected
    _pool_connected += 1

@_event.listens_for(engine.sync_engine, "close")
def _on_close(dbapi_connection, connection_record):
    _pool_events.append({"ts": _time.time(), "type": "close"})
    global _pool_connected
    _pool_connected -= 1

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """获取数据库会话（依赖注入）

    Yields:
        AsyncSession: 数据库会话对象

    Example:
        @router.get("/users")
        async def get_users(db: SessionDep):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_pool_events():
    return _pool_events


def get_pool_counters():
    return {"checked_out": _pool_checked_out, "connected": _pool_connected, "total_checkouts": _pool_total_checkouts}

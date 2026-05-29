"""异步任务进度管理器

提供 TaskManager 类，基于内存 dict + asyncio.Lock 实现线程安全的
任务状态跟踪。适用于长时间运行的后台任务进度查询。

用法:
    from app.utils.task_manager import task_manager

    task_id = task_manager.create()
    task_manager.update(task_id, stage="处理中", progress=50)
    status = task_manager.get(task_id)
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import asyncio


@dataclass
class TaskStatus:
    """任务状态数据

    Attributes:
        task_id: 唯一任务标识 (UUID4 字符串)
        status: 任务状态 (pending/running/completed/failed)
        stage: 当前阶段描述 (如 "解析中", "上传图片中")
        progress: 进度百分比 (0-100)
        result: 任务完成后的结果数据
        error: 错误信息 (失败时)
        created_at: 创建时间 (time.time 时间戳)
        updated_at: 最后更新时间 (time.time 时间戳)
    """

    task_id: str
    status: str = "pending"
    stage: str = ""
    progress: int = 0
    result: Any = None
    error: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class TaskManager:
    """异步任务进度管理器

    使用 dict + asyncio.Lock 实现线程安全的内存级任务状态跟踪。
    支持创建、更新、查询和过期清理操作。
    """

    def __init__(self) -> None:
        self._tasks: dict[str, TaskStatus] = {}
        self._lock = asyncio.Lock()

    async def create(self) -> str:
        """创建一个新任务

        Returns:
            UUID4 字符串格式的任务 ID
        """
        task_id = str(uuid.uuid4())
        status = TaskStatus(task_id=task_id)
        async with self._lock:
            self._tasks[task_id] = status
        return task_id

    async def update(self, task_id: str, **kwargs: Any) -> None:
        """更新任务状态

        只更新 kwargs 中存在的字段 (status, stage, progress, result, error)，
        自动设置 updated_at 为当前时间。

        Args:
            task_id: 要更新的任务 ID
            **kwargs: 可更新字段: status, stage, progress, result, error

        Raises:
            KeyError: 任务不存在时抛出
        """
        allowed_fields = {"status", "stage", "progress", "result", "error"}
        async with self._lock:
            status = self._tasks.get(task_id)
            if status is None:
                raise KeyError(f"Task {task_id} not found")
            for key, value in kwargs.items():
                if key in allowed_fields:
                    setattr(status, key, value)
            status.updated_at = time.time()

    async def get(self, task_id: str) -> TaskStatus | None:
        """获取任务状态

        Args:
            task_id: 任务 ID

        Returns:
            TaskStatus 实例，任务不存在时返回 None
        """
        async with self._lock:
            return self._tasks.get(task_id)

    async def cleanup_expired(self, max_age_seconds: int = 3600) -> int:
        """清理过期任务

        移除所有 created_at 早于当前时间 - max_age_seconds 的任务。

        Args:
            max_age_seconds: 任务最大存活时间 (秒)，默认 3600

        Returns:
            被清理的任务数量
        """
        cutoff = time.time() - max_age_seconds
        removed = 0
        async with self._lock:
            expired_ids = [
                tid
                for tid, status in self._tasks.items()
                if status.created_at < cutoff
            ]
            for tid in expired_ids:
                del self._tasks[tid]
                removed += 1
        return removed


# 全局单例
task_manager = TaskManager()

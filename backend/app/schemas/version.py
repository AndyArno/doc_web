"""版本相关的 Pydantic schemas"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VersionDiffLine(BaseModel):
    """差异对比行

    Attributes:
        type: 行类型，'added'、'removed'、'unchanged'
        content: 行内容
        old_line_num: 原始行号（删除行和未改变行有值）
        new_line_num: 新行号（添加行和未改变行有值）
    """

    type: str  # 'added', 'removed', 'unchanged'
    content: str
    old_line_num: int | None = None
    new_line_num: int | None = None


class VersionDiffResponse(BaseModel):
    """版本差异对比响应"""

    from_version: "VersionResponse"
    to_version: "VersionResponse"
    diff: list[VersionDiffLine]
    summary: dict  # {'added': N, 'removed': N, 'changed': N}


class VersionResponse(BaseModel):
    """版本响应 schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    chapter_id: int
    content: str | None
    version_num: int
    created_by: int | None
    created_at: datetime
    updated_at: datetime


class VersionListResponse(BaseModel):
    """版本列表响应"""

    chapter_id: int
    total: int
    versions: list[VersionResponse]

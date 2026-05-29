"""教材相关的 Pydantic schemas"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.textbook import TextbookStatus


class TextbookBase(BaseModel):
    """教材基础 schema"""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    cover_image: str | None = None


class TextbookCreate(TextbookBase):
    """创建教材 schema"""

    status: TextbookStatus = Field(default=TextbookStatus.DRAFT)


class TextbookUpdate(BaseModel):
    """更新教材 schema"""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    cover_image: str | None = None
    status: TextbookStatus | None = None


class TextbookResponse(BaseModel):
    """教材响应 schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    cover_image: str | None
    slug: str
    status: TextbookStatus
    created_at: datetime
    updated_at: datetime


class TextbookListResponse(BaseModel):
    """教材列表响应"""

    items: list[TextbookResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

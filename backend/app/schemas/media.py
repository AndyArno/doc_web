"""媒体资源相关的 Pydantic schemas"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field


class MediaResponse(BaseModel):
    """媒体响应 schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    textbook_id: int | None
    textbook_title: str | None
    chapter_id: int | None
    filename: str
    original_name: str
    file_path: str
    file_size: int
    file_type: str
    is_deleted: bool
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def file_size_mb(self) -> float:
        return round(self.file_size / (1024 * 1024), 2)

    @computed_field
    @property
    def url(self) -> str:
        return f"/uploads/images/{self.filename}"


class MediaListResponse(BaseModel):
    """媒体列表响应"""

    items: list[MediaResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TrashListResponse(BaseModel):
    """回收站列表响应"""

    items: list[MediaResponse]
    total: int
    total_size_mb: float


class UploadResponse(BaseModel):
    """上传响应 schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    original_name: str
    file_path: str
    file_size: int
    file_type: str
    url: str
    warning: str | None = None


class MarkdownUploadResponse(BaseModel):
    """Markdown ZIP 上传响应"""

    textbook_id: int
    title: str
    chapters_count: int
    task_id: str | None = None
    message: str

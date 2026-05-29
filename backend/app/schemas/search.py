"""搜索相关数据模型

定义搜索 API 的请求和响应模型。
"""

from pydantic import BaseModel, Field


class SearchQueryParams(BaseModel):
    """搜索查询参数

    Attributes:
        q: 搜索关键词
        page: 页码（从1开始）
        page_size: 每页数量
        textbook_id: 限定教材ID（可选）
    """

    q: str = Field(..., min_length=1, description="搜索关键词")
    page: int = Field(1, ge=1, description="页码（从1开始）")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    textbook_id: int | None = Field(None, description="限定教材ID")


class SearchResultItem(BaseModel):
    """单个搜索结果

    Attributes:
        doc_id: 文档ID（章节ID）
        doc_type: 文档类型（chapter）
        title: 章节标题
        textbook_id: 教材ID
        textbook_title: 教材标题
        rank: 相关度排名（越小越相关）
    """

    doc_id: int = Field(..., description="文档ID")
    doc_type: str = Field(..., description="文档类型")
    title: str = Field(..., description="章节标题")
    textbook_id: int = Field(..., description="教材ID")
    textbook_title: str = Field(..., description="教材标题")
    rank: float = Field(..., description="相关度排名")


class SearchResponseData(BaseModel):
    """搜索响应数据

    Attributes:
        query: 原始查询字符串
        results: 搜索结果列表
        total: 总结果数
        page: 当前页码
        page_size: 每页数量
        total_pages: 总页数
    """

    query: str = Field(..., description="原始查询字符串")
    results: list[SearchResultItem] = Field(
        default_factory=list, description="搜索结果列表"
    )
    total: int = Field(..., description="总结果数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")


__all__ = [
    "SearchQueryParams",
    "SearchResultItem",
    "SearchResponseData",
]

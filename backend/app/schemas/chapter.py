"""章节相关的 Pydantic schemas"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.chapter import NodeType


class ChapterBase(BaseModel):
    """章节基础 schema"""

    title: str = Field(..., min_length=1, max_length=500)
    content: str | None = None


class ChapterCreate(ChapterBase):
    """创建章节 schema"""

    textbook_id: int
    parent_id: int | None = None
    order_index: int = 0
    node_type: NodeType = NodeType.FOLDER


class ChapterUpdate(BaseModel):
    """更新章节 schema"""

    title: str | None = Field(None, min_length=1, max_length=500)
    content: str | None = None
    parent_id: int | None = None


class ChapterTreeNode(BaseModel):
    """章节树节点 schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    level: int
    order_index: int
    node_type: NodeType
    has_content: bool
    parent_id: int | None = None
    children: list["ChapterTreeNode"] = []


class ChapterTreeResponse(BaseModel):
    """章节树响应"""

    textbook_id: int
    textbook_title: str
    chapters: list[ChapterTreeNode]


class ChapterNavigation(BaseModel):
    """章节导航"""

    prev: dict | None = None
    next: dict | None = None


class ChapterResponse(BaseModel):
    """章节响应 schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    textbook_id: int
    parent_id: int | None
    title: str
    slug: str
    level: int
    order_index: int
    node_type: NodeType
    content: str | None
    created_at: datetime
    updated_at: datetime
    navigation: ChapterNavigation | None = None


class ChapterReorderItem(BaseModel):
    """章节排序项"""

    id: int
    order_index: int
    parent_id: int | None = None


class ChapterReorderRequest(BaseModel):
    """章节排序请求"""

    textbook_id: int
    orders: list[ChapterReorderItem]


class SortPreviewRequest(BaseModel):
    """排序预览请求"""

    textbook_id: int
    selected_ids: list[int] | None = None


class OrderItem(BaseModel):
    """排序项

    用于标识章节或文件夹的排序信息。

    Attributes:
        id: 真实ID（int）或临时ID（str，如 "temp_folder_1"）
        type: 节点类型，"folder" 或 "article"
        folder_number: 文件夹编号（仅 folder 类型有）
        order_index: 排序索引
        parent_id: 父节点ID（真实ID或临时ID）
        is_new: 是否为新建节点
    """

    id: int | str
    type: str  # "folder" or "article"
    folder_number: int | None = None
    order_index: int
    parent_id: int | str | None = None
    is_new: bool = False


class SortPreviewResponse(BaseModel):
    """排序预览响应

    Attributes:
        preview_tree: 排序后的树结构
        changes_count: 变更数量
        folders_created: 将创建的文件夹列表
        orders: 排序项列表，供前端使用
    """

    preview_tree: list[dict]
    changes_count: int
    folders_created: list[str]
    orders: list[OrderItem] = []


class SortApplyRequest(BaseModel):
    """排序应用请求

    Attributes:
        textbook_id: 教材ID
        selected_ids: 选中的章节ID列表
        orders: 预计算的排序结果
        deleted_ids: 需要删除的章节ID列表
        deleted_folder_numbers: 需要删除的文件夹编号列表
    """

    textbook_id: int
    selected_ids: list[int] | None = None
    orders: list[OrderItem] | None = None
    deleted_ids: list[int] = []
    deleted_folder_numbers: list[int] = []


class SortUndoRequest(BaseModel):
    """排序撤回请求"""

    textbook_id: int


ChapterTreeNode.model_rebuild()

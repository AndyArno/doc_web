"""章节树构建工具函数

提供章节树结构构建相关的工具函数。
"""

from app.models.chapter import Chapter
from app.schemas.chapter import ChapterTreeNode


def build_chapter_tree(chapters: list[Chapter]) -> list[ChapterTreeNode]:
    """构建章节树结构

    将扁平的章节列表转换为三级树结构。

    Args:
        chapters: 章节列表

    Returns:
        树结构的章节列表
    """
    return _build_tree_recursive(chapters, parent_id=None)


def _build_tree_recursive(
    chapters: list[Chapter], parent_id: int | None
) -> list[ChapterTreeNode]:
    """递归构建章节树

    Args:
        chapters: 所有章节列表
        parent_id: 父章节 ID

    Returns:
        子树列表
    """
    nodes = []
    for chapter in chapters:
        if chapter.parent_id == parent_id:
            node = ChapterTreeNode(
                id=chapter.id,
                title=chapter.title,
                level=chapter.level,
                order_index=chapter.order_index,
                node_type=chapter.node_type,
                has_content=chapter.has_content,
                parent_id=chapter.parent_id,
                children=_build_tree_recursive(chapters, chapter.id),
            )
            nodes.append(node)

    nodes.sort(key=lambda x: x.order_index)
    return nodes


def flatten_chapters(chapters: list[Chapter]) -> list[Chapter]:
    """扁平化章节树

    将章节树按阅读顺序扁平化为一维列表。

    Args:
        chapters: 章节列表

    Returns:
        按顺序排列的章节列表
    """
    result = []
    root_chapters = [ch for ch in chapters if ch.parent_id is None]
    root_chapters.sort(key=lambda x: x.order_index)

    def add_with_children(chapter: Chapter):
        result.append(chapter)
        children = [ch for ch in chapters if ch.parent_id == chapter.id]
        children.sort(key=lambda x: x.order_index)
        for child in children:
            add_with_children(child)

    for chapter in root_chapters:
        add_with_children(chapter)

    return result

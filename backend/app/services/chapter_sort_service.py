"""章节排序服务模块

提供章节自动排序相关的服务函数。
"""

from typing import Optional

from sqlalchemy import select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.chapter import Chapter, NodeType
from app.models.chapter_tree_snapshot import ChapterTreeSnapshot
from app.models.user import User
from app.utils.chapter_sort import (
    extract_sort_key,
    parse_folder_number,
    parse_title_number,
)


# 最大章节层级
MAX_LEVEL = 6


async def match_folder(
    chapter_number: int, existing_folders: list[Chapter]
) -> Optional[Chapter]:
    """匹配现有文件夹

    根据章节编号在现有文件夹中查找匹配的父文件夹。

    Args:
        chapter_number: 章节主编号
        existing_folders: 根级别文件夹列表

    Returns:
        匹配的文件夹或 None
    """
    for folder in existing_folders:
        folder_number = parse_folder_number(folder.title)
        if folder_number == chapter_number:
            return folder
    return None


async def match_folder_by_number(
    folder_number: int, textbook_id: int, db: AsyncSession
) -> Optional[Chapter]:
    """根据文件夹编号查找文件夹

    Args:
        folder_number: 文件夹编号
        textbook_id: 教材 ID
        db: 数据库会话

    Returns:
        匹配的文件夹或 None
    """
    folders_result = await db.execute(
        select(Chapter).where(
            Chapter.textbook_id == textbook_id,
            Chapter.level == 1,
            Chapter.node_type == NodeType.FOLDER,
        )
    )
    folders = list(folders_result.scalars().all())
    return await match_folder(folder_number, folders)


async def create_folder_if_needed(
    chapter_number: int,
    textbook_id: int,
    db: AsyncSession,
    order_index: int = 0,
) -> Chapter:
    """自动创建文件夹

    如果指定编号的文件夹不存在，则创建新文件夹。

    Args:
        chapter_number: 章节主编号
        textbook_id: 教材 ID
        db: 数据库会话
        order_index: 排序索引

    Returns:
        创建的文件夹

    Raises:
        ValueError: 如果 chapter_number 无效
    """
    if chapter_number <= 0:
        raise ValueError(f"无效的章节编号: {chapter_number}")

    # 查询是否已存在同编号的根级别文件夹
    result = await db.execute(
        select(Chapter).where(
            Chapter.textbook_id == textbook_id,
            Chapter.level == 1,
            Chapter.node_type == NodeType.FOLDER,
        )
    )
    existing_folders = list(result.scalars().all())

    # 检查是否已存在匹配的文件夹
    existing_folder = await match_folder(chapter_number, existing_folders)
    if existing_folder:
        return existing_folder

    # 创建新文件夹
    folder = Chapter(
        textbook_id=textbook_id,
        parent_id=None,
        title=str(chapter_number),
        slug=str(chapter_number),
        level=1,
        order_index=order_index,
        node_type=NodeType.FOLDER,
        content=None,
    )

    db.add(folder)
    await db.flush()  # 获取 ID 但不提交事务
    await db.refresh(folder)

    return folder


async def calculate_sort_orders(
    chapters: list[Chapter],
    selected_ids: list[int] | None,
    db: AsyncSession,
) -> list[dict]:
    """计算章节排序顺序 - 使用 folder_number 代替真实文件夹ID

    核心排序算法：
    1. 筛选需要排序的章节（selected_ids 为 None 则全选）
    2. 提取所有章节编号（parse_title_number）
    3. 按编号分组：无编号组（排最前）→ 编号组（按 X.Y 排序）
    4. 对每组，匹配现有文件夹，或使用临时ID（temp_folder_N）
    5. 计算每个章节的新 parent_id 和 order_index
    6. 返回 orders 列表，包含 type, folder_number, is_new 字段

    Args:
        chapters: 教材的所有章节列表
        selected_ids: 选中的章节 ID 列表，None 表示全部章节
        db: 数据库会话

    Returns:
        排序后的 orders 列表，格式为：
        [{
            "id": int | str,  # 真实ID或临时ID（如 "temp_folder_1"）
            "type": str,  # "folder" or "article"
            "folder_number": int | None,  # 文件夹编号
            "order_index": int,
            "parent_id": int | str | None,
            "is_new": bool  # 是否新建
        }, ...]

    Raises:
        ValueError: 如果 chapters 为空
    """
    if not chapters:
        return []

    # 获取教材 ID
    textbook_id = chapters[0].textbook_id

    # 筛选需要排序的章节
    if selected_ids is not None:
        selected_set = set(selected_ids)
        chapters_to_sort = [ch for ch in chapters if ch.id in selected_set]
    else:
        chapters_to_sort = list(chapters)

    if not chapters_to_sort:
        return []

    # 获取现有的根级别文件夹
    result = await db.execute(
        select(Chapter).where(
            Chapter.textbook_id == textbook_id,
            Chapter.level == 1,
            Chapter.node_type == NodeType.FOLDER,
        )
    )
    existing_folders = list(result.scalars().all())

    # 按 extract_sort_key 排序
    def get_sort_key(chapter: Chapter) -> tuple:
        """获取排序键"""
        is_folder = chapter.node_type == NodeType.FOLDER
        return extract_sort_key(chapter.title, is_folder=is_folder)

    sorted_chapters = sorted(chapters_to_sort, key=get_sort_key)

    # 跟踪需要创建的文件夹编号
    folders_to_create: set[int] = set()
    orders: list[dict] = []

    # 用于跟踪每个文件夹内的 order_index
    folder_order_counters: dict[int | str, int] = {}  # folder_id -> next_order_index
    root_order_counter = 0  # 根级别顺序计数器

    # 用于跟踪已处理的无编号项
    unnumbered_root_order = 0
    unnumbered_in_folder_counters: dict[int, int] = {}  # folder_id -> counter

    for chapter in sorted_chapters:
        sort_key = get_sort_key(chapter)

        # 检查是否为无编号项 (key[0] == 0 表示无编号)
        if sort_key[0] == 0:
            # 无编号项排到最前
            if chapter.node_type == NodeType.FOLDER:
                # 无编号文件夹保持在根级别
                orders.append(
                    {
                        "id": chapter.id,
                        "type": "folder",
                        "folder_number": None,
                        "order_index": unnumbered_root_order,
                        "parent_id": None,
                        "is_new": False,
                    }
                )
                unnumbered_root_order += 1
                # 初始化该文件夹内的计数器
                folder_order_counters[chapter.id] = 0
            else:
                # 无编号文章 - 保持原有父级关系或放到根级别
                if chapter.parent_id is not None:
                    # 有父级，保持原样但更新顺序
                    if chapter.parent_id not in unnumbered_in_folder_counters:
                        unnumbered_in_folder_counters[chapter.parent_id] = 0
                    orders.append(
                        {
                            "id": chapter.id,
                            "type": "article",
                            "folder_number": None,
                            "order_index": unnumbered_in_folder_counters[
                                chapter.parent_id
                            ],
                            "parent_id": chapter.parent_id,
                            "is_new": False,
                        }
                    )
                    unnumbered_in_folder_counters[chapter.parent_id] += 1
                else:
                    # 无父级，放到根级别最前
                    orders.append(
                        {
                            "id": chapter.id,
                            "type": "article",
                            "folder_number": None,
                            "order_index": unnumbered_root_order,
                            "parent_id": None,
                            "is_new": False,
                        }
                    )
                    unnumbered_root_order += 1
        else:
            # 有编号项
            if chapter.node_type == NodeType.FOLDER:
                # 有编号文件夹 - 解析文件夹编号
                folder_number = parse_folder_number(chapter.title)
                if folder_number is not None:
                    # 文件夹在根级别
                    orders.append(
                        {
                            "id": chapter.id,
                            "type": "folder",
                            "folder_number": folder_number,
                            "order_index": root_order_counter,
                            "parent_id": None,
                            "is_new": False,
                        }
                    )
                    root_order_counter += 1
                    # 初始化该文件夹内的计数器
                    folder_order_counters[chapter.id] = 0
            else:
                # 有编号文章 - 需要放入对应文件夹
                numbers = parse_title_number(chapter.title)
                if numbers and len(numbers) >= 1:
                    # 获取主编号（第一级编号）
                    main_number = numbers[0]

                    # 查找现有文件夹
                    matched_folder = await match_folder(main_number, existing_folders)

                    if matched_folder:
                        # 使用现有文件夹
                        parent_id = matched_folder.id
                        folder_id_for_counter = matched_folder.id
                    else:
                        # 需要创建新文件夹（使用临时ID）
                        folders_to_create.add(main_number)
                        parent_id = f"temp_folder_{main_number}"
                        folder_id_for_counter = parent_id

                    # 初始化计数器
                    if folder_id_for_counter not in folder_order_counters:
                        folder_order_counters[folder_id_for_counter] = 0

                    orders.append(
                        {
                            "id": chapter.id,
                            "type": "article",
                            "folder_number": main_number,
                            "order_index": folder_order_counters[folder_id_for_counter],
                            "parent_id": parent_id,
                            "is_new": False,
                        }
                    )
                    folder_order_counters[folder_id_for_counter] += 1

    # 为需要创建的文件夹添加 orders 项
    for main_number in sorted(folders_to_create):
        folder_id = f"temp_folder_{main_number}"
        orders.append(
            {
                "id": folder_id,
                "type": "folder",
                "folder_number": main_number,
                "order_index": root_order_counter,
                "parent_id": None,
                "is_new": True,
            }
        )
        root_order_counter += 1

    return orders


async def preview_sort(
    textbook_id: int,
    selected_ids: list[int] | None,
    db: AsyncSession,
) -> dict:
    """返回排序预览

    计算排序结果但不修改数据库，返回预览数据。

    Args:
        textbook_id: 教材 ID
        selected_ids: 选中的章节 ID 列表，None 表示全部章节
        db: 数据库会话

    Returns:
        包含以下字段的字典：
        - preview_tree: 排序后的树结构
        - changes_count: 变更数量
        - folders_created: 将创建的文件夹列表
        - orders: 排序项列表，供前端使用

    Raises:
        AppException: 教材不存在时抛出 404 错误
    """
    from app.models.textbook import Textbook

    textbook_result = await db.execute(
        select(Textbook).where(Textbook.id == textbook_id)
    )
    textbook = textbook_result.scalar_one_or_none()

    if not textbook:
        raise AppException(code=404, message="教材不存在", data=None)

    chapters_result = await db.execute(
        select(Chapter).where(Chapter.textbook_id == textbook_id)
    )
    chapters = list(chapters_result.scalars().all())

    if not chapters:
        return {
            "preview_tree": [],
            "changes_count": 0,
            "folders_created": [],
            "orders": [],
        }

    original_state = {
        ch.id: {"order_index": ch.order_index, "parent_id": ch.parent_id}
        for ch in chapters
    }

    orders = await calculate_sort_orders(chapters, selected_ids, db)

    orders_map = {o["id"]: o for o in orders if isinstance(o["id"], int)}

    changes_count = 0
    folders_created = []

    for order in orders:
        ch_id = order["id"]
        if isinstance(ch_id, int) and ch_id in original_state:
            orig = original_state[ch_id]
            if (
                orig["order_index"] != order["order_index"]
                or orig["parent_id"] != order["parent_id"]
            ):
                changes_count += 1

    for order in orders:
        if order.get("is_new") and order.get("type") == "folder":
            folder_number = order.get("folder_number")
            if folder_number is not None:
                folders_created.append(str(folder_number))

    preview_tree = _build_preview_tree(chapters, orders)

    return {
        "preview_tree": preview_tree,
        "changes_count": changes_count,
        "folders_created": folders_created,
        "orders": orders,
    }


def _build_preview_tree(chapters: list[Chapter], orders: list[dict]) -> list[dict]:
    """构建预览树结构

    Args:
        chapters: 章节列表
        orders: 排序结果（包含临时ID的文件夹）

    Returns:
        树形结构列表
    """
    orders_map = {o["id"]: o for o in orders}
    chapters_map = {ch.id: ch for ch in chapters}

    preview_nodes = {}

    # 先处理所有真实章节
    for ch in chapters:
        order = orders_map.get(ch.id)
        if order:
            preview_nodes[ch.id] = {
                "id": ch.id,
                "title": ch.title,
                "node_type": ch.node_type.value,
                "level": ch.level,
                "order_index": order["order_index"],
                "parent_id": order["parent_id"],
                "is_new": order.get("is_new", False),
                "folder_number": order.get("folder_number"),
                "children": [],
            }
        else:
            preview_nodes[ch.id] = {
                "id": ch.id,
                "title": ch.title,
                "node_type": ch.node_type.value,
                "level": ch.level,
                "order_index": ch.order_index,
                "parent_id": ch.parent_id,
                "is_new": False,
                "folder_number": None,
                "children": [],
            }

    # 处理临时文件夹（is_new=True 的文件夹）
    for order in orders:
        if order.get("is_new") and order.get("type") == "folder":
            folder_id = order["id"]
            folder_number = order.get("folder_number")
            preview_nodes[folder_id] = {
                "id": folder_id,
                "title": str(folder_number) if folder_number else folder_id,
                "node_type": "folder",
                "level": 1,
                "order_index": order["order_index"],
                "parent_id": None,
                "is_new": True,
                "folder_number": folder_number,
                "children": [],
            }

    # 构建树结构
    root_nodes = []
    for node in preview_nodes.values():
        parent_id = node["parent_id"]
        if parent_id is None:
            root_nodes.append(node)
        elif parent_id in preview_nodes:
            preview_nodes[parent_id]["children"].append(node)

    def sort_children(nodes: list[dict]) -> list[dict]:
        nodes.sort(key=lambda x: x["order_index"])
        for node in nodes:
            if node["children"]:
                node["children"] = sort_children(node["children"])
        return nodes

    return sort_children(root_nodes)


def _get_descendant_ids(parent_id: int, chapters_map: dict) -> set[int]:
    """递归收集所有子孙节点 ID（用于级联删除前的清理）

    当通过 bulk delete 删除父节点时，PostgreSQL 的 ON DELETE CASCADE
    会级联删除子孙节点，但 ORM session 仍持有这些节点的 Python 对象。
    此函数遍历内存中的 chapters_map 找出所有后代，确保后续操作不会
    修改已不存在的行。

    Args:
        parent_id: 父节点 ID
        chapters_map: 章节 ID → Chapter 对象的映射

    Returns:
        所有子孙节点的 ID 集合（不含 parent_id 本身）
    """
    result: set[int] = set()
    for ch_id, ch in chapters_map.items():
        if ch.parent_id == parent_id:
            result.add(ch_id)
            result.update(_get_descendant_ids(ch_id, chapters_map))
    return result


async def apply_sort(
    textbook_id: int,
    selected_ids: list[int] | None,
    orders: list[dict] | None,
    db: AsyncSession,
    user: User,
    *,
    deleted_ids: list[int] | None = None,
    deleted_folder_numbers: list[int] | None = None,
) -> dict:
    """应用排序并保存快照

    执行排序操作并保存快照以支持撤回。

    Args:
        textbook_id: 教材 ID
        selected_ids: 选中的章节 ID 列表，None 表示全部章节
        orders: 预计算的排序结果，None 则自动计算
        db: 数据库会话
        user: 当前用户
        deleted_ids: 需要删除的章节 ID 列表
        deleted_folder_numbers: 需要删除的文件夹编号列表

    Returns:
        包含以下字段的字典：
        - success: 是否成功
        - changes_count: 变更数量
        - folders_created: 新建的文件夹 ID 列表

    Raises:
        AppException: 教材不存在时抛出 404 错误
    """
    result = await db.execute(select(Chapter).where(Chapter.textbook_id == textbook_id))
    chapters = list(result.scalars().all())
    chapters_map = {ch.id: ch for ch in chapters}

    # 保存快照用于撤回（在删除之前）
    snapshot_data = [
        {
            "id": ch.id,
            "order_index": ch.order_index,
            "parent_id": ch.parent_id,
        }
        for ch in chapters
    ]

    # 如果没有传入 orders，则自动计算
    if orders is None:
        orders = await calculate_sort_orders(chapters, selected_ids, db)

    # 将 OrderItem 模型转换为字典（统一处理）
    def order_to_dict(order):
        """将 OrderItem 模型或字典转换为字典"""
        if hasattr(order, "model_dump"):
            return order.model_dump()
        return order

    orders = [order_to_dict(o) for o in orders]

    # 处理删除章节
    if deleted_ids:
        await db.execute(delete(Chapter).where(Chapter.id.in_(deleted_ids)))
        # 从 chapters_map 中移除已删除的章节
        for deleted_id in deleted_ids:
            chapters_map.pop(deleted_id, None)

    # 处理删除文件夹
    if deleted_folder_numbers:
        for folder_number in deleted_folder_numbers:
            folder = await match_folder_by_number(folder_number, textbook_id, db)
            if folder:
                # 收集级联删除的子孙节点（ON DELETE CASCADE 会在 DB 层删除它们，
                # 但 ORM session 仍持有这些对象，后续修改会导致 StaleDataError）
                cascade_ids = _get_descendant_ids(folder.id, chapters_map)
                await db.execute(delete(Chapter).where(Chapter.id == folder.id))
                chapters_map.pop(folder.id, None)
                for cid in cascade_ids:
                    chapters_map.pop(cid, None)

    # 创建文件夹并建立映射
    folder_id_map = {}  # {"temp_folder_1": 465, ...}

    for order in orders:
        if order.get("type") == "folder" and order.get("is_new"):
            folder_number = order.get("folder_number")
            if folder_number:
                # 创建真实文件夹
                folder = Chapter(
                    textbook_id=textbook_id,
                    title=str(folder_number),
                    slug=str(folder_number),
                    level=1,
                    order_index=order["order_index"],
                    node_type=NodeType.FOLDER,
                    content=None,
                    parent_id=None,
                )
                db.add(folder)
                await db.flush()
                await db.refresh(folder)

                # 记录映射
                folder_id_map[order["id"]] = folder.id

    # 更新文章的 parent_id 和 order_index
    changes_count = 0

    for order in orders:
        if order.get("type") == "article":
            ch_id = order["id"]
            if isinstance(ch_id, int) and ch_id in chapters_map:
                chapter = chapters_map[ch_id]
                old_order = chapter.order_index
                old_parent = chapter.parent_id

                # 映射临时ID到真实ID
                parent_id = order.get("parent_id")
                if parent_id and isinstance(parent_id, str):
                    parent_id = folder_id_map.get(parent_id)

                chapter.order_index = order["order_index"]
                chapter.parent_id = parent_id

                # 更新 level
                if parent_id is None:
                    chapter.level = 1
                elif parent_id in chapters_map:
                    new_level = chapters_map[parent_id].level + 1
                    if new_level > MAX_LEVEL:
                        raise AppException(
                            code=400,
                            message=f"章节层级不能超过 {MAX_LEVEL} 层",
                            data=None,
                        )
                    chapter.level = new_level

                if old_order != order["order_index"] or old_parent != parent_id:
                    changes_count += 1

    # 创建快照
    snapshot = ChapterTreeSnapshot(
        textbook_id=textbook_id,
        snapshot_data=snapshot_data,
        operation_type="sort",
        is_active=True,
    )
    db.add(snapshot)
    await db.flush()

    await db.commit()

    return {
        "success": True,
        "changes_count": changes_count,
        "folders_created": list(folder_id_map.values()),
    }


async def undo_sort(textbook_id: int, db: AsyncSession) -> bool:
    """撤回最近一次排序

    从最近的活跃快照恢复章节顺序。

    Args:
        textbook_id: 教材 ID
        db: 数据库会话

    Returns:
        是否成功撤回

    Raises:
        AppException: 没有可撤回的快照时抛出 404 错误
    """
    result = await db.execute(
        select(ChapterTreeSnapshot)
        .where(
            ChapterTreeSnapshot.textbook_id == textbook_id,
            ChapterTreeSnapshot.is_active == True,
        )
        .order_by(desc(ChapterTreeSnapshot.created_at))
        .limit(1)
    )
    snapshot = result.scalar_one_or_none()

    if not snapshot:
        raise AppException(
            code=404,
            message="没有可撤回的排序操作",
            data=None,
        )

    chapters_result = await db.execute(
        select(Chapter).where(Chapter.textbook_id == textbook_id)
    )
    chapters_map = {ch.id: ch for ch in chapters_result.scalars().all()}

    snapshot_data = snapshot.snapshot_data
    if isinstance(snapshot_data, list):
        for item in snapshot_data:
            ch_id = item["id"]
            if ch_id in chapters_map:
                chapter = chapters_map[ch_id]
                chapter.order_index = item["order_index"]
                chapter.parent_id = item["parent_id"]

                if item["parent_id"] is None:
                    chapter.level = 1
                elif item["parent_id"] in chapters_map:
                    parent = chapters_map[item["parent_id"]]
                    new_level = parent.level + 1
                    if new_level > MAX_LEVEL:
                        raise AppException(
                            code=400,
                            message=f"章节层级不能超过 {MAX_LEVEL} 层",
                            data=None,
                        )
                    chapter.level = new_level

    snapshot.is_active = False

    await db.commit()

    return True


__all__ = [
    "MAX_LEVEL",
    "match_folder",
    "create_folder_if_needed",
    "calculate_sort_orders",
    "preview_sort",
    "apply_sort",
    "undo_sort",
]

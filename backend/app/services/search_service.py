"""
搜索服务模块

提供基于 pg_jieba 和 tsvector 的全文搜索功能。

搜索流程：
1. 索引时：使用 pg_jieba 的 jiebacfg 配置进行中文分词，存入 tsvector 列
2. 搜索时：对查询词使用 to_tsquery 进行搜索
"""

import logging
from dataclasses import dataclass
from typing import Optional

import jieba
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def _is_postgresql(session: AsyncSession) -> bool:
    """检查数据库是否为 PostgreSQL（支持全文搜索）。

    搜索索引依赖 pg_jieba 扩展的 to_tsvector 函数，
    仅在 PostgreSQL 上可用。SQLite 等数据库自动跳过索引操作。
    """
    try:
        bind = session.get_bind()
        dialect_name = getattr(bind, "dialect", None)
        if dialect_name:
            return getattr(dialect_name, "name", "") == "postgresql"
    except Exception:
        pass
    return False


@dataclass
class SearchResult:
    """搜索结果项

    Attributes:
        doc_id: 文档 ID（章节 ID）
        doc_type: 文档类型（chapter）
        title: 章节标题
        rank: 相关度排名（越小越相关）
        textbook_id: 教材 ID
        textbook_title: 教材标题
    """

    doc_id: int
    doc_type: str
    title: str
    rank: float
    textbook_id: int
    textbook_title: str


@dataclass
class SearchResponse:
    """搜索响应

    Attributes:
        query: 原始查询字符串
        results: 搜索结果列表
        total: 总结果数
    """

    query: str
    results: list[SearchResult]
    total: int


def _segment_text(text: str) -> str:
    """对文本进行分词

    使用 jieba 进行中文分词，将结果用空格拼接。
    用于生成搜索查询。

    Args:
        text: 待分词的文本

    Returns:
        分词后用空格拼接的字符串
    """
    if not text:
        return ""

    # jieba.lcut 返回分词列表，用空格拼接
    words = jieba.lcut(text)
    return " ".join(words)


async def ensure_search_table(session: AsyncSession) -> None:
    """确保搜索索引表存在

    创建 content_search_idx 表，用于存储章节内容的 tsvector 索引。

    Args:
        session: 数据库会话
    """
    if not _is_postgresql(session):
        return
    # 创建搜索索引表
    sql = text("""
        CREATE TABLE IF NOT EXISTS content_search_idx (
            id SERIAL PRIMARY KEY,
            doc_id INTEGER NOT NULL,
            doc_type VARCHAR(50) NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            textbook_id INTEGER NOT NULL,
            textbook_title TEXT NOT NULL,
            search_vector TSVECTOR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await session.execute(sql)
    
    # 创建 GIN 索引加速搜索
    gin_sql = text("""
        CREATE INDEX IF NOT EXISTS idx_content_search_vector 
        ON content_search_idx USING GIN(search_vector)
    """)
    await session.execute(gin_sql)
    
    # 创建 doc_id 索引
    doc_idx_sql = text("""
        CREATE INDEX IF NOT EXISTS idx_content_search_doc_id 
        ON content_search_idx(doc_id, doc_type)
    """)
    await session.execute(doc_idx_sql)
    
    # 创建 textbook_id 索引
    tb_idx_sql = text("""
        CREATE INDEX IF NOT EXISTS idx_content_search_textbook_id 
        ON content_search_idx(textbook_id)
    """)
    await session.execute(tb_idx_sql)
    
    await session.commit()
    logger.info("搜索索引表 content_search_idx 已创建或已存在")


async def index_chapter(
    session: AsyncSession,
    chapter_id: int,
    title: str,
    content: Optional[str],
    textbook_id: int,
    textbook_title: str,
) -> None:
    """索引单个章节

    将章节内容存入搜索索引表，并生成 tsvector。

    Args:
        session: 数据库会话
        chapter_id: 章节 ID
        title: 章节标题
        content: 章节内容
        textbook_id: 教材 ID
        textbook_title: 教材标题
    """
    if not _is_postgresql(session):
        return
    # 插入索引，使用 pg_jieba 的 jiebacfg 配置生成 tsvector
    sql = text("""
        INSERT INTO content_search_idx (doc_id, doc_type, title, content, textbook_id, textbook_title, search_vector)
        VALUES (:doc_id, 'chapter', :title, :content, :textbook_id, :textbook_title,
                to_tsvector('jiebacfg', COALESCE(:title, '') || ' ' || COALESCE(:content, '')))
    """)
    await session.execute(
        sql,
        {
            "doc_id": chapter_id,
            "title": title,
            "content": content or "",
            "textbook_id": textbook_id,
            "textbook_title": textbook_title,
        },
    )
    await session.commit()
    logger.debug(f"已索引章节 {chapter_id}: {title}")


async def update_chapter_index(
    session: AsyncSession,
    chapter_id: int,
    title: str,
    content: Optional[str],
    textbook_id: int,
    textbook_title: str,
) -> None:
    """更新章节索引

    先删除旧索引，再插入新索引。

    Args:
        session: 数据库会话
        chapter_id: 章节 ID
        title: 章节标题
        content: 章节内容
        textbook_id: 教材 ID
        textbook_title: 教材标题
    """
    if not _is_postgresql(session):
        return
    # 删除旧索引
    await delete_chapter_index(session, chapter_id)

    # 插入新索引
    await index_chapter(
        session=session,
        chapter_id=chapter_id,
        title=title,
        content=content,
        textbook_id=textbook_id,
        textbook_title=textbook_title,
    )
    logger.debug(f"已更新章节索引 {chapter_id}")


async def delete_chapter_index(session: AsyncSession, chapter_id: int) -> None:
    """删除章节索引

    Args:
        session: 数据库会话
        chapter_id: 章节 ID
    """
    if not _is_postgresql(session):
        return
    sql = text("""
        DELETE FROM content_search_idx WHERE doc_id = :doc_id AND doc_type = 'chapter'
    """)
    await session.execute(sql, {"doc_id": chapter_id})
    await session.commit()
    logger.debug(f"已删除章节索引 {chapter_id}")


async def delete_textbook_indexes(session: AsyncSession, textbook_id: int) -> int:
    """删除教材的所有搜索索引

    按 textbook_id 批量删除 content_search_idx 表中的记录。

    Args:
        session: 数据库会话
        textbook_id: 教材 ID

    Returns:
        删除的记录数
    """
    if not _is_postgresql(session):
        return 0
    sql = text("""
        DELETE FROM content_search_idx WHERE textbook_id = :textbook_id
    """)
    result = await session.execute(sql, {"textbook_id": textbook_id})
    await session.commit()
    deleted_count = result.rowcount
    logger.debug(f"已删除教材 {textbook_id} 的 {deleted_count} 条搜索索引")
    return deleted_count


async def search_chapters(
    session: AsyncSession,
    query: str,
    textbook_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
) -> SearchResponse:
    """搜索章节内容

    对查询词进行分词后，在 tsvector 索引中搜索。

    Args:
        session: 数据库会话
        query: 搜索关键词
        textbook_id: 限定教材 ID（可选）
        limit: 返回结果数量限制
        offset: 偏移量（用于分页）

    Returns:
        搜索响应对象
    """
    if not _is_postgresql(session):
        return SearchResponse(items=[], total=0, page=1, page_size=limit)
    if not query or not query.strip():
        return SearchResponse(query=query, results=[], total=0)

    # 对查询词进行分词
    segmented_query = _segment_text(query.strip())
    
    # 将分词结果转换为 tsquery 格式（用 & 连接）
    query_words = segmented_query.split()
    tsquery_str = " & ".join(query_words)

    # 构建 SQL 查询
    if textbook_id:
        # 限定教材搜索
        sql = text("""
            SELECT
                doc_id,
                doc_type,
                title,
                textbook_id,
                textbook_title,
                ts_rank(search_vector, to_tsquery('jiebacfg', :query)) as rank
            FROM content_search_idx
            WHERE search_vector @@ to_tsquery('jiebacfg', :query)
              AND textbook_id = :textbook_id
            ORDER BY rank DESC
            LIMIT :limit OFFSET :offset
        """)
        count_sql = text("""
            SELECT COUNT(*) as total
            FROM content_search_idx
            WHERE search_vector @@ to_tsquery('jiebacfg', :query)
              AND textbook_id = :textbook_id
        """)
        params = {
            "query": tsquery_str,
            "textbook_id": textbook_id,
            "limit": limit,
            "offset": offset,
        }
    else:
        # 全局搜索
        sql = text("""
            SELECT
                doc_id,
                doc_type,
                title,
                textbook_id,
                textbook_title,
                ts_rank(search_vector, to_tsquery('jiebacfg', :query)) as rank
            FROM content_search_idx
            WHERE search_vector @@ to_tsquery('jiebacfg', :query)
            ORDER BY rank DESC
            LIMIT :limit OFFSET :offset
        """)
        count_sql = text("""
            SELECT COUNT(*) as total
            FROM content_search_idx
            WHERE search_vector @@ to_tsquery('jiebacfg', :query)
        """)
        params = {
            "query": tsquery_str,
            "limit": limit,
            "offset": offset,
        }

    # 执行搜索
    result = await session.execute(sql, params)
    rows = result.fetchall()

    # 获取总数
    count_result = await session.execute(count_sql, params)
    total = count_result.scalar() or 0

    # 构建结果列表
    results = []
    for row in rows:
        results.append(
            SearchResult(
                doc_id=row.doc_id,
                doc_type=row.doc_type,
                title=row.title,
                rank=row.rank,
                textbook_id=row.textbook_id,
                textbook_title=row.textbook_title,
            )
        )

    logger.debug(f"搜索 '{query}' 返回 {len(results)} 条结果（共 {total} 条）")

    return SearchResponse(query=query, results=results, total=total)


async def rebuild_all_indexes(session: AsyncSession) -> int:
    """重建所有章节索引

    从 chapters 表重新构建搜索索引。

    Args:
        session: 数据库会话

    Returns:
        索引的章节数量
    """
    if not _is_postgresql(session):
        return 0
    # 清空现有索引
    sql = text("DELETE FROM content_search_idx")
    await session.execute(sql)

    # 查询所有章节及其教材信息
    chapters_sql = text("""
        SELECT
            c.id as chapter_id,
            c.title,
            c.content,
            c.textbook_id,
            t.title as textbook_title
        FROM chapters c
        JOIN textbooks t ON c.textbook_id = t.id
    """)
    result = await session.execute(chapters_sql)
    chapters = result.fetchall()

    # 批量插入章节索引
    count = 0
    for chapter in chapters:
        insert_sql = text("""
            INSERT INTO content_search_idx (doc_id, doc_type, title, content, textbook_id, textbook_title, search_vector)
            VALUES (:doc_id, 'chapter', :title, :content, :textbook_id, :textbook_title,
                    to_tsvector('jiebacfg', COALESCE(:title, '') || ' ' || COALESCE(:content, '')))
        """)
        await session.execute(
            insert_sql,
            {
                "doc_id": chapter.chapter_id,
                "title": chapter.title,
                "content": chapter.content or "",
                "textbook_id": chapter.textbook_id,
                "textbook_title": chapter.textbook_title,
            },
        )
        count += 1

    await session.commit()
    logger.info(f"已重建 {count} 个章节的索引")
    return count


# 兼容性别名
ensure_fts_table = ensure_search_table


__all__ = [
    "SearchResult",
    "SearchResponse",
    "ensure_search_table",
    "ensure_fts_table",
    "index_chapter",
    "update_chapter_index",
    "delete_chapter_index",
    "delete_textbook_indexes",
    "search_chapters",
    "rebuild_all_indexes",
]

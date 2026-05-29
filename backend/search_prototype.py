
# ============================================================
# 中文搜索服务原型代码（SQLite FTS5 + jieba）
# ============================================================

import sqlite3
import jieba
from typing import List, Tuple
from contextlib import contextmanager


class ChineseSearchService:
    """中文搜索服务原型"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_jieba()
    
    def _init_jieba(self):
        """初始化jieba分词器"""
        # 可以加载自定义词典
        # jieba.load_userdict("custom_dict.txt")
        pass
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def create_fts_index(self):
        """创建FTS5索引"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS content_search_idx
                USING fts5(
                    doc_id,
                    doc_type,  -- 'chapter', 'section', 'subsection'
                    title,
                    content,
                    tokenize='unicode61'
                )
            """)
            conn.commit()
    
    def index_document(self, doc_id: int, doc_type: str, title: str, content: str):
        """索引单个文档"""
        # jieba分词
        title_seg = ' '.join(jieba.lcut(title))
        content_seg = ' '.join(jieba.lcut(content))
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO content_search_idx (doc_id, doc_type, title, content)
                VALUES (?, ?, ?, ?)
                """,
                (doc_id, doc_type, title_seg, content_seg)
            )
            conn.commit()
    
    def search(self, query: str, doc_type: str = None, limit: int = 20) -> List[Tuple]:
        """搜索文档"""
        # 分词查询
        query_seg = ' '.join(jieba.lcut(query))
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if doc_type:
                sql = """
                    SELECT doc_id, doc_type, title, rank
                    FROM content_search_idx
                    WHERE content_search_idx MATCH ? AND doc_type = ?
                    ORDER BY rank
                    LIMIT ?
                """
                cursor.execute(sql, (query_seg, doc_type, limit))
            else:
                sql = """
                    SELECT doc_id, doc_type, title, rank
                    FROM content_search_idx
                    WHERE content_search_idx MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """
                cursor.execute(sql, (query_seg, limit))
            
            return cursor.fetchall()
    
    def delete_document(self, doc_id: int):
        """删除文档索引"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM content_search_idx WHERE doc_id = ?",
                (doc_id,)
            )
            conn.commit()
    
    def update_document(self, doc_id: int, doc_type: str, title: str, content: str):
        """更新文档索引"""
        self.delete_document(doc_id)
        self.index_document(doc_id, doc_type, title, content)


# 使用示例
if __name__ == "__main__":
    search_service = ChineseSearchService("search.db")
    search_service.create_fts_index()
    
    # 索引文档
    search_service.index_document(
        doc_id=1,
        doc_type="chapter",
        title="ROS入门教程",
        content="ROS机器人操作系统是一个用于编写机器人软件的灵活框架"
    )
    
    # 搜索
    results = search_service.search("如何安装ROS")
    print(results)

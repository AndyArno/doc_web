#!/usr/bin/env python3
"""
SQLite 到 PostgreSQL 数据迁移脚本

按外键依赖顺序迁移数据：
users → textbooks → chapters → user_textbook_permissions → chapter_versions → media → audit_logs
"""

import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

import asyncpg

# 配置
SQLITE_DB_PATH = Path(__file__).parent.parent / "app.db"
PG_DSN = "postgresql://postgres:postgres@localhost:5432/document_web"


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """解析 SQLite 日期时间字符串"""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


async def migrate():
    """执行迁移"""
    print(f"开始迁移: {SQLITE_DB_PATH} → {PG_DSN}")
    
    # 连接数据库
    sqlite_conn = sqlite3.connect(str(SQLITE_DB_PATH))
    sqlite_conn.row_factory = sqlite3.Row
    pg_conn = await asyncpg.connect(PG_DSN)
    
    try:
        # 按外键依赖顺序迁移
        await migrate_users(sqlite_conn, pg_conn)
        await migrate_textbooks(sqlite_conn, pg_conn)
        await migrate_chapters(sqlite_conn, pg_conn)
        await migrate_permissions(sqlite_conn, pg_conn)
        await migrate_chapter_versions(sqlite_conn, pg_conn)
        await migrate_media(sqlite_conn, pg_conn)
        await migrate_audit_logs(sqlite_conn, pg_conn)
        
        # 重置序列
        await reset_sequences(pg_conn)
        
        print("\n✓ 迁移完成！")
        
        # 验证行数
        await verify_counts(sqlite_conn, pg_conn)
        
    finally:
        sqlite_conn.close()
        await pg_conn.close()


async def migrate_users(sqlite_conn, pg_conn):
    """迁移用户表"""
    cursor = sqlite_conn.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    
    count = 0
    for row in rows:
        try:
            await pg_conn.execute("""
                INSERT INTO users (id, username, email, hashed_password, role, is_active, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (id) DO NOTHING
            """, row['id'], row['username'], row['email'], row['hashed_password'],
                row['role'], bool(row['is_active']), 
                parse_datetime(row['created_at']), parse_datetime(row['updated_at']))
            count += 1
        except Exception as e:
            print(f"    跳过用户 {row['id']}: {e}")
    
    print(f"  users: {count} 行")


async def migrate_textbooks(sqlite_conn, pg_conn):
    """迁移教材表"""
    cursor = sqlite_conn.execute("SELECT * FROM textbooks")
    rows = cursor.fetchall()
    
    count = 0
    for row in rows:
        try:
            await pg_conn.execute("""
                INSERT INTO textbooks (id, title, description, cover_image, slug, is_published, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (id) DO NOTHING
            """, row['id'], row['title'], row['description'], row['cover_image'],
                row['slug'], bool(row['is_published']), 
                parse_datetime(row['created_at']), parse_datetime(row['updated_at']))
            count += 1
        except Exception as e:
            print(f"    跳过教材 {row['id']}: {e}")
    
    print(f"  textbooks: {count} 行")


async def migrate_chapters(sqlite_conn, pg_conn):
    """迁移章节表（处理自关联 FK）"""
    cursor = sqlite_conn.execute("SELECT * FROM chapters ORDER BY level, order_index")
    rows = cursor.fetchall()
    
    count = 0
    for row in rows:
        try:
            await pg_conn.execute("""
                INSERT INTO chapters (id, textbook_id, parent_id, title, slug, level, order_index, content, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (id) DO NOTHING
            """, row['id'], row['textbook_id'], row['parent_id'], row['title'],
                row['slug'], row['level'], row['order_index'], row['content'],
                parse_datetime(row['created_at']), parse_datetime(row['updated_at']))
            count += 1
        except Exception as e:
            print(f"    跳过章节 {row['id']}: {e}")
    
    print(f"  chapters: {count} 行")


async def migrate_permissions(sqlite_conn, pg_conn):
    """迁移权限表"""
    cursor = sqlite_conn.execute("SELECT * FROM user_textbook_permissions")
    rows = cursor.fetchall()
    
    count = 0
    for row in rows:
        try:
            await pg_conn.execute("""
                INSERT INTO user_textbook_permissions (id, user_id, textbook_id, can_edit, can_create, can_delete, can_manage_users, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO NOTHING
            """, row['id'], row['user_id'], row['textbook_id'],
                bool(row['can_edit']), bool(row['can_create']), bool(row['can_delete']), bool(row['can_manage_users']),
                parse_datetime(row['created_at']), parse_datetime(row['updated_at']))
            count += 1
        except Exception as e:
            print(f"    跳过权限 {row['id']}: {e}")
    
    print(f"  user_textbook_permissions: {count} 行")


async def migrate_chapter_versions(sqlite_conn, pg_conn):
    """迁移章节版本表"""
    cursor = sqlite_conn.execute("SELECT * FROM chapter_versions")
    rows = cursor.fetchall()
    
    count = 0
    for row in rows:
        try:
            await pg_conn.execute("""
                INSERT INTO chapter_versions (id, chapter_id, content, version_num, created_by, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO NOTHING
            """, row['id'], row['chapter_id'], row['content'], row['version_num'],
                row['created_by'], parse_datetime(row['created_at']), parse_datetime(row['updated_at']))
            count += 1
        except Exception as e:
            print(f"    跳过版本 {row['id']}: {e}")
    
    print(f"  chapter_versions: {count} 行")


async def migrate_media(sqlite_conn, pg_conn):
    """迁移媒体表"""
    cursor = sqlite_conn.execute("SELECT * FROM media")
    rows = cursor.fetchall()
    
    count = 0
    skipped = 0
    for row in rows:
        try:
            deleted_at = parse_datetime(row['deleted_at']) if row['is_deleted'] else None
            await pg_conn.execute("""
                INSERT INTO media (id, textbook_id, chapter_id, filename, original_name, file_path, file_size, file_type, is_deleted, deleted_at, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (id) DO NOTHING
            """, row['id'], row['textbook_id'], row['chapter_id'], row['filename'],
                row['original_name'], row['file_path'], row['file_size'], row['file_type'],
                bool(row['is_deleted']), deleted_at, 
                parse_datetime(row['created_at']), parse_datetime(row['updated_at']))
            count += 1
        except Exception as e:
            skipped += 1
    
    print(f"  media: {count} 行 (跳过 {skipped} 行无效外键)")


async def migrate_audit_logs(sqlite_conn, pg_conn):
    """迁移审计日志表"""
    cursor = sqlite_conn.execute("SELECT * FROM audit_logs")
    rows = cursor.fetchall()
    
    count = 0
    for row in rows:
        try:
            details = None
            if row['details']:
                try:
                    details = json.loads(row['details']) if isinstance(row['details'], str) else row['details']
                except (json.JSONDecodeError, TypeError):
                    details = None
            
            await pg_conn.execute("""
                INSERT INTO audit_logs (id, action, target_user_id, operator_id, details, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (id) DO NOTHING
            """, row['id'], row['action'], row['target_user_id'], row['operator_id'],
                json.dumps(details) if details else None, parse_datetime(row['created_at']))
            count += 1
        except Exception as e:
            print(f"    跳过审计日志 {row['id']}: {e}")
    
    print(f"  audit_logs: {count} 行")


async def reset_sequences(pg_conn):
    """重置 PostgreSQL 自增序列"""
    tables = ['users', 'textbooks', 'chapters', 'user_textbook_permissions', 
              'chapter_versions', 'media', 'audit_logs']
    
    for table in tables:
        await pg_conn.execute(f"""
            SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1))
            FROM {table}
        """)
    
    print("  序列已重置")


async def verify_counts(sqlite_conn, pg_conn):
    """验证迁移后的行数"""
    tables = ['users', 'textbooks', 'chapters', 'user_textbook_permissions',
              'chapter_versions', 'media', 'audit_logs']
    
    print("\n验证行数:")
    print("-" * 50)
    
    for table in tables:
        sqlite_count = sqlite_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        pg_count = await pg_conn.fetchval(f"SELECT COUNT(*) FROM {table}")
        
        print(f"  {table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")
    
    print("-" * 50)


if __name__ == "__main__":
    asyncio.run(migrate())

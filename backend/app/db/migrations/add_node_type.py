"""
添加 node_type 字段迁移脚本

为 chapters 表添加 node_type 列，并根据 content 是否为空设置值：
- 有内容（content IS NOT NULL AND content != ''）→ 'article'
- 无内容（content IS NULL OR content = ''）→ 'folder'

使用方法:
    cd backend && uv run python -m app.db.migrations.add_node_type
    cd backend && uv run python -m app.db.migrations.add_node_type --rollback

特性:
- 幂等性：重复执行不会报错
- 支持回滚
- 兼容 PostgreSQL 和 SQLite
"""

import argparse
import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal, engine


async def column_exists(
    session: AsyncSession, table_name: str, column_name: str
) -> bool:
    """检查列是否存在（兼容 PostgreSQL 和 SQLite）

    Args:
        session: 数据库会话
        table_name: 表名
        column_name: 列名

    Returns:
        列是否存在
    """
    settings = get_settings()
    db_url = settings.DATABASE_URL

    if "sqlite" in db_url.lower():
        # SQLite: 查询 pragma_table_info
        result = await session.execute(
            text("SELECT name FROM pragma_table_info(:table) WHERE name = :column"),
            {"table": table_name, "column": column_name},
        )
    else:
        # PostgreSQL: 查询 information_schema
        result = await session.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = :table AND column_name = :column
                """
            ),
            {"table": table_name, "column": column_name},
        )

    return result.fetchone() is not None


async def migrate() -> None:
    """执行迁移：添加 node_type 列并设置初始值"""
    print("开始迁移: 添加 node_type 字段...")
    print()

    settings = get_settings()
    db_url = settings.DATABASE_URL

    async with AsyncSessionLocal() as session:
        # 1. 检查列是否已存在
        if await column_exists(session, "chapters", "node_type"):
            print("✓ node_type 列已存在，跳过迁移")
            return

        # 2. 添加 node_type 列
        print("添加 node_type 列...")

        if "sqlite" in db_url.lower():
            # SQLite 语法
            await session.execute(
                text(
                    """
                    ALTER TABLE chapters
                    ADD COLUMN node_type VARCHAR(10) NOT NULL DEFAULT 'folder'
                    """
                )
            )
        else:
            # PostgreSQL 语法：使用枚举类型
            # 先创建枚举类型（如果不存在）
            await session.execute(
                text(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'nodetype') THEN
                            CREATE TYPE nodetype AS ENUM ('folder', 'article');
                        END IF;
                    END$$;
                    """
                )
            )
            await session.execute(
                text(
                    """
                    ALTER TABLE chapters
                    ADD COLUMN node_type nodetype NOT NULL DEFAULT 'folder'
                    """
                )
            )

        await session.commit()
        print("✓ node_type 列已添加")

        # 3. 根据 content 更新 node_type 值
        print("更新现有数据的 node_type 值...")

        result = await session.execute(
            text(
                """
                UPDATE chapters
                SET node_type = 'article'
                WHERE content IS NOT NULL AND content != ''
                """
            )
        )
        article_count = result.rowcount

        result = await session.execute(
            text(
                """
                UPDATE chapters
                SET node_type = 'folder'
                WHERE content IS NULL OR content = ''
                """
            )
        )
        folder_count = result.rowcount

        await session.commit()

        print(f"✓ 已更新 {article_count} 条记录为 'article'")
        print(f"✓ 已更新 {folder_count} 条记录为 'folder'")

    print()
    print("迁移完成！")


async def rollback() -> None:
    """回滚迁移：删除 node_type 列"""
    print("开始回滚: 删除 node_type 字段...")
    print()

    settings = get_settings()
    db_url = settings.DATABASE_URL

    async with AsyncSessionLocal() as session:
        # 检查列是否存在
        if not await column_exists(session, "chapters", "node_type"):
            print("✓ node_type 列不存在，跳过回滚")
            return

        print("删除 node_type 列...")

        if "sqlite" in db_url.lower():
            # SQLite 不支持 DROP COLUMN，需要重建表
            print("⚠️  SQLite 不支持直接删除列")
            print("   如需删除，请手动重建表或删除数据库重新初始化")
            return
        else:
            # PostgreSQL 支持直接删除列
            await session.execute(text("ALTER TABLE chapters DROP COLUMN node_type"))
            await session.commit()
            print("✓ node_type 列已删除")

    print()
    print("回滚完成！")


async def main() -> None:
    """主入口"""
    parser = argparse.ArgumentParser(description="node_type 字段迁移脚本")
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="回滚迁移（删除 node_type 列）",
    )
    args = parser.parse_args()

    if args.rollback:
        await rollback()
    else:
        await migrate()


if __name__ == "__main__":
    asyncio.run(main())

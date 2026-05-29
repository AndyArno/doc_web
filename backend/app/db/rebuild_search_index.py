"""
重建搜索索引脚本

清空现有索引并从数据库重建所有章节的搜索索引。

使用方法:
    cd backend && uv run python -m app.db.rebuild_search_index
"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.services import search_service


async def rebuild_search_index() -> None:
    print("开始重建搜索索引...")
    print()

    async with AsyncSessionLocal() as session:
        await search_service.ensure_search_table(session)
        count = await search_service.rebuild_all_indexes(session)
        print(f"✓ 已重建 {count} 个章节的搜索索引")

    print()
    print("搜索索引重建完成！")


if __name__ == "__main__":
    asyncio.run(rebuild_search_index())

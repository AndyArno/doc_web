"""
数据库初始化脚本

创建所有表并创建默认超级管理员用户。

使用方法:
    cd backend && uv run python -m app.db.init_db
"""

import asyncio
import os

from passlib.context import CryptContext
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal, engine
from app.models import Base, Role, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✓ 数据库表创建完成")

    settings = get_settings()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.role == Role.SUPER_ADMIN)
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print(f"✓ 超级管理员已存在: {existing_admin.username}")
            return

        password = os.getenv(
            "FIRST_SUPERADMIN_PASSWORD", settings.FIRST_SUPERADMIN_PASSWORD
        )
        hashed_password = pwd_context.hash(password)

        admin = User(
            username="admin",
            email="admin@example.com",
            hashed_password=hashed_password,
            role=Role.SUPER_ADMIN,
            is_active=True,
        )

        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        print(f"✓ 超级管理员创建成功: {admin.username}")
        print(f"  邮箱: {admin.email}")
        print(f"  角色: {admin.role.value}")
        print()
        print("⚠️  请立即登录并修改默认密码！")


async def main() -> None:
    print("开始初始化数据库...")
    print()
    await init_db()
    print()
    print("数据库初始化完成！")


if __name__ == "__main__":
    asyncio.run(main())

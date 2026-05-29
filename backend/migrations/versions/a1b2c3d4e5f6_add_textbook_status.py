"""add textbook status

Revision ID: a1b2c3d4e5f6
Revises: 6c55f3c4ba73
Create Date: 2026-03-27 15:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "6c55f3c4ba73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add status enum column, migrate data, drop is_published."""
    # 1. 创建枚举类型
    textbook_status_enum = sa.Enum("draft", "published", name="textbookstatus")
    textbook_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. 添加 status 列（允许 NULL 以便数据迁移）
    op.add_column("textbooks", sa.Column("status", textbook_status_enum, nullable=True))

    # 3. 数据迁移：is_published -> status
    op.execute("""
        UPDATE textbooks
        SET status = CASE
            WHEN is_published = true THEN 'published'::textbookstatus
            ELSE 'draft'::textbookstatus
        END
    """)

    # 4. 设置 status 列为 NOT NULL
    op.alter_column("textbooks", "status", nullable=False)

    # 5. 删除 is_published 列
    op.drop_column("textbooks", "is_published")


def downgrade() -> None:
    """Downgrade schema: add is_published column, migrate data, drop status."""
    # 1. 添加 is_published 列（允许 NULL 以便数据迁移）
    op.add_column("textbooks", sa.Column("is_published", sa.Boolean(), nullable=True))

    # 2. 数据迁移：status -> is_published
    op.execute("""
        UPDATE textbooks
        SET is_published = CASE
            WHEN status = 'published' THEN true
            ELSE false
        END
    """)

    # 3. 设置 is_published 列为 NOT NULL
    op.alter_column("textbooks", "is_published", nullable=False)

    # 4. 删除 status 列
    op.drop_column("textbooks", "status")

    # 5. 删除枚举类型
    textbook_status_enum = sa.Enum("draft", "published", name="textbookstatus")
    textbook_status_enum.drop(op.get_bind(), checkfirst=True)

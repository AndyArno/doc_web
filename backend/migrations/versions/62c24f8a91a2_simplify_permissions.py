"""simplify_permissions

Revision ID: 62c24f8a91a2
Revises: b2c3d4e5f6g7
Create Date: 2026-03-31 13:30:32.337598

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "62c24f8a91a2"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: 合并权限字段为 can_access.

    步骤：
    1. 添加 can_access 列
    2. 迁移数据：任一权限为 TRUE 则 can_access = TRUE
    3. 删除空权限记录（所有权限都为 FALSE）
    4. 删除四个旧权限列
    """
    # 1. 添加 can_access 列（允许 NULL 以便数据迁移）
    op.add_column(
        "user_textbook_permissions",
        sa.Column("can_access", sa.Boolean(), nullable=True),
    )

    # 2. 数据迁移：任一权限为 TRUE 则 can_access = TRUE，否则 FALSE
    op.execute("""
        UPDATE user_textbook_permissions
        SET can_access = CASE
            WHEN can_edit = TRUE 
                 OR can_create = TRUE 
                 OR can_delete = TRUE 
                 OR can_manage_users = TRUE
            THEN TRUE
            ELSE FALSE
        END
    """)

    # 3. 删除空权限记录（所有权限都为 FALSE）
    op.execute("""
        DELETE FROM user_textbook_permissions
        WHERE can_edit = FALSE
          AND can_create = FALSE
          AND can_delete = FALSE
          AND can_manage_users = FALSE
    """)

    # 4. 设置 can_access 列为 NOT NULL
    op.alter_column("user_textbook_permissions", "can_access", nullable=False)

    # 5. 删除四个旧权限列
    op.drop_column("user_textbook_permissions", "can_edit")
    op.drop_column("user_textbook_permissions", "can_create")
    op.drop_column("user_textbook_permissions", "can_delete")
    op.drop_column("user_textbook_permissions", "can_manage_users")


def downgrade() -> None:
    """Downgrade schema: 恢复四个权限字段.

    步骤：
    1. 添加回四个旧权限列（默认 FALSE）
    2. 删除 can_access 列

    注意：无法恢复已删除的空权限记录
    """
    # 1. 添加回四个旧权限列
    op.add_column(
        "user_textbook_permissions", sa.Column("can_edit", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "user_textbook_permissions",
        sa.Column("can_create", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "user_textbook_permissions",
        sa.Column("can_delete", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "user_textbook_permissions",
        sa.Column("can_manage_users", sa.Boolean(), nullable=True),
    )

    # 2. 数据迁移：can_access = TRUE 则四个权限都设为 TRUE（简化处理）
    # 注意：这是有损迁移，无法恢复原来的精确权限配置
    op.execute("""
        UPDATE user_textbook_permissions
        SET can_edit = can_access,
            can_create = can_access,
            can_delete = can_access,
            can_manage_users = can_access
    """)

    # 3. 设置四个旧权限列为 NOT NULL
    op.alter_column("user_textbook_permissions", "can_edit", nullable=False)
    op.alter_column("user_textbook_permissions", "can_create", nullable=False)
    op.alter_column("user_textbook_permissions", "can_delete", nullable=False)
    op.alter_column("user_textbook_permissions", "can_manage_users", nullable=False)

    # 4. 删除 can_access 列
    op.drop_column("user_textbook_permissions", "can_access")

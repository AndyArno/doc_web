"""add_node_type_to_chapters

Revision ID: e724271217c5
Revises: 4208643727c9
Create Date: 2026-05-18 18:22:17.997438

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e724271217c5'
down_revision: Union[str, Sequence[str], None] = '4208643727c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    nodetype = postgresql.ENUM("FOLDER", "ARTICLE", name="nodetype", create_type=True)
    nodetype.create(op.get_bind(), checkfirst=True)
    op.execute(
        "ALTER TABLE chapters ADD COLUMN IF NOT EXISTS node_type nodetype "
        "DEFAULT 'FOLDER' NOT NULL"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE chapters DROP COLUMN IF EXISTS node_type")
    nodetype = postgresql.ENUM("FOLDER", "ARTICLE", name="nodetype", create_type=False)
    nodetype.drop(op.get_bind(), checkfirst=True)

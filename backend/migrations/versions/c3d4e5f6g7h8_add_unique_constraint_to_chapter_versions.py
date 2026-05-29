"""add unique constraint to chapter_versions

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-04-21

"""

from typing import Sequence, Union

from alembic import op


revision: str = "c3d4e5f6g7h8"
down_revision: Union[str, Sequence[str], None] = "910a882f7cec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_chapter_version",
        "chapter_versions",
        ["chapter_id", "version_num"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_chapter_version", "chapter_versions", type_="unique")

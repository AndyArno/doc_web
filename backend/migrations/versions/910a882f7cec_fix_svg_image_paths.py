"""fix_svg_image_paths

Revision ID: 910a882f7cec
Revises: 1b9047b7f088
Create Date: 2026-04-05 19:17:13.890155

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "910a882f7cec"
down_revision: Union[str, Sequence[str], None] = "1b9047b7f088"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """修复章节中的SVG图片路径：./images/ -> /uploads/images/"""
    op.execute("""
        UPDATE chapters 
        SET content = REPLACE(content, './images/', '/uploads/images/')
        WHERE content LIKE '%./images/%'
    """)


def downgrade() -> None:
    """回滚：将路径改回 ./images/"""
    op.execute("""
        UPDATE chapters 
        SET content = REPLACE(content, '/uploads/images/', './images/')
        WHERE content LIKE '%/uploads/images/%'
    """)

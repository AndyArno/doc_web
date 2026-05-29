"""add timezone to datetime columns

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-29

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6g7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: convert all TIMESTAMP columns to TIMESTAMPTZ."""
    # users 表
    op.execute(
        "ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'"
    )

    # textbooks 表
    op.execute(
        "ALTER TABLE textbooks ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE textbooks ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'"
    )

    # chapters 表
    op.execute(
        "ALTER TABLE chapters ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE chapters ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'"
    )

    # chapter_versions 表
    op.execute(
        "ALTER TABLE chapter_versions ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE chapter_versions ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'"
    )

    # user_textbook_permissions 表
    op.execute(
        "ALTER TABLE user_textbook_permissions ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE user_textbook_permissions ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'"
    )

    # audit_logs 表
    op.execute(
        "ALTER TABLE audit_logs ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'"
    )

    # media 表
    op.execute(
        "ALTER TABLE media ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE media ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE media ALTER COLUMN deleted_at TYPE TIMESTAMPTZ USING deleted_at AT TIME ZONE 'UTC'"
    )


def downgrade() -> None:
    """Downgrade schema: convert all TIMESTAMPTZ columns back to TIMESTAMP."""
    # users 表
    op.execute(
        "ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at AT TIME ZONE 'UTC'"
    )

    # textbooks 表
    op.execute(
        "ALTER TABLE textbooks ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE textbooks ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at AT TIME ZONE 'UTC'"
    )

    # chapters 表
    op.execute(
        "ALTER TABLE chapters ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE chapters ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at AT TIME ZONE 'UTC'"
    )

    # chapter_versions 表
    op.execute(
        "ALTER TABLE chapter_versions ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE chapter_versions ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at AT TIME ZONE 'UTC'"
    )

    # user_textbook_permissions 表
    op.execute(
        "ALTER TABLE user_textbook_permissions ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE user_textbook_permissions ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at AT TIME ZONE 'UTC'"
    )

    # audit_logs 表
    op.execute(
        "ALTER TABLE audit_logs ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'"
    )

    # media 表
    op.execute(
        "ALTER TABLE media ALTER COLUMN created_at TYPE TIMESTAMP USING created_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE media ALTER COLUMN updated_at TYPE TIMESTAMP USING updated_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE media ALTER COLUMN deleted_at TYPE TIMESTAMP USING deleted_at AT TIME ZONE 'UTC'"
    )

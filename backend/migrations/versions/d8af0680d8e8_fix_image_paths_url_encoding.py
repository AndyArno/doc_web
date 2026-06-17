"""fix_image_paths_url_encoding

Revision ID: d8af0680d8e8
Revises: e724271217c5
Create Date: 2026-06-17 18:39:20.139254

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import re
from urllib.parse import unquote

revision: str = 'd8af0680d8e8'
down_revision: Union[str, Sequence[str], None] = 'e724271217c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix image paths: picture/xxx.png → /uploads/images/{uuid}.ext"""
    conn = op.get_bind()
    img_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')

    chapters = conn.execute(
        text("SELECT id, textbook_id, content FROM chapters WHERE content LIKE '%picture/%'")
    ).fetchall()

    for ch_id, textbook_id, content in chapters:
        if not content:
            continue
        new_content = content
        for match in img_pattern.finditer(content):
            alt_text = match.group(1)
            old_path = match.group(2)
            decoded = unquote(old_path)
            basename = decoded.split('/')[-1] if '/' in decoded else decoded
            media = conn.execute(
                text("SELECT filename FROM media WHERE textbook_id = :tid AND original_name = :oname"),
                {"tid": textbook_id, "oname": basename}
            ).fetchone()
            if media:
                new_url = f"/uploads/images/{media[0]}"
                new_content = new_content.replace(
                    f"![{alt_text}]({old_path})",
                    f"![{alt_text}]({new_url})"
                )
        if new_content != content:
            conn.execute(
                text("UPDATE chapters SET content = :content WHERE id = :id"),
                {"content": new_content, "id": ch_id}
            )

    versions = conn.execute(
        text("SELECT id, chapter_id, content FROM chapter_versions WHERE content LIKE '%picture/%'")
    ).fetchall()

    for ver_id, chapter_id, content in versions:
        if not content:
            continue
        ch_row = conn.execute(
            text("SELECT textbook_id FROM chapters WHERE id = :cid"),
            {"cid": chapter_id}
        ).fetchone()
        if not ch_row:
            continue
        textbook_id = ch_row[0]

        new_content = content
        for match in img_pattern.finditer(content):
            alt_text = match.group(1)
            old_path = match.group(2)
            decoded = unquote(old_path)
            basename = decoded.split('/')[-1] if '/' in decoded else decoded
            media = conn.execute(
                text("SELECT filename FROM media WHERE textbook_id = :tid AND original_name = :oname"),
                {"tid": textbook_id, "oname": basename}
            ).fetchone()
            if media:
                new_url = f"/uploads/images/{media[0]}"
                new_content = new_content.replace(
                    f"![{alt_text}]({old_path})",
                    f"![{alt_text}]({new_url})"
                )
        if new_content != content:
            conn.execute(
                text("UPDATE chapter_versions SET content = :content WHERE id = :id"),
                {"content": new_content, "id": ver_id}
            )


def downgrade() -> None:
    """Reverse: /uploads/images/{uuid}.ext → picture/{original_name}"""
    conn = op.get_bind()
    img_pattern = re.compile(r'!\[([^\]]*)\]\(/uploads/images/([^)]+)\)')

    for table_name, id_col in [('chapters', 'id'), ('chapter_versions', 'id')]:
        rows = conn.execute(
            text(f"SELECT {id_col}, content FROM {table_name} WHERE content LIKE '%/uploads/images/%'")
        ).fetchall()

        for row_id, content in rows:
            if not content:
                continue
            new_content = content
            for match in img_pattern.finditer(content):
                alt_text = match.group(1)
                uuid_filename = match.group(2)
                media = conn.execute(
                    text("SELECT original_name FROM media WHERE filename = :fname"),
                    {"fname": uuid_filename}
                ).fetchone()
                if media:
                    old_path = f"picture/{media[0]}"
                    new_content = new_content.replace(
                        f"![{alt_text}](/uploads/images/{uuid_filename})",
                        f"![{alt_text}]({old_path})"
                    )
            if new_content != content:
                conn.execute(
                    text(f"UPDATE {table_name} SET content = :content WHERE {id_col} = :id"),
                    {"content": new_content, "id": row_id}
                )

"""Initial migration

Revision ID: 001
Revises:
Create Date: 2026-03-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "posts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("is_media_group", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("file_id", sa.String, nullable=True),
        sa.Column("file_type", sa.String(10), nullable=True),
        sa.Column("caption_override", sa.Text, nullable=True),
        sa.Column("position", sa.Integer, unique=True, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "media_group_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "post_id",
            sa.Integer,
            sa.ForeignKey("posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_id", sa.String, nullable=False),
        sa.Column("file_type", sa.String(10), nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
    )

    op.create_table(
        "schedule_slots",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("day_of_week", sa.SmallInteger, nullable=True),
        sa.Column("time", sa.Time, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
    )

    op.create_table(
        "settings",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_table("schedule_slots")
    op.drop_table("media_group_items")
    op.drop_table("posts")

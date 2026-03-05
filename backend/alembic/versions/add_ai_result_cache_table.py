"""add ai result cache table

Revision ID: add_ai_result_cache_table
Revises: merge_heads_20260304
Create Date: 2026-03-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_ai_result_cache_table"
down_revision: Union[str, Sequence[str], None] = "merge_heads_20260304"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "ai_result_cache" not in existing_tables:
        op.create_table(
            "ai_result_cache",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("cache_key", sa.String(length=64), nullable=False),
            sa.Column("input_hash", sa.String(length=64), nullable=False),
            sa.Column("model", sa.String(length=120), nullable=False),
            sa.Column("prompt_version", sa.String(length=64), nullable=False),
            sa.Column("task_type", sa.String(length=120), nullable=False),
            sa.Column("result_json", sa.Text(), nullable=False),
            sa.Column("hits", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("last_accessed_at", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("cache_key"),
        )

    existing_indexes = {idx["name"] for idx in inspector.get_indexes("ai_result_cache")}
    indexes = [
        (op.f("ix_ai_result_cache_id"), ["id"], False),
        (op.f("ix_ai_result_cache_cache_key"), ["cache_key"], True),
        (op.f("ix_ai_result_cache_input_hash"), ["input_hash"], False),
        (op.f("ix_ai_result_cache_model"), ["model"], False),
        (op.f("ix_ai_result_cache_prompt_version"), ["prompt_version"], False),
        (op.f("ix_ai_result_cache_task_type"), ["task_type"], False),
        (op.f("ix_ai_result_cache_created_at"), ["created_at"], False),
        (op.f("ix_ai_result_cache_last_accessed_at"), ["last_accessed_at"], False),
        (op.f("ix_ai_result_cache_expires_at"), ["expires_at"], False),
    ]
    for idx_name, columns, unique in indexes:
        if idx_name not in existing_indexes:
            op.create_index(idx_name, "ai_result_cache", columns, unique=unique)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "ai_result_cache" not in set(inspector.get_table_names()):
        return

    existing_indexes = {idx["name"] for idx in inspector.get_indexes("ai_result_cache")}
    for idx_name in [
        op.f("ix_ai_result_cache_expires_at"),
        op.f("ix_ai_result_cache_last_accessed_at"),
        op.f("ix_ai_result_cache_created_at"),
        op.f("ix_ai_result_cache_task_type"),
        op.f("ix_ai_result_cache_prompt_version"),
        op.f("ix_ai_result_cache_model"),
        op.f("ix_ai_result_cache_input_hash"),
        op.f("ix_ai_result_cache_cache_key"),
        op.f("ix_ai_result_cache_id"),
    ]:
        if idx_name in existing_indexes:
            op.drop_index(idx_name, table_name="ai_result_cache")

    op.drop_table("ai_result_cache")

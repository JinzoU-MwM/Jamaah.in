"""add shared manifest lock fields

Revision ID: add_shared_manifest_lock_fields
Revises: add_ai_result_cache_table
Create Date: 2026-03-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_shared_manifest_lock_fields"
down_revision: Union[str, Sequence[str], None] = "add_ai_result_cache_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("groups")}

    if "shared_failed_attempts" not in columns:
        op.add_column(
            "groups",
            sa.Column("shared_failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        )
    if "shared_locked_until" not in columns:
        op.add_column("groups", sa.Column("shared_locked_until", sa.DateTime(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("groups")}

    if "shared_locked_until" in columns:
        op.drop_column("groups", "shared_locked_until")
    if "shared_failed_attempts" in columns:
        op.drop_column("groups", "shared_failed_attempts")

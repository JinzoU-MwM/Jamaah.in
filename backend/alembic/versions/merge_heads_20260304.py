"""merge alembic heads after support-ticket and phone-otp branches

Revision ID: merge_heads_20260304
Revises: add_super_admin_and_support_tickets, fix_phone_otp_code_size
Create Date: 2026-03-04
"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "merge_heads_20260304"
down_revision: Union[str, Sequence[str], None] = (
    "add_super_admin_and_support_tickets",
    "fix_phone_otp_code_size",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge-point migration with no schema changes."""
    pass


def downgrade() -> None:
    """No-op downgrade for merge-point migration."""
    pass


"""add performance indexes

Revision ID: add_performance_indexes
Revises: 6b58c0cb7608
Create Date: 2026-02-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'add_performance_indexes'
down_revision = '6b58c0cb7608'
branch_labels = None
depends_on = None


def upgrade():
    # Index for NIK searches
    op.create_index(
        'idx_group_members_nik',
        'group_members',
        ['no_identitas']
    )

    # Index for passport searches
    op.create_index(
        'idx_group_members_passport',
        'group_members',
        ['no_paspor']
    )

    # Index for family grouping (room assignment optimization)
    op.create_index(
        'idx_group_members_family_id',
        'group_members',
        ['family_id']
    )

    # Index for user groups ordering
    op.create_index(
        'idx_groups_user_updated',
        'groups',
        ['user_id', sa.text('updated_at DESC')]
    )


def downgrade():
    op.drop_index('idx_groups_user_updated', table_name='groups')
    op.drop_index('idx_group_members_family_id', table_name='group_members')
    op.drop_index('idx_group_members_passport', table_name='group_members')
    op.drop_index('idx_group_members_nik', table_name='group_members')

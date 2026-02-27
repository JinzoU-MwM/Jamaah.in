"""add phone verification fields

Revision ID: add_phone_verification
Revises: add_performance_indexes
Create Date: 2026-02-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'add_phone_verification'
down_revision = 'add_performance_indexes'
branch_labels = None
depends_on = None


def upgrade():
    # Add phone verification fields to users table
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('phone_verified', sa.Boolean(), default=False))
    op.add_column('users', sa.Column('phone_otp_code', sa.String(10), nullable=True))
    op.add_column('users', sa.Column('phone_otp_expires', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('trial_used_at', sa.DateTime(), nullable=True))

    # Create unique index on phone_number
    op.create_index('idx_users_phone_number', 'users', ['phone_number'], unique=True)


def downgrade():
    op.drop_index('idx_users_phone_number', table_name='users')
    op.drop_column('users', 'trial_used_at')
    op.drop_column('users', 'phone_otp_expires')
    op.drop_column('users', 'phone_otp_code')
    op.drop_column('users', 'phone_verified')
    op.drop_column('users', 'phone_number')

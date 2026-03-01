"""fix phone_otp_code column size for bcrypt hash

Revision ID: fix_phone_otp_code_size
Revises: add_phone_verification
Create Date: 2026-03-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'fix_phone_otp_code_size'
down_revision = 'add_phone_verification'
branch_labels = None
depends_on = None


def upgrade():
    # Alter phone_otp_code from String(10) to String(255) to store bcrypt hash
    op.alter_column('users', 'phone_otp_code',
                    existing_type=sa.String(10),
                    type_=sa.String(255),
                    existing_nullable=True)


def downgrade():
    op.alter_column('users', 'phone_otp_code',
                    existing_type=sa.String(255),
                    type_=sa.String(10),
                    existing_nullable=True)

"""add super admin and support tickets

Revision ID: add_super_admin_and_support_tickets
Revises: 6b58c0cb7608
Create Date: 2026-03-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_super_admin_and_support_tickets'
down_revision: Union[str, Sequence[str], None] = '6b58c0cb7608'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_super_admin column to users table
    op.add_column('users', sa.Column('is_super_admin', sa.Boolean(), nullable=False, server_default='false'))

    # Create ticket status enum
    ticket_status_enum = sa.Enum('open', 'in_progress', 'resolved', 'closed', name='ticketstatus')
    ticket_status_enum.create(op.get_bind())

    # Create ticket priority enum
    ticket_priority_enum = sa.Enum('low', 'medium', 'high', 'urgent', name='ticketpriority')
    ticket_priority_enum.create(op.get_bind())

    # Create sender type enum
    sender_type_enum = sa.Enum('user', 'admin', name='sendertype')
    sender_type_enum.create(op.get_bind())

    # Create support_tickets table
    op.create_table(
        'support_tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('status', ticket_status_enum, nullable=False),
        sa.Column('priority', ticket_priority_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_support_tickets_user_id'), 'support_tickets', ['user_id'], unique=False)
    op.create_index(op.f('ix_support_tickets_status'), 'support_tickets', ['status'], unique=False)
    op.create_index(op.f('ix_support_tickets_priority'), 'support_tickets', ['priority'], unique=False)
    op.create_index(op.f('ix_support_tickets_created_at'), 'support_tickets', ['created_at'], unique=False)

    # Create ticket_messages table
    op.create_table(
        'ticket_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('sender_type', sender_type_enum, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['ticket_id'], ['support_tickets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ticket_messages_ticket_id'), 'ticket_messages', ['ticket_id'], unique=False)
    op.create_index(op.f('ix_ticket_messages_sender_type'), 'ticket_messages', ['sender_type'], unique=False)
    op.create_index(op.f('ix_ticket_messages_created_at'), 'ticket_messages', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop ticket_messages table
    op.drop_index(op.f('ix_ticket_messages_created_at'), table_name='ticket_messages')
    op.drop_index(op.f('ix_ticket_messages_sender_type'), table_name='ticket_messages')
    op.drop_index(op.f('ix_ticket_messages_ticket_id'), table_name='ticket_messages')
    op.drop_table('ticket_messages')

    # Drop support_tickets table
    op.drop_index(op.f('ix_support_tickets_created_at'), table_name='support_tickets')
    op.drop_index(op.f('ix_support_tickets_priority'), table_name='support_tickets')
    op.drop_index(op.f('ix_support_tickets_status'), table_name='support_tickets')
    op.drop_index(op.f('ix_support_tickets_user_id'), table_name='support_tickets')
    op.drop_table('support_tickets')

    # Drop enums
    sender_type_enum = sa.Enum(name='sendertype')
    sender_type_enum.drop(op.get_bind())

    ticket_priority_enum = sa.Enum(name='ticketpriority')
    ticket_priority_enum.drop(op.get_bind())

    ticket_status_enum = sa.Enum(name='ticketstatus')
    ticket_status_enum.drop(op.get_bind())

    # Drop is_super_admin column from users table
    op.drop_column('users', 'is_super_admin')

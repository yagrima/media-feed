"""Add notifications and preferences tables

Revision ID: 004
Revises: 003
Create Date: 2025-10-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Create notification_preferences table and add additional indexes to notifications."""

    # Notifications table already exists from migration 001
    # Just add additional indexes
    op.create_index('idx_notifications_user_read', 'notifications', ['user_id', 'is_read', 'created_at'])
    op.create_index('idx_notifications_user_created', 'notifications', ['user_id', 'created_at'])
    op.create_index('idx_notifications_type', 'notifications', ['type'])

    # Create notification_preferences table
    op.create_table(
        'notification_preferences',
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('email_enabled', sa.Boolean, default=True, nullable=False),
        sa.Column('email_frequency', sa.String(20), default='daily', nullable=False),
        sa.Column('in_app_enabled', sa.Boolean, default=True, nullable=False),
        sa.Column('sequel_notifications', sa.Boolean, default=True, nullable=False),
        sa.Column('season_notifications', sa.Boolean, default=True, nullable=False),
        sa.Column('new_content_notifications', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint(
            "email_frequency IN ('instant', 'daily', 'weekly', 'never')",
            name='valid_email_frequency'
        ),
    )


def downgrade():
    """Drop notification_preferences table and indexes."""
    # Drop notification_preferences table
    op.drop_table('notification_preferences')

    # Drop indexes for notifications
    op.drop_index('idx_notifications_type', 'notifications')
    op.drop_index('idx_notifications_user_created', 'notifications')
    op.drop_index('idx_notifications_user_read', 'notifications')

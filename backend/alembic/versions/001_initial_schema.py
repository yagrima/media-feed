"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-10-19 19:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET, TIMESTAMP
import uuid
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema"""

    # Users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('email_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('failed_login_attempts', sa.Integer, nullable=False, server_default='0'),
        sa.Column('locked_until', TIMESTAMP, nullable=True),
        sa.Column('totp_secret', sa.String(32), nullable=True),
        sa.Column('refresh_token_hash', sa.String(255), nullable=True),
        sa.Column('last_login_at', TIMESTAMP, nullable=True),
        sa.Column('last_login_ip', sa.String(45), nullable=True),
        sa.Column('created_at', TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_users_email', 'users', ['email'])

    # User sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('refresh_token_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('expires_at', TIMESTAMP, nullable=False),
        sa.Column('ip_address', INET, nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('created_at', TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_sessions_user', 'user_sessions', ['user_id'])
    op.create_index('idx_sessions_token', 'user_sessions', ['refresh_token_hash'])

    # Media table
    op.create_table(
        'media',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('type', sa.String(50), nullable=True),
        sa.Column('release_date', sa.Date, nullable=True),
        sa.Column('base_title', sa.String(255), nullable=True),
        sa.Column('season_number', sa.Integer, nullable=True),
        sa.Column('episode_number', sa.Integer, nullable=True),
        sa.Column('tmdb_id', sa.Integer, nullable=True),
        sa.Column('imdb_id', sa.String(20), nullable=True),
        sa.Column('platform', sa.String(50), nullable=True),
        sa.Column('platform_ids', JSONB, nullable=False, server_default='{}'),
        sa.Column('media_metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('parent_id', UUID(as_uuid=True), sa.ForeignKey('media.id'), nullable=True),
        sa.Column('created_at', TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', TIMESTAMP, nullable=True),
    )
    op.create_index('idx_media_title', 'media', ['title'])
    op.create_index('idx_media_base_title', 'media', ['base_title'])
    op.create_index('idx_media_tmdb', 'media', ['tmdb_id'])

    # User media table
    op.create_table(
        'user_media',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('media_id', UUID(as_uuid=True), sa.ForeignKey('media.id', ondelete='CASCADE'), nullable=False),
        sa.Column('watched_date', sa.Date, nullable=True),
        sa.Column('rating', sa.Integer, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_user_media_user', 'user_media', ['user_id'])
    op.create_index('idx_user_media_media', 'user_media', ['media_id'])
    op.create_index('idx_user_media_unique', 'user_media', ['user_id', 'media_id'], unique=True)

    # Security events table
    op.create_table(
        'security_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('ip_address', INET, nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('event_metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_security_events_user', 'security_events', ['user_id'])
    op.create_index('idx_security_events_type', 'security_events', ['event_type'])

    # Notifications table
    op.create_table(
        'notifications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('media_id', UUID(as_uuid=True), sa.ForeignKey('media.id', ondelete='SET NULL'), nullable=True),
        sa.Column('related_media_id', UUID(as_uuid=True), sa.ForeignKey('media.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action_url', sa.String(500), nullable=True),
        sa.Column('is_read', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_emailed', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('unsubscribe_token', sa.String(255), nullable=True, unique=True),
        sa.Column('unsubscribe_token_expires', TIMESTAMP, nullable=True),
        sa.Column('notification_metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('read_at', TIMESTAMP, nullable=True),
        sa.Column('emailed_at', TIMESTAMP, nullable=True),
    )
    op.create_index('idx_notifications_user', 'notifications', ['user_id'])
    op.create_index('idx_notifications_read', 'notifications', ['is_read'])


def downgrade() -> None:
    """Drop all tables"""
    op.drop_table('notifications')
    op.drop_table('security_events')
    op.drop_table('user_media')
    op.drop_table('media')
    op.drop_table('user_sessions')
    op.drop_table('users')

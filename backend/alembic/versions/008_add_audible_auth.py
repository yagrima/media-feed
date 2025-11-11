"""add_audible_auth

Revision ID: 008
Revises: 007
Create Date: 2025-11-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # Create audible_auth table for storing encrypted Audible API tokens
    op.create_table(
        'audible_auth',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('encrypted_token', sa.Text(), nullable=False, comment='AES-256 encrypted Audible auth token'),
        sa.Column('marketplace', sa.String(10), nullable=False, comment='Audible marketplace: us, uk, de, etc.'),
        sa.Column('device_name', sa.String(255), nullable=True, comment='Virtual device name registered with Audible'),
        sa.Column('last_sync_at', sa.TIMESTAMP(), nullable=True, comment='Last successful library sync timestamp'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('user_id', name='uq_audible_auth_user_id')
    )
    
    # Create index for quick user lookup
    op.create_index('idx_audible_auth_user', 'audible_auth', ['user_id'])


def downgrade():
    # Drop index first
    op.drop_index('idx_audible_auth_user', table_name='audible_auth')
    
    # Drop table
    op.drop_table('audible_auth')

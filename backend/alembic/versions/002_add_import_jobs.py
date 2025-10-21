"""Add import_jobs table

Revision ID: 002
Revises: 001
Create Date: 2025-10-19 19:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create import_jobs table"""
    op.create_table(
        'import_jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('total_rows', sa.Integer, nullable=False, server_default='0'),
        sa.Column('processed_rows', sa.Integer, nullable=False, server_default='0'),
        sa.Column('successful_rows', sa.Integer, nullable=False, server_default='0'),
        sa.Column('failed_rows', sa.Integer, nullable=False, server_default='0'),
        sa.Column('error_log', JSONB, nullable=False, server_default='[]'),
        sa.Column('filename', sa.String(255), nullable=True),
        sa.Column('file_size', sa.Integer, nullable=True),
        sa.Column('file_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('started_at', sa.TIMESTAMP, nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP, nullable=True),
    )

    # Create indexes
    op.create_index('idx_import_jobs_user_status', 'import_jobs', ['user_id', 'status'])
    op.create_index('idx_import_jobs_created', 'import_jobs', ['created_at'])


def downgrade() -> None:
    """Drop import_jobs table"""
    op.drop_index('idx_import_jobs_created', table_name='import_jobs')
    op.drop_index('idx_import_jobs_user_status', table_name='import_jobs')
    op.drop_table('import_jobs')

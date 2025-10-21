"""Add sequel tracking fields to media table

Revision ID: 003
Revises: 002
Create Date: 2025-10-20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Add sequel tracking fields to media table."""
    # These fields were already added in migration 001
    # Just add the additional indexes
    op.create_index('idx_media_season_number', 'media', ['season_number'])
    op.create_index('idx_media_base_title_season', 'media', ['base_title', 'season_number'])


def downgrade():
    """Remove sequel tracking fields from media table."""
    # Drop only the indexes we created
    op.drop_index('idx_media_base_title_season', 'media')
    op.drop_index('idx_media_season_number', 'media')

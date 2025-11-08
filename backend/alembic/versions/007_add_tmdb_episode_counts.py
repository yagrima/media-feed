"""Add TMDB episode counts to media

Revision ID: 007
Revises: 006
Create Date: 2025-11-09

Adds columns to store total season/episode counts from TMDB API:
- total_seasons: Total number of seasons for TV series
- total_episodes: Total number of episodes across all seasons
- last_tmdb_update: Timestamp of last TMDB data fetch

This enables progress tracking like "45/276 episodes watched"
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    """Add TMDB episode count columns"""
    
    # Add total_seasons column (for TV series)
    op.add_column('media',
        sa.Column('total_seasons', sa.Integer(), nullable=True)
    )
    
    # Add total_episodes column (sum across all seasons)
    op.add_column('media',
        sa.Column('total_episodes', sa.Integer(), nullable=True)
    )
    
    # Add last update timestamp for TMDB data
    op.add_column('media',
        sa.Column('last_tmdb_update', TIMESTAMP, nullable=True)
    )
    
    # Add index for querying series with known episode counts
    op.create_index(
        'idx_media_total_episodes',
        'media',
        ['total_episodes']
    )


def downgrade():
    """Revert TMDB episode count columns"""
    
    # Drop index
    op.drop_index('idx_media_total_episodes', table_name='media')
    
    # Drop columns
    op.drop_column('media', 'last_tmdb_update')
    op.drop_column('media', 'total_episodes')
    op.drop_column('media', 'total_seasons')

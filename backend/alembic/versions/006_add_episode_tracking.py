"""Add episode tracking to user_media

Revision ID: 006
Revises: 005
Create Date: 2025-10-26

Enables episode-by-episode tracking for TV series:
- Adds season_number and episode_number to user_media
- Changes unique constraint to allow multiple episodes per media
- One Media entry per series, multiple UserMedia entries per episode
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    """Add episode tracking columns and update constraints"""
    
    # Add episode tracking columns
    op.add_column('user_media',
        sa.Column('season_number', sa.Integer(), nullable=True)
    )
    
    op.add_column('user_media',
        sa.Column('episode_number', sa.Integer(), nullable=True)
    )
    
    op.add_column('user_media',
        sa.Column('episode_title', sa.String(500), nullable=True)
    )
    
    # Drop old unique constraint
    op.drop_index('idx_user_media_unique', table_name='user_media')
    
    # Create new unique constraint that allows multiple episodes per series
    # Constraint allows same media_id with different season/episode combinations
    op.create_index(
        'idx_user_media_episode_unique',
        'user_media',
        ['user_id', 'media_id', 'season_number', 'episode_number'],
        unique=True
    )
    
    # Add index for season queries
    op.create_index(
        'idx_user_media_season',
        'user_media',
        ['media_id', 'season_number']
    )


def downgrade():
    """Revert episode tracking changes"""
    
    # Drop new indexes
    op.drop_index('idx_user_media_season', table_name='user_media')
    op.drop_index('idx_user_media_episode_unique', table_name='user_media')
    
    # Restore old unique constraint
    op.create_index(
        'idx_user_media_unique',
        'user_media',
        ['user_id', 'media_id'],
        unique=True
    )
    
    # Drop columns
    op.drop_column('user_media', 'episode_title')
    op.drop_column('user_media', 'episode_number')
    op.drop_column('user_media', 'season_number')

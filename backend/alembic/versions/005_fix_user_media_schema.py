"""Fix user_media schema

Revision ID: 005
Revises: 004
Create Date: 2025-10-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    """Add missing columns to user_media table"""
    
    # Add status column
    op.add_column('user_media',
        sa.Column('status', sa.String(50), nullable=True)
    )
    
    # Add platform column
    op.add_column('user_media',
        sa.Column('platform', sa.String(50), nullable=True)
    )
    
    # Add consumed_at column
    op.add_column('user_media',
        sa.Column('consumed_at', sa.Date(), nullable=True)
    )
    
    # Add imported_from column
    op.add_column('user_media',
        sa.Column('imported_from', sa.String(50), nullable=True)
    )
    
    # Add raw_import_data column
    op.add_column('user_media',
        sa.Column('raw_import_data', sa.JSON(), nullable=True)
    )
    
    # Migrate data from watched_date to consumed_at
    op.execute("""
        UPDATE user_media 
        SET consumed_at = watched_date 
        WHERE watched_date IS NOT NULL
    """)
    
    # Set default status for existing entries
    op.execute("""
        UPDATE user_media 
        SET status = 'watched' 
        WHERE status IS NULL
    """)
    
    # Drop old watched_date column (optional - keep for backward compatibility)
    # op.drop_column('user_media', 'watched_date')


def downgrade():
    """Revert changes"""
    
    # Restore watched_date if needed
    # op.add_column('user_media', 
    #     sa.Column('watched_date', sa.Date(), nullable=True)
    # )
    
    op.drop_column('user_media', 'raw_import_data')
    op.drop_column('user_media', 'imported_from')
    op.drop_column('user_media', 'consumed_at')
    op.drop_column('user_media', 'platform')
    op.drop_column('user_media', 'status')

"""
Dashboard API Endpoints
Provides overview statistics and recent activity
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.db.base import get_db
from app.db.models import UserMedia, Media, User
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/statistics")
async def get_dashboard_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get dashboard statistics for the current user
    
    Returns aggregate statistics for different media types
    and recent activity
    """
    
    # Get total media count by type
    media_stats_query = (
        select(
            Media.type,
            func.count(func.distinct(Media.id)).label('unique_media_count'),
            func.count(UserMedia.id).label('total_items_count')
        )
        .join(UserMedia, Media.id == UserMedia.media_id)
        .where(UserMedia.user_id == current_user.id)
        .group_by(Media.type)
    )
    
    media_stats_result = await db.execute(media_stats_query)
    media_stats_rows = media_stats_result.all()
    
    # Initialize stats for all media types (future-proof)
    stats_by_type = {
        'movie': {'unique_count': 0, 'total_count': 0},
        'tv_series': {'unique_count': 0, 'total_count': 0},
        'book': {'unique_count': 0, 'total_count': 0},
        'audiobook': {'unique_count': 0, 'total_count': 0},
    }
    
    # Fill in actual data
    for row in media_stats_rows:
        media_type = row.type
        if media_type in stats_by_type:
            stats_by_type[media_type] = {
                'unique_count': row.unique_media_count,
                'total_count': row.total_items_count
            }
    
    # Get recent activity (last 10 items)
    recent_query = (
        select(UserMedia, Media)
        .join(Media, UserMedia.media_id == Media.id)
        .where(UserMedia.user_id == current_user.id)
        .order_by(desc(UserMedia.consumed_at), desc(UserMedia.created_at))
        .limit(10)
    )
    
    recent_result = await db.execute(recent_query)
    recent_items = recent_result.all()
    
    # Format recent activity
    recent_activity = [
        {
            'id': str(user_media.id),
            'media_id': str(media.id),
            'title': media.title,
            'type': media.type,
            'platform': user_media.platform or media.platform,
            'consumed_at': user_media.consumed_at.isoformat() if user_media.consumed_at else None,
            'season_number': user_media.season_number,
            'episode_title': user_media.episode_title,
        }
        for user_media, media in recent_items
    ]
    
    # Get this week's activity count
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_count_query = (
        select(func.count(UserMedia.id))
        .where(
            and_(
                UserMedia.user_id == current_user.id,
                UserMedia.consumed_at >= week_ago.date()
            )
        )
    )
    week_count_result = await db.execute(week_count_query)
    this_week_count = week_count_result.scalar() or 0
    
    return {
        'statistics': stats_by_type,
        'recent_activity': recent_activity,
        'this_week_count': this_week_count,
        'total_items': sum(stat['total_count'] for stat in stats_by_type.values()),
    }

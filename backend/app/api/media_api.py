"""
Media API Endpoints
Handles user media library operations
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select, func, and_
from typing import List, Optional
from uuid import UUID

from app.db.base import get_db
from app.db.models import UserMedia, Media, User
from app.core.dependencies import get_current_user
from app.schemas.media_schemas import (
    UserMediaResponse,
    UserMediaListResponse,
    MediaType,
)

router = APIRouter(prefix="/api", tags=["media"])


@router.get("/media-test")
async def test_media_endpoint():
    """
    Simple test endpoint without auth or database
    """
    return {
        "test": "ok",
        "message": "Media API is reachable"
    }


@router.get("/media", response_model=UserMediaListResponse)
async def get_user_media(
    type: Optional[MediaType] = Query(None, description="Filter by media type"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's media library with optional filtering
    
    Returns one card per Media (series/movie), with episode counts for TV series.
    Each UserMedia represents one episode, so we group by media_id.

    - **type**: Filter by movie or tv_series (optional)
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    """
    # Build query to get distinct media IDs for this user
    # Group by media_id to get one row per series/movie
    media_ids_stmt = (
        select(Media.id, func.max(UserMedia.consumed_at).label('latest_consumed'))
        .join(UserMedia)
        .where(UserMedia.user_id == current_user.id)
    )
    
    # Apply type filter if provided
    if type:
        media_ids_stmt = media_ids_stmt.where(Media.type == type.value)
    
    media_ids_stmt = media_ids_stmt.group_by(Media.id)
    
    # Count total unique media
    count_stmt = select(func.count()).select_from(
        media_ids_stmt.subquery()
    )
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()
    
    # Apply ordering and pagination on grouped results
    media_ids_stmt = (
        media_ids_stmt
        .order_by(func.max(UserMedia.consumed_at).desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    
    # Get the media IDs for this page
    media_ids_result = await db.execute(media_ids_stmt)
    media_ids = [row[0] for row in media_ids_result.all()]
    
    if not media_ids:
        return {
            "items": [],
            "total": total,
            "page": page,
            "limit": limit,
        }
    
    # Fetch full media objects with first UserMedia for each
    # We need at least one UserMedia per Media to return
    stmt = (
        select(Media)
        .options(joinedload(Media.user_consumption))
        .where(Media.id.in_(media_ids))
    )
    
    result = await db.execute(stmt)
    media_items = result.scalars().unique().all()
    
    # For each media, count episodes and create a representative UserMedia
    items = []
    for media in media_items:
        # Count total episodes for this media
        episode_count_stmt = (
            select(func.count())
            .select_from(UserMedia)
            .where(
                and_(
                    UserMedia.user_id == current_user.id,
                    UserMedia.media_id == media.id
                )
            )
        )
        count_result = await db.execute(episode_count_stmt)
        watched_count = count_result.scalar()
        
        # Get the most recent UserMedia for this media (for consumed_at date)
        latest_stmt = (
            select(UserMedia)
            .where(
                and_(
                    UserMedia.user_id == current_user.id,
                    UserMedia.media_id == media.id
                )
            )
            .order_by(UserMedia.consumed_at.desc())
            .limit(1)
        )
        latest_result = await db.execute(latest_stmt)
        representative_user_media = latest_result.scalar_one()
        
        # Attach episode count to media for serialization
        if media.type == "tv_series":
            media.watched_episodes_count = watched_count
        
        items.append(representative_user_media)

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/media/{media_id}/episodes")
async def get_media_episodes(
    media_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all episodes for a TV series
    
    Returns list of all episodes the user has watched for this series,
    grouped by season and ordered by episode number.
    """
    # Verify media exists and is a TV series
    media_stmt = select(Media).where(Media.id == media_id)
    media_result = await db.execute(media_stmt)
    media = media_result.scalar_one_or_none()
    
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Get all episodes for this media
    episodes_stmt = (
        select(UserMedia)
        .where(
            and_(
                UserMedia.user_id == current_user.id,
                UserMedia.media_id == media_id
            )
        )
        .order_by(
            UserMedia.season_number.asc().nulls_last(),
            UserMedia.episode_number.asc().nulls_last(),
            UserMedia.consumed_at.desc()
        )
    )
    
    episodes_result = await db.execute(episodes_stmt)
    episodes = episodes_result.scalars().all()
    
    # Format response with episode details
    return {
        "media": {
            "id": str(media.id),
            "title": media.title,
            "type": media.type,
        },
        "episodes": [
            {
                "id": str(ep.id),
                "season_number": ep.season_number,
                "episode_number": ep.episode_number,
                "episode_title": ep.episode_title,
                "consumed_at": ep.consumed_at.isoformat() if ep.consumed_at else None,
                "platform": ep.platform,
            }
            for ep in episodes
        ],
        "total_episodes": len(episodes)
    }


@router.delete("/media/{media_id}")
async def delete_user_media(
    media_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a user media entry (single episode or entire series)
    """
    # Find user media entry
    stmt = select(UserMedia).where(
        UserMedia.id == media_id,
        UserMedia.user_id == current_user.id
    )
    result = await db.execute(stmt)
    user_media = result.scalar_one_or_none()

    if not user_media:
        raise HTTPException(status_code=404, detail="Media not found")

    # Delete entry
    await db.delete(user_media)
    await db.commit()

    return {"message": "Media deleted successfully"}

"""
Media API Endpoints
Handles user media library operations
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select, func
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

    - **type**: Filter by movie or tv_series (optional)
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    """
    # Build base statement
    stmt = (
        select(UserMedia)
        .options(joinedload(UserMedia.media))
        .where(UserMedia.user_id == current_user.id)
    )

    # Build count statement
    count_stmt = (
        select(func.count())
        .select_from(UserMedia)
        .where(UserMedia.user_id == current_user.id)
    )

    # Apply type filter if provided
    if type:
        stmt = stmt.join(Media).where(Media.type == type.value)
        count_stmt = count_stmt.join(Media).where(Media.type == type.value)

    # Get total count
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Apply pagination and ordering
    offset = (page - 1) * limit
    stmt = stmt.order_by(UserMedia.consumed_at.desc()).offset(offset).limit(limit)

    # Execute query
    result = await db.execute(stmt)
    items = result.scalars().unique().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.delete("/media/{media_id}")
async def delete_user_media(
    media_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a user media entry
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

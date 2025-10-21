"""
Media API Endpoints
Handles user media library operations
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
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

router = APIRouter(prefix="/api/user", tags=["media"])


@router.get("/media", response_model=UserMediaListResponse)
async def get_user_media(
    type: Optional[MediaType] = Query(None, description="Filter by media type"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user's media library with optional filtering

    - **type**: Filter by movie or tv_series (optional)
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    """
    # Build query
    query = (
        db.query(UserMedia)
        .options(joinedload(UserMedia.media))
        .filter(UserMedia.user_id == current_user.id)
    )

    # Apply type filter if provided
    if type:
        query = query.join(Media).filter(Media.type == type.value)

    # Get total count before pagination
    total = query.count()

    # Apply pagination
    offset = (page - 1) * limit
    items = query.order_by(UserMedia.consumed_at.desc()).offset(offset).limit(limit).all()

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
    db: Session = Depends(get_db),
):
    """
    Delete a user media entry
    """
    user_media = (
        db.query(UserMedia)
        .filter(UserMedia.id == media_id, UserMedia.user_id == current_user.id)
        .first()
    )

    if not user_media:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Media not found")

    db.delete(user_media)
    db.commit()

    return {"message": "Media deleted successfully"}

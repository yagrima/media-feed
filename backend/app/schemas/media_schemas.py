"""
Media Pydantic Schemas
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from enum import Enum
from uuid import UUID


class MediaType(str, Enum):
    """Media type enumeration"""
    movie = "movie"
    tv_series = "tv_series"


class MediaBase(BaseModel):
    """Base media schema"""
    title: str
    type: str
    platform: Optional[str] = None
    base_title: Optional[str] = None
    season_number: Optional[int] = None


class MediaResponse(MediaBase):
    """Media response schema"""
    id: UUID
    created_at: datetime
    watched_episodes_count: Optional[int] = None  # Number of watched episodes for TV series
    total_episodes: Optional[int] = None  # Total episodes from TMDB (for TV series)
    total_seasons: Optional[int] = None  # Total seasons from TMDB (for TV series)

    class Config:
        from_attributes = True


class UserMediaBase(BaseModel):
    """Base user media schema"""
    consumed_at: Optional[datetime] = None
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    episode_title: Optional[str] = None


class UserMediaResponse(UserMediaBase):
    """User media response schema"""
    id: UUID
    user_id: UUID
    media_id: UUID
    created_at: datetime
    media: MediaResponse

    class Config:
        from_attributes = True


class UserMediaListResponse(BaseModel):
    """Paginated user media list response"""
    items: List[UserMediaResponse]
    total: int
    page: int
    limit: int

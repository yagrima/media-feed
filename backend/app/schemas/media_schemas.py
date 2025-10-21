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
    platform: str
    base_title: Optional[str] = None
    season_number: Optional[int] = None


class MediaResponse(MediaBase):
    """Media response schema"""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class UserMediaBase(BaseModel):
    """Base user media schema"""
    consumed_at: datetime


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

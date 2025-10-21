"""
Media and import schemas with validation
"""
from pydantic import BaseModel, validator, constr
from typing import Optional, Dict, Any
from datetime import date, datetime
import re


class MediaImport(BaseModel):
    """Manual media import with sanitization"""
    title: constr(max_length=255, pattern=r'^[^<>&]*$')
    platform: constr(pattern=r'^[a-zA-Z0-9_-]+$')
    consumed_at: Optional[str]
    status: Optional[str] = "completed"

    @validator('title')
    def sanitize_title(cls, v):
        """Additional title sanitization"""
        if not v:
            raise ValueError('Title cannot be empty')
        # Remove null bytes and excessive whitespace
        v = v.strip().replace('\x00', '')
        # Remove potential formula injection characters if at start
        if v and v[0] in ['=', '+', '-', '@']:
            v = "'" + v
        return v

    @validator('platform')
    def validate_platform(cls, v):
        """Validate platform name"""
        allowed_platforms = [
            'netflix', 'amazon', 'disney', 'hbo', 'apple', 'hulu',
            'youtube', 'other'
        ]
        if v.lower() not in allowed_platforms:
            return 'other'
        return v.lower()


class MediaResponse(BaseModel):
    """Media information response"""
    id: str
    title: str
    type: Optional[str]
    release_date: Optional[date]
    platform_ids: Dict[str, Any]
    metadata: Dict[str, Any]
    parent_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class MediaSearch(BaseModel):
    """Media search parameters"""
    query: constr(min_length=1, max_length=255)
    type: Optional[str] = None
    limit: Optional[int] = 20

    @validator('query')
    def sanitize_query(cls, v):
        """Sanitize search query"""
        # Remove special SQL characters
        v = re.sub(r'[;<>\"\'\\]', '', v)
        return v.strip()

    @validator('limit')
    def validate_limit(cls, v):
        """Ensure reasonable limit"""
        if v is not None and (v < 1 or v > 100):
            return 20
        return v


class UserMediaResponse(BaseModel):
    """User's media consumption response"""
    media: MediaResponse
    status: Optional[str]
    platform: Optional[str]
    consumed_at: Optional[date]
    imported_from: Optional[str]

    class Config:
        from_attributes = True


class ImportStatus(BaseModel):
    """CSV import status response"""
    job_id: str
    status: str  # pending, processing, completed, failed
    total_rows: int
    processed_rows: int
    success_count: int
    error_count: int
    errors: list[str]


class NotificationPreferences(BaseModel):
    """User notification preferences"""
    email_enabled: bool = True
    notify_sequels: bool = True
    notify_seasons: bool = True
    frequency: str = "immediate"  # immediate, daily, weekly

    @validator('frequency')
    def validate_frequency(cls, v):
        """Validate notification frequency"""
        allowed = ['immediate', 'daily', 'weekly']
        if v not in allowed:
            return 'immediate'
        return v

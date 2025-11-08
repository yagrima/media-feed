"""
Pydantic schemas for notification API endpoints
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class NotificationResponse(BaseModel):
    """Response schema for a single notification"""
    id: UUID
    user_id: UUID
    type: str
    title: str
    message: str
    media_id: Optional[UUID] = None
    sequel_id: Optional[UUID] = None
    read: bool
    emailed: bool
    data: Dict[str, Any] = Field(default_factory=dict, alias="metadata")  # Frontend expects "data"
    created_at: datetime
    read_at: Optional[datetime] = None
    emailed_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)
        populate_by_name = True  # Allow using both "data" and "metadata"


class NotificationListResponse(BaseModel):
    """Response schema for paginated notification list"""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int


class UnreadCountResponse(BaseModel):
    """Response schema for unread notification count"""
    unread_count: int


class MarkReadRequest(BaseModel):
    """Request to mark notification as read"""
    notification_id: UUID


class NotificationPreferencesResponse(BaseModel):
    """Response schema for notification preferences"""
    user_id: UUID
    email_enabled: bool
    email_frequency: str
    in_app_enabled: bool
    sequel_notifications: bool
    season_notifications: bool
    new_content_notifications: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferencesUpdate(BaseModel):
    """Request to update notification preferences"""
    email_enabled: Optional[bool] = None
    email_frequency: Optional[str] = None
    in_app_enabled: Optional[bool] = None
    sequel_notifications: Optional[bool] = None
    season_notifications: Optional[bool] = None
    new_content_notifications: Optional[bool] = None

    @validator('email_frequency')
    def validate_email_frequency(cls, v):
        """Validate email frequency is one of the allowed values"""
        if v is not None and v not in ['instant', 'daily', 'weekly', 'never']:
            raise ValueError('email_frequency must be one of: instant, daily, weekly, never')
        return v


class UnsubscribeResponse(BaseModel):
    """Response for unsubscribe action"""
    success: bool
    message: str


class NotificationCreateRequest(BaseModel):
    """Request to create a notification (internal/admin use)"""
    type: str
    title: str
    message: str
    media_id: Optional[UUID] = None
    sequel_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = {}

    @validator('type')
    def validate_notification_type(cls, v):
        """Validate notification type"""
        allowed_types = ['sequel_found', 'season_released', 'new_content']
        if v not in allowed_types:
            raise ValueError(f'type must be one of: {", ".join(allowed_types)}')
        return v

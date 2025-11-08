"""
Notification API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
import logging

from app.db.base import get_db
from app.schemas.notification_schemas import (
    NotificationResponse,
    NotificationListResponse,
    UnreadCountResponse,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    UnsubscribeResponse
)
from app.services.notification_service_async import create_notification_service
from app.core.dependencies import get_current_user
from app.core.rate_limiter import get_rate_limiter
from app.db.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
async def get_notifications(
    request: Request,
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's notifications with pagination

    - **unread_only**: Filter for unread notifications
    - **page**: Page number (starts at 1)
    - **page_size**: Items per page (max 100)
    """
    notification_service = create_notification_service(db)

    # Calculate offset
    offset = (page - 1) * page_size

    # Rate limiting check
    limiter = get_rate_limiter()
    rate_limit_key = f"notifications:get_notifications:{current_user.id}"
    allowed, requests_made, retry_after = await limiter.check_rate_limit(
        rate_limit_key, 100, 60
    )
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {retry_after} seconds."
        )

    # Get notifications list
    notifications = await notification_service.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        limit=page_size,
        offset=offset
    )

    # Get total count (query all to get accurate count - can be optimized later with COUNT query)
    all_notifications = await notification_service.get_user_notifications(
        user_id=current_user.id,
        unread_only=False,
        limit=10000,  # Large number to get all
        offset=0
    )
    total_count = len(all_notifications)
    unread_count = len([n for n in all_notifications if n.read_at is None])

    return {
        "items": [NotificationResponse.from_orm(n).dict() for n in notifications],
        "total": total_count,
        "unread_count": unread_count,
        "page": page,
        "limit": page_size
    }


@router.get("/unread", response_model=UnreadCountResponse)
async def get_unread_count(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get count of unread notifications

    Returns the number of unread notifications for the current user.
    """
    notification_service = create_notification_service(db)
    unread_count = await notification_service.get_unread_count_async(current_user.id)

    return UnreadCountResponse(unread_count=unread_count)


@router.put("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_as_read(
    request: Request,
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a specific notification as read

    - **notification_id**: UUID of the notification to mark as read
    """
    notification_service = create_notification_service(db)

    success = notification_service.mark_as_read(
        notification_id=notification_id,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied"
        )

    return None


@router.put("/mark-all-read", response_model=dict)
async def mark_all_notifications_as_read(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark all notifications as read for the current user

    Returns the number of notifications that were marked as read.
    """
    notification_service = create_notification_service(db)

    count = notification_service.mark_all_as_read(current_user.id)

    return {"marked_read": count, "message": f"{count} notification(s) marked as read"}


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's notification preferences

    Returns all notification settings for the current user.
    """
    notification_service = create_notification_service(db)

    preferences = await notification_service.get_notification_preferences(current_user.id)
    
    if not preferences:
        # Create default preferences if none exist
        preferences = await notification_service.update_notification_preferences(
            current_user.id,
            email_enabled=True,
            email_frequency="weekly"
        )

    return NotificationPreferencesResponse.from_orm(preferences)


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    request: Request,
    preferences_update: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user's notification preferences

    Update any subset of notification preferences. Only provided fields will be updated.
    """
    notification_service = create_notification_service(db)

    # Convert to dict, excluding None values
    update_data = preferences_update.dict(exclude_unset=True, exclude_none=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No preferences provided for update"
        )

    preferences = await notification_service.update_notification_preferences(
        user_id=current_user.id,
        **update_data
    )

    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )

    return NotificationPreferencesResponse.from_orm(preferences)


@router.get("/unsubscribe", response_model=UnsubscribeResponse)
async def unsubscribe_from_emails(
    token: str = Query(..., description="Unsubscribe token from email"),
    db: AsyncSession = Depends(get_db)
):
    """
    Unsubscribe from email notifications using token

    This endpoint is typically accessed via link in notification emails.
    No authentication required - token provides authorization.

    - **token**: Unsubscribe token from email link
    """
    notification_service = create_notification_service(db)

    success = notification_service.unsubscribe_from_emails(token)

    if success:
        return UnsubscribeResponse(
            success=True,
            message="You have been successfully unsubscribed from email notifications. You can re-enable them in your account settings."
        )
    else:
        return UnsubscribeResponse(
            success=False,
            message="Invalid or expired unsubscribe link. Please check your account settings to manage notifications."
        )


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    request: Request,
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a specific notification

    - **notification_id**: UUID of the notification to delete
    """
    from app.db.models import Notification
    from sqlalchemy import and_

    # Find and verify ownership
    notification = db.query(Notification).filter(
        and_(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied"
        )

    db.delete(notification)
    db.commit()

    logger.info(f"Deleted notification {notification_id} for user {current_user.id}")

    return None

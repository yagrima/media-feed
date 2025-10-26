"""
Complete Async Notification Service
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, func, update, delete
from datetime import datetime, timedelta
import logging
import uuid
import hmac
import hashlib

from app.db.models import (
    Notification,
    NotificationPreferences,
    User,
    Media,
    UserMedia
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Complete Async Service for creating and managing user notifications"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_notifications(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """Get user notifications with pagination and filtering"""
        try:
            query = select(Notification).where(Notification.user_id == user_id)
            
            if unread_only:
                query = query.where(Notification.read_at.is_(None))
            
            query = query.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to get notifications: {str(e)}")
            return []

    async def mark_notification_as_read(
        self,
        user_id: uuid.UUID,
        notification_id: uuid.UUID
    ) -> bool:
        """Mark a specific notification as read"""
        try:
            update_stmt = update(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                    Notification.read_at.is_(None)
                )
            ).values(read_at=datetime.utcnow())
            
            result = await self.db.execute(update_stmt)
            await self.db.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {str(e)}")
            await self.db.rollback()
            return False

    async def mark_all_notifications_read(
        self,
        user_id: uuid.UUID
    ) -> int:
        """Mark all notifications as read for user, returns count"""
        try:
            update_stmt = update(Notification).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.read_at.is_(None)
                )
            ).values(read_at=datetime.utcnow())
            
            result = await self.db.execute(update_stmt)
            await self.db.commit()
            
            return result.rowcount
            
        except Exception as e:
            logger.error(f"Failed to mark all notifications as read: {str(e)}")
            await self.db.rollback()
            return 0

    async def get_notification_preferences(
        self,
        user_id: uuid.UUID
    ) -> Optional[NotificationPreferences]:
        """Get user notification preferences"""
        try:
            query = select(NotificationPreferences).where(NotificationPreferences.user_id == user_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get notification preferences: {str(e)}")
            return None

    async def update_notification_preferences(
        self,
        user_id: uuid.UUID,
        email_enabled: Optional[bool] = None,
        email_frequency: Optional[str] = None
    ) -> Optional[NotificationPreferences]:
        """Update user notification preferences"""
        try:
            # Get existing preferences or create new
            query = select(NotificationPreferences).where(NotificationPreferences.user_id == user_id)
            result = await self.db.execute(query)
            preferences = result.scalar_one_or_none()
            
            if not preferences:
                preferences = NotificationPreferences(user_id=user_id)
                self.db.add(preferences)
            
            # Update provided fields
            if email_enabled is not None:
                preferences.email_enabled = email_enabled
            if email_frequency is not None:
                preferences.email_frequency = email_frequency
            
            preferences.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(preferences)
            
            return preferences
            
        except Exception as e:
            logger.error(f"Failed to update notification preferences: {str(e)}")
            await self.db.rollback()
            return None

    async def delete_notification(
        self,
        user_id: uuid.UUID,
        notification_id: uuid.UUID
    ) -> bool:
        """Delete a specific notification"""
        try:
            delete_stmt = delete(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            )
            
            result = await self.db.execute(delete_stmt)
            await self.db.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            logger.error(f"Failed to delete notification: {str(e)}")
            await self.db.rollback()
            return False

    async def unsubscribe_from_emails(self, token: str) -> bool:
        """Unsubscribe from email notifications using token"""
        try:
            query = select(Notification).where(
                and_(
                    Notification.unsubscribe_token == token,
                    Notification.unsubscribe_token_expires > datetime.utcnow()
                )
            )
            result = await self.db.execute(query)
            notification = result.scalar_one_or_none()
            
            if not notification:
                logger.warning("Invalid or expired unsubscribe token")
                return False
            
            # Disable email notifications
            update_stmt = update(NotificationPreferences).where(
                NotificationPreferences.user_id == notification.user_id
            ).values(email_enabled=False, updated_at=datetime.utcnow())
            
            await self.db.execute(update_stmt)
            await self.db.commit()
            
            logger.info(f"User {notification.user_id} unsubscribed from email notifications")
            return True
            
        except Exception as e:
            logger.error(f"Unsubscribe failed: {str(e)}")
            await self.db.rollback()
            return False

    def _generate_unsubscribe_token(self, user_id: uuid.UUID) -> str:
        """Generate secure unsubscribe token"""
        message = f"{user_id}:{settings.APP_NAME}".encode()
        signature = hmac.new(
            settings.SECRET_KEY.encode(),
            message,
            hashlib.sha256
        ).hexdigest()
        return f"{user_id}:{signature}"


def create_notification_service(db: AsyncSession) -> NotificationService:
    """Create notification service instance"""
    return NotificationService(db)

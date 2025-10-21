"""
Notification creation and management service
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
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
    """Service for creating and managing user notifications"""

    def __init__(self, db: Session):
        self.db = db

    def create_sequel_notification(
        self,
        user_id: uuid.UUID,
        original_media_id: uuid.UUID,
        sequel_media_id: uuid.UUID,
        confidence: float,
        reason: str
    ) -> Optional[Notification]:
        """
        Create a notification for a detected sequel

        Args:
            user_id: User's UUID
            original_media_id: Original media they watched
            sequel_media_id: Detected sequel
            confidence: Match confidence (0.0-1.0)
            reason: Detection reason/explanation

        Returns:
            Notification object or None if duplicate
        """
        try:
            # Check if notification already exists (duplicate prevention)
            existing = self.db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.media_id == original_media_id,
                    Notification.sequel_id == sequel_media_id,
                    Notification.type == 'sequel_found'
                )
            ).first()

            if existing:
                logger.info(f"Duplicate notification skipped for user {user_id}")
                return None

            # Get media details
            sequel = self.db.query(Media).filter(Media.id == sequel_media_id).first()
            original = self.db.query(Media).filter(Media.id == original_media_id).first()

            if not sequel or not original:
                logger.error(f"Media not found: sequel={sequel_media_id}, original={original_media_id}")
                return None

            # Create notification
            notification = Notification(
                user_id=user_id,
                type='sequel_found',
                title=f"New sequel: {sequel.title}",
                message=f"We found a sequel to '{original.title}' that you watched.",
                media_id=original_media_id,
                sequel_id=sequel_media_id,
                metadata={
                    'confidence': confidence,
                    'reason': reason,
                    'sequel_title': sequel.title,
                    'original_title': original.title,
                    'platform': sequel.platform,
                    'release_date': sequel.release_date.isoformat() if sequel.release_date else None,
                    'poster_url': sequel.poster_url
                },
                unsubscribe_token=self._generate_unsubscribe_token(user_id),
                unsubscribe_token_expires=datetime.utcnow() + timedelta(days=30)
            )

            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)

            logger.info(f"Created sequel notification for user {user_id}: {sequel.title}")
            return notification

        except Exception as e:
            logger.error(f"Failed to create sequel notification: {str(e)}")
            self.db.rollback()
            return None

    def create_bulk_notifications(
        self,
        user_id: uuid.UUID,
        sequels: List[Dict[str, Any]]
    ) -> List[Notification]:
        """
        Create multiple notifications for a batch of sequels

        Args:
            user_id: User's UUID
            sequels: List of sequel dictionaries with metadata

        Returns:
            List of created Notification objects
        """
        created_notifications = []

        for sequel_data in sequels:
            notification = self.create_sequel_notification(
                user_id=user_id,
                original_media_id=sequel_data['original_media_id'],
                sequel_media_id=sequel_data['sequel_media_id'],
                confidence=sequel_data.get('confidence', 0.0),
                reason=sequel_data.get('reason', 'Sequel detected')
            )

            if notification:
                created_notifications.append(notification)

        logger.info(f"Created {len(created_notifications)} notifications for user {user_id}")
        return created_notifications

    def get_user_notifications(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """
        Get notifications for a user

        Args:
            user_id: User's UUID
            unread_only: Only return unread notifications
            limit: Maximum number of notifications
            offset: Pagination offset

        Returns:
            List of Notification objects
        """
        query = self.db.query(Notification).filter(Notification.user_id == user_id)

        if unread_only:
            query = query.filter(Notification.is_read == False)

        notifications = query.order_by(Notification.created_at.desc()).limit(limit).offset(offset).all()

        return notifications

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        """Get count of unread notifications for a user"""
        from sqlalchemy import select, func
        stmt = select(func.count()).select_from(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    def mark_as_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Mark a notification as read

        Args:
            notification_id: Notification UUID
            user_id: User UUID (for ownership verification)

        Returns:
            bool: True if successful
        """
        try:
            notification = self.db.query(Notification).filter(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            ).first()

            if not notification:
                logger.warning(f"Notification {notification_id} not found or not owned by user {user_id}")
                return False

            notification.is_read = True
            notification.read_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Marked notification {notification_id} as read")
            return True

        except Exception as e:
            logger.error(f"Failed to mark notification as read: {str(e)}")
            self.db.rollback()
            return False

    def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        """
        Mark all notifications as read for a user

        Args:
            user_id: User UUID

        Returns:
            int: Number of notifications marked as read
        """
        try:
            updated_count = self.db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            ).update({
                'is_read': True,
                'read_at': datetime.utcnow()
            })

            self.db.commit()
            logger.info(f"Marked {updated_count} notifications as read for user {user_id}")
            return updated_count

        except Exception as e:
            logger.error(f"Failed to mark all notifications as read: {str(e)}")
            self.db.rollback()
            return 0

    def mark_as_emailed(self, notification_id: uuid.UUID) -> bool:
        """Mark notification as emailed (internal use)"""
        try:
            notification = self.db.query(Notification).filter(
                Notification.id == notification_id
            ).first()

            if not notification:
                return False

            notification.emailed = True
            notification.emailed_at = datetime.utcnow()
            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to mark notification as emailed: {str(e)}")
            self.db.rollback()
            return False

    def get_or_create_preferences(self, user_id: uuid.UUID) -> NotificationPreferences:
        """
        Get or create notification preferences for a user

        Args:
            user_id: User UUID

        Returns:
            NotificationPreferences object
        """
        preferences = self.db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == user_id
        ).first()

        if not preferences:
            preferences = NotificationPreferences(user_id=user_id)
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)
            logger.info(f"Created default notification preferences for user {user_id}")

        return preferences

    def update_preferences(
        self,
        user_id: uuid.UUID,
        **kwargs
    ) -> Optional[NotificationPreferences]:
        """
        Update notification preferences for a user

        Args:
            user_id: User UUID
            **kwargs: Preference fields to update

        Returns:
            Updated NotificationPreferences or None
        """
        try:
            preferences = self.get_or_create_preferences(user_id)

            # Update allowed fields
            allowed_fields = [
                'email_enabled', 'email_frequency', 'in_app_enabled',
                'sequel_notifications', 'season_notifications', 'new_content_notifications'
            ]

            for field, value in kwargs.items():
                if field in allowed_fields and hasattr(preferences, field):
                    setattr(preferences, field, value)

            preferences.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(preferences)

            logger.info(f"Updated notification preferences for user {user_id}")
            return preferences

        except Exception as e:
            logger.error(f"Failed to update preferences: {str(e)}")
            self.db.rollback()
            return None

    def validate_unsubscribe_token(self, token: str, user_id: uuid.UUID) -> bool:
        """
        Validate an unsubscribe token

        Args:
            token: Unsubscribe token
            user_id: User UUID

        Returns:
            bool: True if valid
        """
        try:
            expected_token = self._generate_unsubscribe_token(user_id)

            # Constant-time comparison to prevent timing attacks
            return hmac.compare_digest(token, expected_token)

        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            return False

    def unsubscribe_from_emails(self, token: str) -> bool:
        """
        Unsubscribe user from email notifications using token

        Args:
            token: Unsubscribe token

        Returns:
            bool: True if successful
        """
        try:
            # Find notification with this token
            notification = self.db.query(Notification).filter(
                and_(
                    Notification.unsubscribe_token == token,
                    Notification.unsubscribe_token_expires > datetime.utcnow()
                )
            ).first()

            if not notification:
                logger.warning("Invalid or expired unsubscribe token")
                return False

            # Disable email notifications for this user
            preferences = self.get_or_create_preferences(notification.user_id)
            preferences.email_enabled = False
            preferences.updated_at = datetime.utcnow()

            self.db.commit()
            logger.info(f"User {notification.user_id} unsubscribed from email notifications")
            return True

        except Exception as e:
            logger.error(f"Unsubscribe failed: {str(e)}")
            self.db.rollback()
            return False

    def _generate_unsubscribe_token(self, user_id: uuid.UUID) -> str:
        """
        Generate a secure unsubscribe token for a user

        Args:
            user_id: User UUID

        Returns:
            str: HMAC-signed token
        """
        # Create HMAC signature using user_id and secret key
        message = f"{user_id}:{settings.APP_NAME}".encode()
        signature = hmac.new(
            settings.SECRET_KEY.encode(),
            message,
            hashlib.sha256
        ).hexdigest()

        # Token format: user_id:signature
        return f"{user_id}:{signature}"


def create_notification_service(db: Session) -> NotificationService:
    """Factory function to create NotificationService instance"""
    return NotificationService(db)

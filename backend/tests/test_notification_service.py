"""
Unit tests for NotificationService.
Tests notification creation, duplicate prevention, preferences, and unsubscribe functionality.
"""

import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import uuid4, UUID
import hmac
import hashlib

from app.db.models import (
    User,
    Media,
    Notification,
    NotificationPreferences
)
from app.services.notification_service import NotificationService
from app.core.config import settings


@pytest.fixture
def test_user(db: Session):
    """Create test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        email_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user2(db: Session):
    """Create second test user."""
    user = User(
        id=uuid4(),
        email="test2@example.com",
        password_hash="hashed_password",
        email_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_media_original(db: Session):
    """Create original media."""
    media = Media(
        id=uuid4(),
        title="Stranger Things: Season 1",
        base_title="Stranger Things",
        season_number=1,
        type='tv_series',
        platform='netflix',
        release_date=datetime(2016, 7, 15)
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


@pytest.fixture
def test_media_sequel(db: Session):
    """Create sequel media."""
    media = Media(
        id=uuid4(),
        title="Stranger Things: Season 2",
        base_title="Stranger Things",
        season_number=2,
        type='tv_series',
        platform='netflix',
        release_date=datetime(2017, 10, 27),
        poster_url="https://image.tmdb.org/t/p/w500/poster.jpg"
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


@pytest.fixture
def notification_service(db: Session):
    """Create NotificationService instance."""
    return NotificationService(db)


class TestNotificationCreation:
    """Test notification creation functionality."""

    def test_create_sequel_notification_success(
        self,
        notification_service: NotificationService,
        test_user: User,
        test_media_original: Media,
        test_media_sequel: Media,
        db: Session
    ):
        """Test successful sequel notification creation."""
        notification = notification_service.create_sequel_notification(
            user_id=test_user.id,
            original_media_id=test_media_original.id,
            sequel_media_id=test_media_sequel.id,
            confidence=0.95,
            reason="Season number increment detected"
        )

        assert notification is not None
        assert notification.user_id == test_user.id
        assert notification.type == 'sequel_found'
        assert notification.media_id == test_media_original.id
        assert notification.sequel_id == test_media_sequel.id
        assert notification.read is False
        assert notification.emailed is False

        # Check metadata
        assert notification.metadata['confidence'] == 0.95
        assert notification.metadata['reason'] == "Season number increment detected"
        assert notification.metadata['sequel_title'] == "Stranger Things: Season 2"
        assert notification.metadata['original_title'] == "Stranger Things: Season 1"
        assert notification.metadata['platform'] == 'netflix'
        assert notification.metadata['poster_url'] is not None

        # Check unsubscribe token
        assert notification.unsubscribe_token is not None
        assert notification.unsubscribe_token_expires is not None
        assert notification.unsubscribe_token_expires > datetime.utcnow()

    def test_create_duplicate_notification_prevented(
        self,
        notification_service: NotificationService,
        test_user: User,
        test_media_original: Media,
        test_media_sequel: Media,
        db: Session
    ):
        """Test that duplicate notifications are prevented."""
        # Create first notification
        first = notification_service.create_sequel_notification(
            user_id=test_user.id,
            original_media_id=test_media_original.id,
            sequel_media_id=test_media_sequel.id,
            confidence=0.95,
            reason="First detection"
        )
        assert first is not None

        # Attempt to create duplicate
        duplicate = notification_service.create_sequel_notification(
            user_id=test_user.id,
            original_media_id=test_media_original.id,
            sequel_media_id=test_media_sequel.id,
            confidence=0.90,
            reason="Second detection (should be blocked)"
        )
        assert duplicate is None

        # Verify only one notification exists
        notifications = db.query(Notification).filter(
            Notification.user_id == test_user.id
        ).all()
        assert len(notifications) == 1

    def test_create_notification_missing_media(
        self,
        notification_service: NotificationService,
        test_user: User,
        db: Session
    ):
        """Test notification creation with non-existent media."""
        fake_media_id = uuid4()

        notification = notification_service.create_sequel_notification(
            user_id=test_user.id,
            original_media_id=fake_media_id,
            sequel_media_id=uuid4(),
            confidence=0.95,
            reason="Test"
        )

        assert notification is None

    def test_create_bulk_notifications(
        self,
        notification_service: NotificationService,
        test_user: User,
        db: Session
    ):
        """Test bulk notification creation."""
        # Create test media
        media_original = Media(
            id=uuid4(),
            title="Test Show: Season 1",
            base_title="Test Show",
            season_number=1,
            type='tv_series',
            platform='netflix'
        )
        media_sequel1 = Media(
            id=uuid4(),
            title="Test Show: Season 2",
            base_title="Test Show",
            season_number=2,
            type='tv_series',
            platform='netflix'
        )
        media_sequel2 = Media(
            id=uuid4(),
            title="Test Show: Season 3",
            base_title="Test Show",
            season_number=3,
            type='tv_series',
            platform='netflix'
        )
        db.add_all([media_original, media_sequel1, media_sequel2])
        db.commit()

        # Create bulk notifications
        sequels = [
            {
                'original_media_id': media_original.id,
                'sequel_media_id': media_sequel1.id,
                'confidence': 0.95,
                'reason': 'Season 2'
            },
            {
                'original_media_id': media_original.id,
                'sequel_media_id': media_sequel2.id,
                'confidence': 0.95,
                'reason': 'Season 3'
            }
        ]

        created = notification_service.create_bulk_notifications(
            user_id=test_user.id,
            sequels=sequels
        )

        assert len(created) == 2
        assert all(n.user_id == test_user.id for n in created)


class TestNotificationRetrieval:
    """Test notification retrieval functionality."""

    def test_get_user_notifications(
        self,
        notification_service: NotificationService,
        test_user: User,
        test_user2: User,
        test_media_original: Media,
        test_media_sequel: Media,
        db: Session
    ):
        """Test retrieving user's notifications."""
        # Create notifications for user 1
        for i in range(3):
            notification_service.create_sequel_notification(
                user_id=test_user.id,
                original_media_id=test_media_original.id,
                sequel_media_id=test_media_sequel.id,
                confidence=0.95,
                reason=f"Test {i}"
            )
            # Create different sequel for each iteration to avoid duplicates
            test_media_sequel = Media(
                id=uuid4(),
                title=f"Sequel {i}",
                base_title="Test",
                type='tv_series',
                platform='netflix'
            )
            db.add(test_media_sequel)
            db.commit()

        # Get notifications
        notifications = notification_service.get_user_notifications(
            user_id=test_user.id,
            limit=50
        )

        assert len(notifications) == 3
        assert all(n.user_id == test_user.id for n in notifications)

    def test_get_unread_notifications_only(
        self,
        notification_service: NotificationService,
        test_user: User,
        test_media_original: Media,
        test_media_sequel: Media,
        db: Session
    ):
        """Test filtering for unread notifications only."""
        # Create notification and mark as read
        n1 = notification_service.create_sequel_notification(
            user_id=test_user.id,
            original_media_id=test_media_original.id,
            sequel_media_id=test_media_sequel.id,
            confidence=0.95,
            reason="Read notification"
        )
        notification_service.mark_as_read(n1.id, test_user.id)

        # Create unread notification
        sequel2 = Media(
            id=uuid4(),
            title="Unread Sequel",
            base_title="Test",
            type='tv_series',
            platform='netflix'
        )
        db.add(sequel2)
        db.commit()

        notification_service.create_sequel_notification(
            user_id=test_user.id,
            original_media_id=test_media_original.id,
            sequel_media_id=sequel2.id,
            confidence=0.95,
            reason="Unread notification"
        )

        # Get only unread
        unread = notification_service.get_user_notifications(
            user_id=test_user.id,
            unread_only=True
        )

        assert len(unread) == 1
        assert unread[0].read is False

    def test_get_unread_count(
        self,
        notification_service: NotificationService,
        test_user: User,
        test_media_original: Media,
        db: Session
    ):
        """Test getting unread notification count."""
        # Create 3 unread notifications
        for i in range(3):
            sequel = Media(
                id=uuid4(),
                title=f"Sequel {i}",
                base_title="Test",
                type='tv_series',
                platform='netflix'
            )
            db.add(sequel)
            db.commit()

            notification_service.create_sequel_notification(
                user_id=test_user.id,
                original_media_id=test_media_original.id,
                sequel_media_id=sequel.id,
                confidence=0.95,
                reason=f"Test {i}"
            )

        count = notification_service.get_unread_count(test_user.id)
        assert count == 3

    def test_pagination(
        self,
        notification_service: NotificationService,
        test_user: User,
        test_media_original: Media,
        db: Session
    ):
        """Test pagination of notifications."""
        # Create 10 notifications
        for i in range(10):
            sequel = Media(
                id=uuid4(),
                title=f"Sequel {i}",
                base_title="Test",
                type='tv_series',
                platform='netflix'
            )
            db.add(sequel)
            db.commit()

            notification_service.create_sequel_notification(
                user_id=test_user.id,
                original_media_id=test_media_original.id,
                sequel_media_id=sequel.id,
                confidence=0.95,
                reason=f"Test {i}"
            )

        # Get first page (5 items)
        page1 = notification_service.get_user_notifications(
            user_id=test_user.id,
            limit=5,
            offset=0
        )
        assert len(page1) == 5

        # Get second page (5 items)
        page2 = notification_service.get_user_notifications(
            user_id=test_user.id,
            limit=5,
            offset=5
        )
        assert len(page2) == 5

        # Verify no overlap
        page1_ids = {n.id for n in page1}
        page2_ids = {n.id for n in page2}
        assert len(page1_ids.intersection(page2_ids)) == 0


class TestNotificationUpdates:
    """Test notification update functionality."""

    def test_mark_as_read(
        self,
        notification_service: NotificationService,
        test_user: User,
        test_media_original: Media,
        test_media_sequel: Media,
        db: Session
    ):
        """Test marking notification as read."""
        notification = notification_service.create_sequel_notification(
            user_id=test_user.id,
            original_media_id=test_media_original.id,
            sequel_media_id=test_media_sequel.id,
            confidence=0.95,
            reason="Test"
        )

        assert notification.read is False
        assert notification.read_at is None

        # Mark as read
        success = notification_service.mark_as_read(
            notification_id=notification.id,
            user_id=test_user.id
        )

        assert success is True

        # Verify update
        db.refresh(notification)
        assert notification.read is True
        assert notification.read_at is not None

    def test_mark_as_read_wrong_user(
        self,
        notification_service: NotificationService,
        test_user: User,
        test_user2: User,
        test_media_original: Media,
        test_media_sequel: Media,
        db: Session
    ):
        """Test marking notification as read with wrong user (ownership check)."""
        notification = notification_service.create_sequel_notification(
            user_id=test_user.id,
            original_media_id=test_media_original.id,
            sequel_media_id=test_media_sequel.id,
            confidence=0.95,
            reason="Test"
        )

        # Attempt to mark as read with different user
        success = notification_service.mark_as_read(
            notification_id=notification.id,
            user_id=test_user2.id
        )

        assert success is False

        # Verify notification still unread
        db.refresh(notification)
        assert notification.read is False

    def test_mark_all_as_read(
        self,
        notification_service: NotificationService,
        test_user: User,
        test_media_original: Media,
        db: Session
    ):
        """Test marking all notifications as read."""
        # Create 5 notifications
        for i in range(5):
            sequel = Media(
                id=uuid4(),
                title=f"Sequel {i}",
                base_title="Test",
                type='tv_series',
                platform='netflix'
            )
            db.add(sequel)
            db.commit()

            notification_service.create_sequel_notification(
                user_id=test_user.id,
                original_media_id=test_media_original.id,
                sequel_media_id=sequel.id,
                confidence=0.95,
                reason=f"Test {i}"
            )

        # Mark all as read
        count = notification_service.mark_all_as_read(test_user.id)
        assert count == 5

        # Verify all marked as read
        unread_count = notification_service.get_unread_count(test_user.id)
        assert unread_count == 0

    def test_mark_as_emailed(
        self,
        notification_service: NotificationService,
        test_user: User,
        test_media_original: Media,
        test_media_sequel: Media,
        db: Session
    ):
        """Test marking notification as emailed."""
        notification = notification_service.create_sequel_notification(
            user_id=test_user.id,
            original_media_id=test_media_original.id,
            sequel_media_id=test_media_sequel.id,
            confidence=0.95,
            reason="Test"
        )

        assert notification.emailed is False
        assert notification.emailed_at is None

        # Mark as emailed
        success = notification_service.mark_as_emailed(notification.id)
        assert success is True

        # Verify update
        db.refresh(notification)
        assert notification.emailed is True
        assert notification.emailed_at is not None


class TestNotificationPreferences:
    """Test notification preferences functionality."""

    def test_get_or_create_preferences_creates_new(
        self,
        notification_service: NotificationService,
        test_user: User,
        db: Session
    ):
        """Test creating new preferences for user."""
        preferences = notification_service.get_or_create_preferences(test_user.id)

        assert preferences is not None
        assert preferences.user_id == test_user.id
        assert preferences.email_enabled is True
        assert preferences.in_app_enabled is True
        assert preferences.sequel_notifications is True

    def test_get_or_create_preferences_returns_existing(
        self,
        notification_service: NotificationService,
        test_user: User,
        db: Session
    ):
        """Test returning existing preferences."""
        # Create preferences
        first = notification_service.get_or_create_preferences(test_user.id)

        # Get again
        second = notification_service.get_or_create_preferences(test_user.id)

        assert first.id == second.id

    def test_update_preferences(
        self,
        notification_service: NotificationService,
        test_user: User,
        db: Session
    ):
        """Test updating notification preferences."""
        preferences = notification_service.update_preferences(
            user_id=test_user.id,
            email_enabled=False,
            email_frequency='weekly',
            sequel_notifications=False
        )

        assert preferences is not None
        assert preferences.email_enabled is False
        assert preferences.email_frequency == 'weekly'
        assert preferences.sequel_notifications is False

    def test_update_preferences_partial(
        self,
        notification_service: NotificationService,
        test_user: User,
        db: Session
    ):
        """Test partial preference updates."""
        # Create initial preferences
        notification_service.get_or_create_preferences(test_user.id)

        # Update only one field
        preferences = notification_service.update_preferences(
            user_id=test_user.id,
            email_frequency='weekly'
        )

        assert preferences.email_frequency == 'weekly'
        # Other defaults should remain
        assert preferences.email_enabled is True


class TestUnsubscribeTokens:
    """Test unsubscribe token functionality."""

    def test_generate_unsubscribe_token(
        self,
        notification_service: NotificationService,
        test_user: User
    ):
        """Test unsubscribe token generation."""
        token = notification_service._generate_unsubscribe_token(test_user.id)

        assert token is not None
        assert ':' in token
        assert str(test_user.id) in token

    def test_validate_unsubscribe_token_valid(
        self,
        notification_service: NotificationService,
        test_user: User
    ):
        """Test validation of valid unsubscribe token."""
        token = notification_service._generate_unsubscribe_token(test_user.id)

        is_valid = notification_service.validate_unsubscribe_token(
            token=token,
            user_id=test_user.id
        )

        assert is_valid is True

    def test_validate_unsubscribe_token_invalid(
        self,
        notification_service: NotificationService,
        test_user: User
    ):
        """Test validation of invalid unsubscribe token."""
        fake_token = f"{test_user.id}:invalid_signature"

        is_valid = notification_service.validate_unsubscribe_token(
            token=fake_token,
            user_id=test_user.id
        )

        assert is_valid is False

    def test_unsubscribe_from_emails_success(
        self,
        notification_service: NotificationService,
        test_user: User,
        test_media_original: Media,
        test_media_sequel: Media,
        db: Session
    ):
        """Test successful email unsubscribe."""
        # Create notification with token
        notification = notification_service.create_sequel_notification(
            user_id=test_user.id,
            original_media_id=test_media_original.id,
            sequel_media_id=test_media_sequel.id,
            confidence=0.95,
            reason="Test"
        )

        # Unsubscribe using token
        success = notification_service.unsubscribe_from_emails(
            notification.unsubscribe_token
        )

        assert success is True

        # Verify preferences updated
        preferences = notification_service.get_or_create_preferences(test_user.id)
        assert preferences.email_enabled is False

    def test_unsubscribe_from_emails_expired_token(
        self,
        notification_service: NotificationService,
        test_user: User,
        test_media_original: Media,
        test_media_sequel: Media,
        db: Session
    ):
        """Test unsubscribe with expired token."""
        # Create notification
        notification = notification_service.create_sequel_notification(
            user_id=test_user.id,
            original_media_id=test_media_original.id,
            sequel_media_id=test_media_sequel.id,
            confidence=0.95,
            reason="Test"
        )

        # Manually expire token
        notification.unsubscribe_token_expires = datetime.utcnow() - timedelta(days=1)
        db.commit()

        # Attempt unsubscribe
        success = notification_service.unsubscribe_from_emails(
            notification.unsubscribe_token
        )

        assert success is False

    def test_unsubscribe_from_emails_invalid_token(
        self,
        notification_service: NotificationService,
        db: Session
    ):
        """Test unsubscribe with invalid token."""
        success = notification_service.unsubscribe_from_emails("invalid_token")
        assert success is False

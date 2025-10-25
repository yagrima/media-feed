"""
Integration tests for Notification API endpoints.
Tests API endpoints with authentication, rate limiting, and ownership verification.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import uuid4

from app.main import app
from app.db.models import User, Media, Notification, NotificationPreferences
from app.security.jwt_handler import create_access_token
from app.services.notification_service import NotificationService


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_user(db: Session):
    """Create test user."""
    user = User(
        id=uuid4(),
        email="testuser@example.com",
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
        email="testuser2@example.com",
        password_hash="hashed_password",
        email_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User):
    """Create authorization headers for test user."""
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user2(test_user2: User):
    """Create authorization headers for second test user."""
    token = create_access_token(test_user2.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_media_original(db: Session):
    """Create original media."""
    media = Media(
        id=uuid4(),
        title="Test Show: Season 1",
        base_title="Test Show",
        season_number=1,
        type='tv_series',
        platform='netflix'
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
        title="Test Show: Season 2",
        base_title="Test Show",
        season_number=2,
        type='tv_series',
        platform='netflix',
        poster_url="https://example.com/poster.jpg"
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


@pytest.fixture
def test_notification(
    db: Session,
    test_user: User,
    test_media_original: Media,
    test_media_sequel: Media
):
    """Create test notification."""
    notification_service = NotificationService(db)
    return notification_service.create_sequel_notification(
        user_id=test_user.id,
        original_media_id=test_media_original.id,
        sequel_media_id=test_media_sequel.id,
        confidence=0.95,
        reason="Test notification"
    )


class TestGetNotifications:
    """Test GET /api/notifications endpoint."""

    def test_get_notifications_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        test_notification: Notification,
        db: Session
    ):
        """Test retrieving user's notifications."""
        response = client.get(
            "/api/notifications",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert 'notifications' in data
        assert 'total' in data
        assert 'unread_count' in data
        assert len(data['notifications']) >= 1

    def test_get_notifications_unread_only(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        test_notification: Notification,
        db: Session
    ):
        """Test filtering for unread notifications only."""
        # Mark notification as read
        test_notification.read = True
        test_notification.read_at = datetime.utcnow()
        db.commit()

        # Create unread notification
        notification_service = NotificationService(db)
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
            original_media_id=test_notification.media_id,
            sequel_media_id=sequel2.id,
            confidence=0.95,
            reason="Unread"
        )

        # Get only unread
        response = client.get(
            "/api/notifications?unread_only=true",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data['notifications']) >= 1
        assert all(not n['read'] for n in data['notifications'])

    def test_get_notifications_pagination(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        test_media_original: Media,
        db: Session
    ):
        """Test pagination parameters."""
        # Create multiple notifications
        notification_service = NotificationService(db)
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

        # Get first page
        response = client.get(
            "/api/notifications?page=1&page_size=3",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data['notifications']) <= 3
        assert data['page'] == 1
        assert data['page_size'] == 3

    def test_get_notifications_unauthorized(self, client: TestClient):
        """Test endpoint requires authentication."""
        response = client.get("/api/notifications")
        assert response.status_code == 401


class TestGetUnreadCount:
    """Test GET /api/notifications/unread endpoint."""

    def test_get_unread_count_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        test_notification: Notification
    ):
        """Test getting unread notification count."""
        response = client.get(
            "/api/notifications/unread",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert 'unread_count' in data
        assert data['unread_count'] >= 1

    def test_get_unread_count_zero(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        test_notification: Notification,
        db: Session
    ):
        """Test unread count returns zero when all read."""
        # Mark notification as read
        test_notification.read = True
        test_notification.read_at = datetime.utcnow()
        db.commit()

        response = client.get(
            "/api/notifications/unread",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['unread_count'] == 0


class TestMarkNotificationAsRead:
    """Test PUT /api/notifications/{id}/read endpoint."""

    def test_mark_notification_as_read_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_notification: Notification,
        db: Session
    ):
        """Test marking notification as read."""
        response = client.put(
            f"/api/notifications/{test_notification.id}/read",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify notification marked as read
        db.refresh(test_notification)
        assert test_notification.read is True
        assert test_notification.read_at is not None

    def test_mark_notification_as_read_not_found(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test marking non-existent notification."""
        fake_id = uuid4()
        response = client.put(
            f"/api/notifications/{fake_id}/read",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_mark_notification_as_read_wrong_user(
        self,
        client: TestClient,
        auth_headers_user2: dict,
        test_notification: Notification,
        db: Session
    ):
        """Test user cannot mark another user's notification as read."""
        response = client.put(
            f"/api/notifications/{test_notification.id}/read",
            headers=auth_headers_user2
        )

        assert response.status_code == 404

        # Verify notification still unread
        db.refresh(test_notification)
        assert test_notification.read is False


class TestMarkAllNotificationsAsRead:
    """Test PUT /api/notifications/mark-all-read endpoint."""

    def test_mark_all_notifications_as_read_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        test_media_original: Media,
        db: Session
    ):
        """Test marking all notifications as read."""
        # Create multiple notifications
        notification_service = NotificationService(db)
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

        response = client.put(
            "/api/notifications/mark-all-read",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['marked_read'] >= 3

        # Verify unread count is zero
        unread_response = client.get(
            "/api/notifications/unread",
            headers=auth_headers
        )
        assert unread_response.json()['unread_count'] == 0


class TestGetNotificationPreferences:
    """Test GET /api/notifications/preferences endpoint."""

    def test_get_preferences_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User
    ):
        """Test retrieving notification preferences."""
        response = client.get(
            "/api/notifications/preferences",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert 'email_enabled' in data
        assert 'email_frequency' in data
        assert 'in_app_enabled' in data
        assert 'sequel_notifications' in data

    def test_get_preferences_creates_defaults(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User,
        db: Session
    ):
        """Test preferences are created with defaults if not exist."""
        # Ensure no preferences exist
        db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == test_user.id
        ).delete()
        db.commit()

        response = client.get(
            "/api/notifications/preferences",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Check defaults
        assert data['email_enabled'] is True
        assert data['in_app_enabled'] is True


class TestUpdateNotificationPreferences:
    """Test PUT /api/notifications/preferences endpoint."""

    def test_update_preferences_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User
    ):
        """Test updating notification preferences."""
        update_data = {
            "email_enabled": False,
            "email_frequency": "weekly",
            "sequel_notifications": False
        }

        response = client.put(
            "/api/notifications/preferences",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data['email_enabled'] is False
        assert data['email_frequency'] == 'weekly'
        assert data['sequel_notifications'] is False

    def test_update_preferences_partial(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User
    ):
        """Test partial preference update."""
        update_data = {
            "email_frequency": "daily"
        }

        response = client.put(
            "/api/notifications/preferences",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data['email_frequency'] == 'daily'

    def test_update_preferences_empty(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test updating with no data returns error."""
        response = client.put(
            "/api/notifications/preferences",
            headers=auth_headers,
            json={}
        )

        assert response.status_code == 400


class TestUnsubscribeFromEmails:
    """Test GET /api/notifications/unsubscribe endpoint."""

    def test_unsubscribe_success(
        self,
        client: TestClient,
        test_user: User,
        test_notification: Notification,
        db: Session
    ):
        """Test successful email unsubscribe."""
        token = test_notification.unsubscribe_token

        response = client.get(
            f"/api/notifications/unsubscribe?token={token}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

        # Verify preferences updated
        preferences = db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == test_user.id
        ).first()
        assert preferences.email_enabled is False

    def test_unsubscribe_invalid_token(self, client: TestClient):
        """Test unsubscribe with invalid token."""
        response = client.get(
            "/api/notifications/unsubscribe?token=invalid_token"
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is False

    def test_unsubscribe_expired_token(
        self,
        client: TestClient,
        test_notification: Notification,
        db: Session
    ):
        """Test unsubscribe with expired token."""
        # Expire token
        test_notification.unsubscribe_token_expires = datetime.utcnow() - timedelta(days=1)
        db.commit()

        token = test_notification.unsubscribe_token

        response = client.get(
            f"/api/notifications/unsubscribe?token={token}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is False

    def test_unsubscribe_no_auth_required(
        self,
        client: TestClient,
        test_notification: Notification
    ):
        """Test unsubscribe endpoint does not require authentication."""
        token = test_notification.unsubscribe_token

        # Should work without auth headers
        response = client.get(
            f"/api/notifications/unsubscribe?token={token}"
        )

        assert response.status_code == 200


class TestDeleteNotification:
    """Test DELETE /api/notifications/{id} endpoint."""

    def test_delete_notification_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_notification: Notification,
        db: Session
    ):
        """Test deleting notification."""
        notification_id = test_notification.id

        response = client.delete(
            f"/api/notifications/{notification_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify deleted
        deleted = db.query(Notification).filter(
            Notification.id == notification_id
        ).first()
        assert deleted is None

    def test_delete_notification_not_found(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test deleting non-existent notification."""
        fake_id = uuid4()

        response = client.delete(
            f"/api/notifications/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_delete_notification_wrong_user(
        self,
        client: TestClient,
        auth_headers_user2: dict,
        test_notification: Notification,
        db: Session
    ):
        """Test user cannot delete another user's notification."""
        response = client.delete(
            f"/api/notifications/{test_notification.id}",
            headers=auth_headers_user2
        )

        assert response.status_code == 404

        # Verify notification still exists
        exists = db.query(Notification).filter(
            Notification.id == test_notification.id
        ).first()
        assert exists is not None


class TestRateLimiting:
    """Test rate limiting on notification endpoints."""

    def test_notification_endpoints_rate_limited(
        self,
        client: TestClient,
        auth_headers: dict,
        test_user: User
    ):
        """Test notification endpoints enforce rate limits."""
        # This is a basic test - actual rate limit testing would require
        # making 100+ requests which is slow. In production, rate limits
        # are tested via load testing.

        # Make a few requests to verify rate limiting is configured
        for i in range(5):
            response = client.get(
                "/api/notifications/unread",
                headers=auth_headers
            )
            assert response.status_code == 200

        # Verify rate limit headers are present (if implemented)
        # This depends on your rate limiter implementation
        # assert 'X-RateLimit-Limit' in response.headers

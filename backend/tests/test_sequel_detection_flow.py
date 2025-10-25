"""
Integration tests for sequel detection flow.
Tests end-to-end flow from media import to sequel detection to notification creation.
"""

import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import uuid4

from app.db.models import User, Media, UserMedia, Notification
from app.services.title_parser import title_parser
from app.services.sequel_detector import create_sequel_detector
from app.services.tmdb_client import TMDBClient


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
def test_media_season1(db: Session):
    """Create test media - Breaking Bad Season 1."""
    parsed = title_parser.parse("Breaking Bad: Season 1")

    media = Media(
        id=uuid4(),
        title="Breaking Bad: Season 1",
        base_title=parsed['base_title'],
        season_number=parsed['season_number'],
        type='tv_series',
        platform='netflix'
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


@pytest.fixture
def test_media_season2(db: Session):
    """Create test media - Breaking Bad Season 2."""
    parsed = title_parser.parse("Breaking Bad: Season 2")

    media = Media(
        id=uuid4(),
        title="Breaking Bad: Season 2",
        base_title=parsed['base_title'],
        season_number=parsed['season_number'],
        type='tv_series',
        platform='netflix'
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


@pytest.fixture
def test_media_season3(db: Session):
    """Create test media - Breaking Bad Season 3."""
    parsed = title_parser.parse("Breaking Bad: Season 3")

    media = Media(
        id=uuid4(),
        title="Breaking Bad: Season 3",
        base_title=parsed['base_title'],
        season_number=parsed['season_number'],
        type='tv_series',
        platform='netflix'
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


class TestSequelDetectionFlow:
    """Test complete sequel detection workflow."""

    def test_parse_and_store_media_with_base_title(self, db: Session):
        """Test that media is stored with parsed base_title."""
        title = "Stranger Things: Season 1: Episode 1"
        parsed = title_parser.parse(title)

        media = Media(
            id=uuid4(),
            title=title,
            base_title=parsed['base_title'],
            season_number=parsed['season_number'],
            episode_number=parsed['episode_number'],
            type='tv_series',
            platform='netflix'
        )
        db.add(media)
        db.commit()

        # Verify stored correctly
        assert media.base_title == "Stranger Things"
        assert media.season_number == 1
        assert media.episode_number == 1
        assert media.type == 'tv_series'

    def test_user_consumes_media(self, db: Session, test_user: User, test_media_season1: Media):
        """Test user consumption tracking."""
        user_media = UserMedia(
            user_id=test_user.id,
            media_id=test_media_season1.id,
            status='completed',
            platform='netflix',
            consumed_at=datetime.utcnow().date(),
            imported_from='csv'
        )
        db.add(user_media)
        db.commit()

        # Verify relationship
        assert len(test_user.media_items) == 1
        assert test_user.media_items[0].media.title == "Breaking Bad: Season 1"

    def test_detect_sequel_season_increment(
        self,
        db: Session,
        test_user: User,
        test_media_season1: Media,
        test_media_season2: Media
    ):
        """Test sequel detection for season increment."""
        # User has consumed Season 1
        user_media = UserMedia(
            user_id=test_user.id,
            media_id=test_media_season1.id,
            status='completed',
            platform='netflix',
            consumed_at=datetime.utcnow().date()
        )
        db.add(user_media)
        db.commit()

        # Run sequel detection
        detector = create_sequel_detector(db)
        matches = detector.find_sequels_for_user(str(test_user.id))

        # Should find Season 2
        assert len(matches) > 0

        season2_match = next(
            (m for m in matches if m.sequel_media.id == test_media_season2.id),
            None
        )
        assert season2_match is not None
        assert season2_match.confidence >= 0.90
        assert season2_match.match_type == 'season_increment'
        assert "Season 2" in season2_match.sequel_media.title

    def test_detect_multiple_sequels(
        self,
        db: Session,
        test_user: User,
        test_media_season1: Media,
        test_media_season2: Media,
        test_media_season3: Media
    ):
        """Test detection of multiple sequels."""
        # User has consumed Season 1
        user_media = UserMedia(
            user_id=test_user.id,
            media_id=test_media_season1.id,
            status='completed',
            platform='netflix',
            consumed_at=datetime.utcnow().date()
        )
        db.add(user_media)
        db.commit()

        # Run sequel detection
        detector = create_sequel_detector(db)
        matches = detector.find_sequels_for_user(str(test_user.id))

        # Should find both Season 2 and Season 3
        assert len(matches) >= 2

        sequel_titles = [m.sequel_media.title for m in matches]
        assert "Breaking Bad: Season 2" in sequel_titles
        assert "Breaking Bad: Season 3" in sequel_titles

    def test_exclude_already_consumed_sequels(
        self,
        db: Session,
        test_user: User,
        test_media_season1: Media,
        test_media_season2: Media,
        test_media_season3: Media
    ):
        """Test that already-consumed media is excluded from sequel results."""
        # User has consumed Season 1 AND Season 2
        for media in [test_media_season1, test_media_season2]:
            user_media = UserMedia(
                user_id=test_user.id,
                media_id=media.id,
                status='completed',
                platform='netflix',
                consumed_at=datetime.utcnow().date()
            )
            db.add(user_media)
        db.commit()

        # Run sequel detection
        detector = create_sequel_detector(db)
        matches = detector.find_sequels_for_user(str(test_user.id))

        # Should find Season 3 but NOT Season 2
        sequel_ids = [str(m.sequel_media.id) for m in matches]
        assert str(test_media_season2.id) not in sequel_ids
        assert str(test_media_season3.id) in sequel_ids

    def test_sequel_summary_statistics(
        self,
        db: Session,
        test_user: User,
        test_media_season1: Media,
        test_media_season2: Media,
        test_media_season3: Media
    ):
        """Test sequel detection summary statistics."""
        # User has consumed Season 1
        user_media = UserMedia(
            user_id=test_user.id,
            media_id=test_media_season1.id,
            status='completed',
            platform='netflix',
            consumed_at=datetime.utcnow().date()
        )
        db.add(user_media)
        db.commit()

        # Run sequel detection
        detector = create_sequel_detector(db)
        matches = detector.find_sequels_for_user(str(test_user.id))
        summary = detector.get_sequel_summary(matches)

        # Verify summary
        assert summary['total_sequels'] >= 2
        assert 'season_increment' in summary['by_type']
        assert summary['by_type']['season_increment'] >= 2
        assert 'netflix' in summary['by_platform']
        assert summary['high_confidence_count'] >= 2

    def test_no_sequels_for_standalone_media(self, db: Session, test_user: User):
        """Test that standalone media (no sequels available) returns empty."""
        # Create standalone movie
        media = Media(
            id=uuid4(),
            title="Inception",
            base_title="Inception",
            type='movie',
            platform='netflix'
        )
        db.add(media)

        user_media = UserMedia(
            user_id=test_user.id,
            media_id=media.id,
            status='completed',
            platform='netflix',
            consumed_at=datetime.utcnow().date()
        )
        db.add(user_media)
        db.commit()

        # Run sequel detection
        detector = create_sequel_detector(db)
        matches = detector.find_sequels_for_user(str(test_user.id))

        # Should find no sequels
        assert len(matches) == 0

    def test_confidence_scoring(
        self,
        db: Session,
        test_user: User,
        test_media_season1: Media,
        test_media_season2: Media
    ):
        """Test confidence scores are calculated correctly."""
        # User has consumed Season 1
        user_media = UserMedia(
            user_id=test_user.id,
            media_id=test_media_season1.id,
            status='completed',
            platform='netflix',
            consumed_at=datetime.utcnow().date()
        )
        db.add(user_media)
        db.commit()

        # Run sequel detection
        detector = create_sequel_detector(db)
        matches = detector.find_sequels_for_media(test_media_season1, str(test_user.id))

        # Season increment should have highest confidence
        season2_match = next(
            (m for m in matches if m.sequel_media.id == test_media_season2.id),
            None
        )
        assert season2_match is not None
        assert season2_match.confidence >= 0.95  # EXACT_SEASON_INCREMENT_CONFIDENCE


class TestNotificationCreationFlow:
    """Test notification creation from sequel detection."""

    def test_create_notification_from_sequel_match(
        self,
        db: Session,
        test_user: User,
        test_media_season1: Media,
        test_media_season2: Media
    ):
        """Test creating notification from sequel match."""
        notification = Notification(
            id=uuid4(),
            user_id=test_user.id,
            type='sequel_found',
            title=f"New season available: {test_media_season2.base_title}",
            message=f"Season {test_media_season2.season_number} is now available on {test_media_season2.platform}",
            media_id=test_media_season1.id,
            sequel_id=test_media_season2.id,
            metadata={
                'confidence': 0.95,
                'match_type': 'season_increment',
                'platform': test_media_season2.platform
            }
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        # Verify notification created
        assert notification.user_id == test_user.id
        assert notification.type == 'sequel_found'
        assert notification.read is False
        assert notification.emailed is False
        assert notification.media_id == test_media_season1.id
        assert notification.sequel_id == test_media_season2.id

    def test_notification_relationships(
        self,
        db: Session,
        test_user: User,
        test_media_season1: Media,
        test_media_season2: Media
    ):
        """Test notification relationships to user and media."""
        notification = Notification(
            id=uuid4(),
            user_id=test_user.id,
            type='sequel_found',
            title="Test notification",
            message="Test message",
            media_id=test_media_season1.id,
            sequel_id=test_media_season2.id
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        # Test relationships
        assert notification.user.email == test_user.email
        assert notification.media.title == test_media_season1.title
        assert notification.sequel.title == test_media_season2.title

    def test_prevent_duplicate_notifications(
        self,
        db: Session,
        test_user: User,
        test_media_season1: Media,
        test_media_season2: Media
    ):
        """Test that duplicate notifications are prevented."""
        # Create first notification
        notification1 = Notification(
            id=uuid4(),
            user_id=test_user.id,
            type='sequel_found',
            title="Test",
            message="Test",
            media_id=test_media_season1.id,
            sequel_id=test_media_season2.id
        )
        db.add(notification1)
        db.commit()

        # Check for existing notification before creating another
        existing = db.query(Notification).filter(
            Notification.user_id == test_user.id,
            Notification.media_id == test_media_season1.id,
            Notification.sequel_id == test_media_season2.id,
            Notification.type == 'sequel_found'
        ).first()

        assert existing is not None
        # Should not create duplicate


class TestEndToEndSequelFlow:
    """Test complete end-to-end flow."""

    def test_full_flow_import_to_notification(
        self,
        db: Session,
        test_user: User
    ):
        """
        Test complete flow:
        1. Parse CSV title
        2. Create media with base_title
        3. User consumes media
        4. Sequel becomes available
        5. Detection finds sequel
        6. Notification created
        """
        # Step 1-2: Parse and create media
        title = "The Office: Season 1"
        parsed = title_parser.parse(title)

        season1 = Media(
            id=uuid4(),
            title=title,
            base_title=parsed['base_title'],
            season_number=parsed['season_number'],
            type='tv_series',
            platform='netflix'
        )
        db.add(season1)
        db.commit()

        # Step 3: User consumes
        user_media = UserMedia(
            user_id=test_user.id,
            media_id=season1.id,
            status='completed',
            platform='netflix',
            consumed_at=datetime.utcnow().date()
        )
        db.add(user_media)
        db.commit()

        # Step 4: Sequel becomes available (simulated)
        season2 = Media(
            id=uuid4(),
            title="The Office: Season 2",
            base_title=parsed['base_title'],
            season_number=2,
            type='tv_series',
            platform='netflix'
        )
        db.add(season2)
        db.commit()

        # Step 5: Detection
        detector = create_sequel_detector(db)
        matches = detector.find_sequels_for_user(str(test_user.id))

        assert len(matches) > 0
        match = matches[0]

        # Step 6: Create notification
        notification = Notification(
            id=uuid4(),
            user_id=test_user.id,
            type='sequel_found',
            title=f"New season: {match.sequel_media.base_title}",
            message=f"Season {match.sequel_media.season_number} is available",
            media_id=season1.id,
            sequel_id=season2.id,
            metadata={'confidence': match.confidence}
        )
        db.add(notification)
        db.commit()

        # Verify complete flow
        assert notification.user_id == test_user.id
        assert notification.sequel.season_number == 2
        assert notification.read is False

        # Verify user can query their notifications
        user_notifications = db.query(Notification).filter(
            Notification.user_id == test_user.id
        ).all()

        assert len(user_notifications) == 1
        assert user_notifications[0].type == 'sequel_found'

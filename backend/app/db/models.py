"""
Database models matching the security-enhanced schema
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Boolean, Integer, Date, Text,
    ForeignKey, Index, TIMESTAMP, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class User(Base):
    """User model with enhanced security features"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Security tracking
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(TIMESTAMP, nullable=True)
    totp_secret = Column(String(32), nullable=True)  # For 2FA

    # Session management
    refresh_token_hash = Column(String(255), nullable=True)
    last_login_at = Column(TIMESTAMP, nullable=True)
    last_login_ip = Column(INET, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    media_items = relationship("UserMedia", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    monitoring_items = relationship("MonitoringQueue", back_populates="user", cascade="all, delete-orphan")
    security_events = relationship("SecurityEvent", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship("NotificationPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class UserSession(Base):
    """User session tracking for refresh token management"""
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    refresh_token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(TIMESTAMP, nullable=False)

    # Session metadata
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index('idx_sessions_user', 'user_id'),
        Index('idx_sessions_token', 'refresh_token_hash'),
    )

    def __repr__(self):
        return f"<UserSession {self.id} for user {self.user_id}>"


class Media(Base):
    """Core media catalog"""
    __tablename__ = "media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    type = Column(String(50), nullable=True)  # movie, tv_series, book, audiobook
    release_date = Column(Date, nullable=True)

    # Sequel tracking fields
    base_title = Column(String(255), nullable=True, index=True)
    season_number = Column(Integer, nullable=True)
    episode_number = Column(Integer, nullable=True)
    tmdb_id = Column(Integer, nullable=True, index=True)
    imdb_id = Column(String(20), nullable=True)
    platform = Column(String(50), nullable=True)  # Primary platform for this media

    # Platform and metadata stored as JSON
    platform_ids = Column(JSONB, default={}, nullable=False)
    media_metadata = Column(JSONB, default={}, nullable=False)

    # Series relationships
    parent_id = Column(UUID(as_uuid=True), ForeignKey("media.id"), nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    parent = relationship("Media", remote_side=[id], backref="children")
    user_consumption = relationship("UserMedia", back_populates="media", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_media_title', 'title'),
        Index('idx_media_platform_ids', 'platform_ids', postgresql_using='gin'),
        Index('idx_media_base_title', 'base_title'),
        Index('idx_media_tmdb_id', 'tmdb_id'),
        Index('idx_media_season_number', 'season_number'),
        Index('idx_media_base_title_season', 'base_title', 'season_number'),
    )

    def __repr__(self):
        return f"<Media {self.title} ({self.type})>"


class UserMedia(Base):
    """User's media consumption tracking"""
    __tablename__ = "user_media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    media_id = Column(UUID(as_uuid=True), ForeignKey("media.id", ondelete="CASCADE"), nullable=False)

    status = Column(String(50), nullable=True)  # watched, reading, completed, in_progress
    platform = Column(String(50), nullable=True)  # where consumed
    consumed_at = Column(Date, nullable=True)

    # Import tracking
    imported_from = Column(String(50), nullable=True)  # csv, manual
    raw_import_data = Column(JSONB, nullable=True)  # original CSV row

    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="media_items")
    media = relationship("Media", back_populates="user_consumption")

    __table_args__ = (
        Index('idx_user_media_user', 'user_id'),
        Index('idx_user_media_media', 'media_id'),
        Index('idx_user_media_unique', 'user_id', 'media_id', unique=True),
    )

    def __repr__(self):
        return f"<UserMedia user={self.user_id} media={self.media_id}>"


class MonitoringQueue(Base):
    """Queue for monitoring and notifications"""
    __tablename__ = "monitoring_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    media_id = Column(UUID(as_uuid=True), ForeignKey("media.id"), nullable=True)
    next_media_id = Column(UUID(as_uuid=True), ForeignKey("media.id"), nullable=True)

    notified = Column(Boolean, default=False, nullable=False)
    notification_token = Column(String(255), nullable=True)  # Unsubscribe token

    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="monitoring_items")
    media = relationship("Media", foreign_keys=[media_id])
    next_media = relationship("Media", foreign_keys=[next_media_id])

    __table_args__ = (
        Index('idx_monitoring_queue_user_notified', 'user_id', 'notified'),
    )

    def __repr__(self):
        return f"<MonitoringQueue {self.id} notified={self.notified}>"


class APIKey(Base):
    """Encrypted API key storage"""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service = Column(String(50), nullable=False)  # rapidapi, sendgrid
    key_hash = Column(String(255), nullable=False)
    encrypted_key = Column(Text, nullable=False)  # Encrypted with master key

    last_rotated = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    expires_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<APIKey {self.service}>"


class ImportJob(Base):
    """Import job tracking"""
    __tablename__ = "import_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    source = Column(String(50), nullable=False)  # netflix_csv, manual, api
    status = Column(String(50), nullable=False, default="pending")  # pending, processing, completed, failed, partial

    # Progress tracking
    total_rows = Column(Integer, default=0, nullable=False)
    processed_rows = Column(Integer, default=0, nullable=False)
    successful_rows = Column(Integer, default=0, nullable=False)
    failed_rows = Column(Integer, default=0, nullable=False)

    # Error tracking
    error_log = Column(JSONB, default=[], nullable=False)

    # File metadata
    filename = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String(64), nullable=True)  # SHA256 hash

    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)

    __table_args__ = (
        Index('idx_import_jobs_user_status', 'user_id', 'status'),
        Index('idx_import_jobs_created', 'created_at'),
    )

    def __repr__(self):
        return f"<ImportJob {self.id} {self.status}>"


class SecurityEvent(Base):
    """Security audit log"""
    __tablename__ = "security_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_type = Column(String(50), nullable=False)  # login_success, login_failed, csv_import, etc

    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    event_metadata = Column(JSONB, default={}, nullable=False)  # Additional context

    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="security_events")

    __table_args__ = (
        Index('idx_security_events_user', 'user_id', 'created_at'),
        Index('idx_security_events_type', 'event_type', 'created_at'),
    )

    def __repr__(self):
        return f"<SecurityEvent {self.event_type} at {self.created_at}>"


class Notification(Base):
    """User notifications for sequel detection and updates"""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Notification details
    type = Column(String(50), nullable=False)  # sequel_found, season_released, new_content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Related media
    media_id = Column(UUID(as_uuid=True), ForeignKey("media.id", ondelete="CASCADE"), nullable=True)
    sequel_id = Column(UUID(as_uuid=True), ForeignKey("media.id", ondelete="SET NULL"), nullable=True)

    # Status tracking
    is_read = Column(Boolean, default=False, nullable=False)
    is_emailed = Column(Boolean, default=False, nullable=False)

    # Unsubscribe token for email notifications (with expiration)
    unsubscribe_token = Column(String(255), nullable=True, unique=True)
    unsubscribe_token_expires = Column(TIMESTAMP, nullable=True)

    # Additional data
    notification_metadata = Column(JSONB, default={}, nullable=False)

    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    read_at = Column(TIMESTAMP, nullable=True)
    emailed_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")
    media = relationship("Media", foreign_keys=[media_id])
    sequel = relationship("Media", foreign_keys=[sequel_id])

    __table_args__ = (
        Index('idx_notifications_user_read', 'user_id', 'is_read', 'created_at'),
        Index('idx_notifications_user_created', 'user_id', 'created_at'),
        Index('idx_notifications_type', 'type'),
    )

    def __repr__(self):
        return f"<Notification {self.type} for user {self.user_id}>"


class NotificationPreferences(Base):
    """User preferences for notifications"""
    __tablename__ = "notification_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    # Email preferences
    email_enabled = Column(Boolean, default=True, nullable=False)
    email_frequency = Column(String(20), default='daily', nullable=False)  # instant, daily, weekly, never

    # In-app preferences
    in_app_enabled = Column(Boolean, default=True, nullable=False)

    # Notification type preferences
    sequel_notifications = Column(Boolean, default=True, nullable=False)
    season_notifications = Column(Boolean, default=True, nullable=False)
    new_content_notifications = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="notification_preferences")

    __table_args__ = (
        CheckConstraint(
            "email_frequency IN ('instant', 'daily', 'weekly', 'never')",
            name='valid_email_frequency'
        ),
    )

    def __repr__(self):
        return f"<NotificationPreferences for user {self.user_id}>"

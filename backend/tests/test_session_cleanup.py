"""
Tests for Session Cleanup Tasks
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from app.db.models import User, UserSession
from app.tasks.session_tasks import cleanup_expired_sessions, get_session_stats
from app.core.security import security_service


@pytest.mark.asyncio
async def test_cleanup_expired_sessions_removes_expired(db_session):
    """Test that cleanup removes only expired sessions"""
    # Create test user
    user = User(
        email="cleanup_test@example.com",
        password_hash=security_service.hash_password("TestPass123!"),
        email_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create 2 expired sessions
    expired_session_1 = UserSession(
        user_id=user.id,
        refresh_token_hash=security_service.hash_token("expired_token_1"),
        expires_at=datetime.utcnow() - timedelta(days=1),  # Expired yesterday
    )
    expired_session_2 = UserSession(
        user_id=user.id,
        refresh_token_hash=security_service.hash_token("expired_token_2"),
        expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
    )
    
    # Create 2 active (non-expired) sessions
    active_session_1 = UserSession(
        user_id=user.id,
        refresh_token_hash=security_service.hash_token("active_token_1"),
        expires_at=datetime.utcnow() + timedelta(days=7),  # Expires in 7 days
    )
    active_session_2 = UserSession(
        user_id=user.id,
        refresh_token_hash=security_service.hash_token("active_token_2"),
        expires_at=datetime.utcnow() + timedelta(days=1),  # Expires in 1 day
    )
    
    db_session.add_all([expired_session_1, expired_session_2, active_session_1, active_session_2])
    await db_session.commit()
    
    # Verify initial state: 4 sessions total
    result = await db_session.execute(select(UserSession).where(UserSession.user_id == user.id))
    initial_sessions = result.scalars().all()
    assert len(initial_sessions) == 4
    
    # Run cleanup task (synchronous Celery task)
    cleanup_result = cleanup_expired_sessions()
    
    # Verify cleanup result
    assert cleanup_result['status'] == 'success'
    assert cleanup_result['deleted_count'] == 2
    
    # Verify database state: only 2 active sessions remain
    await db_session.expire_all()  # Clear SQLAlchemy cache
    result = await db_session.execute(select(UserSession).where(UserSession.user_id == user.id))
    remaining_sessions = result.scalars().all()
    assert len(remaining_sessions) == 2
    
    # Verify that remaining sessions are the active ones
    remaining_hashes = [s.refresh_token_hash for s in remaining_sessions]
    assert active_session_1.refresh_token_hash in remaining_hashes
    assert active_session_2.refresh_token_hash in remaining_hashes


@pytest.mark.asyncio
async def test_cleanup_expired_sessions_no_expired(db_session):
    """Test cleanup when no sessions are expired"""
    # Create test user
    user = User(
        email="no_expired@example.com",
        password_hash=security_service.hash_password("TestPass123!"),
        email_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create only active sessions
    active_session = UserSession(
        user_id=user.id,
        refresh_token_hash=security_service.hash_token("active_token"),
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db_session.add(active_session)
    await db_session.commit()
    
    # Run cleanup
    cleanup_result = cleanup_expired_sessions()
    
    # Verify no sessions were deleted
    assert cleanup_result['status'] == 'success'
    assert cleanup_result['deleted_count'] == 0
    assert 'No expired sessions' in cleanup_result['message']
    
    # Verify session still exists
    result = await db_session.execute(select(UserSession).where(UserSession.user_id == user.id))
    sessions = result.scalars().all()
    assert len(sessions) == 1


@pytest.mark.asyncio
async def test_cleanup_expired_sessions_all_expired(db_session):
    """Test cleanup when all sessions are expired"""
    # Create test user
    user = User(
        email="all_expired@example.com",
        password_hash=security_service.hash_password("TestPass123!"),
        email_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create only expired sessions
    for i in range(3):
        expired_session = UserSession(
            user_id=user.id,
            refresh_token_hash=security_service.hash_token(f"expired_token_{i}"),
            expires_at=datetime.utcnow() - timedelta(days=i+1),
        )
        db_session.add(expired_session)
    await db_session.commit()
    
    # Verify initial state
    result = await db_session.execute(select(UserSession).where(UserSession.user_id == user.id))
    initial_sessions = result.scalars().all()
    assert len(initial_sessions) == 3
    
    # Run cleanup
    cleanup_result = cleanup_expired_sessions()
    
    # Verify all sessions deleted
    assert cleanup_result['status'] == 'success'
    assert cleanup_result['deleted_count'] == 3
    
    # Verify no sessions remain
    await db_session.expire_all()
    result = await db_session.execute(select(UserSession).where(UserSession.user_id == user.id))
    remaining_sessions = result.scalars().all()
    assert len(remaining_sessions) == 0


@pytest.mark.asyncio
async def test_cleanup_preserves_other_users_sessions(db_session):
    """Test that cleanup doesn't affect other users' sessions"""
    # Create two users
    user1 = User(
        email="user1@example.com",
        password_hash=security_service.hash_password("TestPass123!"),
        email_verified=True
    )
    user2 = User(
        email="user2@example.com",
        password_hash=security_service.hash_password("TestPass123!"),
        email_verified=True
    )
    db_session.add_all([user1, user2])
    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)
    
    # User 1: expired session
    expired_session = UserSession(
        user_id=user1.id,
        refresh_token_hash=security_service.hash_token("expired_token"),
        expires_at=datetime.utcnow() - timedelta(days=1),
    )
    
    # User 2: active session
    active_session = UserSession(
        user_id=user2.id,
        refresh_token_hash=security_service.hash_token("active_token"),
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    
    db_session.add_all([expired_session, active_session])
    await db_session.commit()
    
    # Run cleanup
    cleanup_result = cleanup_expired_sessions()
    
    # Verify only user1's expired session was deleted
    assert cleanup_result['deleted_count'] == 1
    
    # Verify user1 has no sessions
    result1 = await db_session.execute(select(UserSession).where(UserSession.user_id == user1.id))
    assert len(result1.scalars().all()) == 0
    
    # Verify user2 still has active session
    await db_session.expire_all()
    result2 = await db_session.execute(select(UserSession).where(UserSession.user_id == user2.id))
    user2_sessions = result2.scalars().all()
    assert len(user2_sessions) == 1
    assert user2_sessions[0].refresh_token_hash == active_session.refresh_token_hash


@pytest.mark.asyncio
async def test_get_session_stats(db_session):
    """Test session statistics task"""
    # Create test user
    user = User(
        email="stats_test@example.com",
        password_hash=security_service.hash_password("TestPass123!"),
        email_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create 2 expired and 3 active sessions
    for i in range(2):
        expired = UserSession(
            user_id=user.id,
            refresh_token_hash=security_service.hash_token(f"expired_{i}"),
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        db_session.add(expired)
    
    for i in range(3):
        active = UserSession(
            user_id=user.id,
            refresh_token_hash=security_service.hash_token(f"active_{i}"),
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db_session.add(active)
    
    await db_session.commit()
    
    # Get stats
    stats = get_session_stats()
    
    # Verify stats
    assert stats['total_sessions'] == 5
    assert stats['active_sessions'] == 3
    assert stats['expired_sessions'] == 2
    assert 'timestamp' in stats


@pytest.mark.asyncio
async def test_max_sessions_per_user_reduced_to_three(db_session):
    """Test that new config limit of 3 sessions per user is enforced"""
    from app.core.config import settings
    
    # Verify config value
    assert settings.MAX_SESSIONS_PER_USER == 3
    
    # This test ensures the config change is properly applied
    # The actual enforcement is tested in auth_service tests

"""
Authentication service business logic
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.db.models import User, UserSession, SecurityEvent
from app.core.security import security_service
from app.core.config import settings


class AuthService:
    """Authentication business logic"""

    @staticmethod
    async def create_user(db: AsyncSession, email: str, password: str) -> User:
        """
        Create new user with hashed password

        Args:
            db: Database session
            email: User email
            password: Plain text password

        Returns:
            Created user

        Raises:
            HTTPException: If email already exists
        """
        # Check if user exists
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create user
        hashed_password = security_service.hash_password(password)
        user = User(
            email=email,
            password_hash=hashed_password,
            email_verified=not settings.ENABLE_EMAIL_VERIFICATION
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str,
        ip_address: Optional[str] = None
    ) -> Optional[User]:
        """
        Authenticate user and handle failed login attempts

        Args:
            db: Database session
            email: User email
            password: Plain text password
            ip_address: Client IP address

        Returns:
            User if authentication successful, None otherwise
        """
        # Get user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            return None

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked until {user.locked_until}"
            )

        # Verify password
        if not security_service.verify_password(password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1

            # Lock account if max attempts reached
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=settings.LOCKOUT_DURATION_MINUTES
                )

            await db.commit()
            return None

        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = ip_address

        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    async def create_tokens(
        db: AsyncSession,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Create access and refresh tokens

        Args:
            db: Database session
            user: User object
            ip_address: Client IP
            user_agent: Client user agent

        Returns:
            Tuple of (access_token, refresh_token)
        """
        # Create tokens
        access_token = security_service.create_access_token(str(user.id))
        refresh_token = security_service.create_refresh_token(str(user.id))

        # Store refresh token hash in session
        token_hash = security_service.hash_token(refresh_token)
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        # Check session limit
        sessions_result = await db.execute(
            select(UserSession)
            .where(UserSession.user_id == user.id)
            .order_by(UserSession.created_at.desc())
        )
        sessions = sessions_result.scalars().all()

        if len(sessions) >= settings.MAX_SESSIONS_PER_USER:
            # Remove oldest session
            await db.delete(sessions[-1])

        # Create new session
        session = UserSession(
            user_id=user.id,
            refresh_token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )

        db.add(session)
        await db.commit()

        return access_token, refresh_token

    @staticmethod
    async def refresh_access_token(
        db: AsyncSession,
        refresh_token: str
    ) -> str:
        """
        Refresh access token using refresh token

        Args:
            db: Database session
            refresh_token: Refresh token

        Returns:
            New access token

        Raises:
            HTTPException: If refresh token is invalid
        """
        # Verify refresh token
        payload = security_service.verify_token(refresh_token, token_type="refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        user_id = payload.get("sub")

        # Find session with matching token hash
        token_hash = security_service.hash_token(refresh_token)
        result = await db.execute(
            select(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.expires_at > datetime.utcnow()
            )
        )
        sessions = result.scalars().all()

        # Verify token hash matches one of the sessions
        session_found = False
        for session in sessions:
            if security_service.verify_token_hash(refresh_token, session.refresh_token_hash):
                session_found = True
                break

        if not session_found:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or expired"
            )

        # Create new access token
        access_token = security_service.create_access_token(user_id)

        return access_token

    @staticmethod
    async def revoke_session(
        db: AsyncSession,
        user_id: str,
        session_id: str
    ) -> bool:
        """
        Revoke specific user session

        Args:
            db: Database session
            user_id: User ID
            session_id: Session ID to revoke

        Returns:
            True if session was revoked
        """
        result = await db.execute(
            select(UserSession)
            .where(
                UserSession.id == session_id,
                UserSession.user_id == user_id
            )
        )
        session = result.scalar_one_or_none()

        if session:
            await db.delete(session)
            await db.commit()
            return True

        return False

    @staticmethod
    async def log_security_event(
        db: AsyncSession,
        event_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """
        Log security event for audit trail

        Args:
            db: Database session
            event_type: Type of security event
            user_id: User ID if applicable
            ip_address: Client IP
            user_agent: Client user agent
            metadata: Additional event metadata
        """
        event = SecurityEvent(
            user_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )

        db.add(event)
        await db.commit()

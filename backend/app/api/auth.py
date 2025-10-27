"""
Authentication API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import get_db
from app.db.models import User, UserSession
from app.schemas.auth import (
    UserCreate, UserLogin, TokenResponse, TokenRefresh,
    UserResponse, SessionResponse, PasswordResetRequest, PasswordResetConfirm
)
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user
from app.core.middleware import limiter
from app.core.config import settings


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register new user and return authentication tokens
    
    After successful registration, the user is automatically logged in.

    Rate limit: 5 requests per hour per IP
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Create user
    user = await AuthService.create_user(db, user_data.email, user_data.password)

    # Create tokens (auto-login)
    access_token, refresh_token = await AuthService.create_tokens(
        db, user, ip_address, user_agent
    )

    # Log security event
    await AuthService.log_security_event(
        db,
        event_type="user_registered",
        user_id=str(user.id),
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={"auto_login": True}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.LOGIN_RATE_LIMIT)
async def login(
    request: Request,
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens

    Rate limit: 10 requests per minute per IP
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Authenticate user
    user = await AuthService.authenticate_user(
        db,
        credentials.email,
        credentials.password,
        ip_address
    )

    if not user:
        # Log failed login
        await AuthService.log_security_event(
            db,
            event_type="login_failed",
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"email": credentials.email}
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Create tokens
    access_token, refresh_token = await AuthService.create_tokens(
        db, user, ip_address, user_agent
    )

    # Log successful login
    await AuthService.log_security_event(
        db,
        event_type="login_success",
        user_id=str(user.id),
        ip_address=ip_address,
        user_agent=user_agent
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=dict)
@limiter.limit("20/hour")
async def refresh_token(
    request: Request,
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token

    Rate limit: 20 requests per hour
    """
    access_token = await AuthService.refresh_access_token(db, token_data.refresh_token)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user by invalidating all sessions
    """
    # Delete all user sessions
    result = await db.execute(
        select(UserSession).where(UserSession.user_id == current_user.id)
    )
    sessions = result.scalars().all()

    for session in sessions:
        await db.delete(session)

    await db.commit()

    # Log logout
    await AuthService.log_security_event(
        db,
        event_type="logout",
        user_id=str(current_user.id)
    )

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at
    )


@router.get("/sessions", response_model=list[SessionResponse])
async def get_active_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all active sessions for current user
    """
    result = await db.execute(
        select(UserSession)
        .where(UserSession.user_id == current_user.id)
        .order_by(UserSession.created_at.desc())
    )
    sessions = result.scalars().all()

    return [
        SessionResponse(
            id=str(session.id),
            ip_address=str(session.ip_address) if session.ip_address else None,
            user_agent=session.user_agent,
            created_at=session.created_at,
            expires_at=session.expires_at
        )
        for session in sessions
    ]


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke specific session
    """
    success = await AuthService.revoke_session(db, str(current_user.id), session_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return {"message": "Session revoked successfully"}


@router.post("/verify-email", response_model=dict)
async def verify_email(
    verification_data: EmailVerification,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify user's email address with verification token
    """
    success = await AuthService.verify_email(db, verification_data.token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    return {"message": "Email verified successfully"}


@router.post("/resend-verification", response_model=dict)
@limiter.limit("3/hour")
async def resend_verification(
    request: Request,
    reset_data: PasswordResetRequest,  # Using same schema for email
    db: AsyncSession = Depends(get_db)
):
    """
    Resend email verification link
    """
    success = await AuthService.resend_verification_email(db, reset_data.email)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found or email already verified"
        )
    
    return {"message": "Verification email sent"}


@router.post("/reset-password", response_model=dict)
@limiter.limit("5/hour")
async def reset_password(
    request: Request,
    reset_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset via email
    """
    success = await AuthService.send_password_reset_email(db, reset_data.email)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    return {"message": "Password reset email sent"}


@router.post("/confirm-reset-password", response_model=dict)
async def confirm_reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm password reset with token and new password
    """
    success = await AuthService.confirm_password_reset(
        db, reset_data.token, reset_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return {"message": "Password reset successfully"}

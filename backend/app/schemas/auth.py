"""
Authentication and user schemas with validation
"""
from pydantic import BaseModel, EmailStr, validator, constr
from typing import Optional
from datetime import datetime
import re


class UserCreate(BaseModel):
    """User registration schema with password validation"""
    email: EmailStr
    password: constr(min_length=12, max_length=128)

    @validator('password')
    def validate_password_strength(cls, v):
        """Enforce password complexity requirements"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenRefresh(BaseModel):
    """Refresh token request"""
    refresh_token: str


class UserResponse(BaseModel):
    """User information response"""
    id: str
    email: str
    email_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class PasswordReset(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: constr(min_length=12, max_length=128)

    @validator('new_password')
    def validate_password_strength(cls, v):
        """Enforce password complexity requirements"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class EmailVerification(BaseModel):
    """Email verification schema"""
    token: str


class SessionResponse(BaseModel):
    """Active session information"""
    id: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True

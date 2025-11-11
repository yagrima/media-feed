"""
Audible Schemas - Pydantic models for Audible integration API
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import uuid


class AudibleConnectRequest(BaseModel):
    """Request to connect Audible account"""
    email: str = Field(..., min_length=3, max_length=255, description="Audible/Amazon email")
    password: str = Field(..., min_length=6, description="Audible/Amazon password (2FA code can be appended)")
    marketplace: str = Field(default="us", pattern=r"^[a-z]{2}$", description="Marketplace code (us, uk, de, etc.)")

    @validator('email')
    def validate_email(cls, v):
        """Basic email validation"""
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower().strip()

    @validator('marketplace')
    def validate_marketplace(cls, v):
        """Validate marketplace code"""
        valid_marketplaces = ['us', 'uk', 'de', 'fr', 'ca', 'au', 'in', 'it', 'jp', 'es']
        if v.lower() not in valid_marketplaces:
            raise ValueError(f'Invalid marketplace. Must be one of: {", ".join(valid_marketplaces)}')
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "marketplace": "us"
            }
        }


class AudibleConnectResponse(BaseModel):
    """Response after connecting Audible account"""
    success: bool
    message: str
    device_name: Optional[str] = None
    marketplace: str
    books_imported: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Audible account connected successfully",
                "device_name": "Me Feed - Web",
                "marketplace": "us",
                "books_imported": 245
            }
        }


class AudibleSyncRequest(BaseModel):
    """Request to sync Audible library (no body needed, uses stored token)"""
    pass


class AudibleSyncResponse(BaseModel):
    """Response after syncing Audible library"""
    success: bool
    message: str
    imported: int = Field(description="Number of new books imported")
    updated: int = Field(description="Number of existing books updated")
    skipped: int = Field(description="Number of books skipped")
    errors: int = Field(description="Number of errors encountered")
    total: int = Field(description="Total books in library")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Library synced successfully",
                "imported": 12,
                "updated": 3,
                "skipped": 230,
                "errors": 0,
                "total": 245
            }
        }


class AudibleDisconnectResponse(BaseModel):
    """Response after disconnecting Audible"""
    success: bool
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Audible account disconnected successfully"
            }
        }


class AudibleStatusResponse(BaseModel):
    """Audible connection status"""
    connected: bool
    marketplace: Optional[str] = None
    device_name: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    books_count: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "connected": True,
                "marketplace": "us",
                "device_name": "Me Feed - Web",
                "last_sync_at": "2025-11-11T10:30:00Z",
                "books_count": 245
            }
        }


class AudibleErrorResponse(BaseModel):
    """Error response for Audible operations"""
    error: str
    detail: Optional[str] = None
    error_type: Optional[str] = None  # captcha_required, 2fa_required, auth_failed, etc.

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Authentication failed",
                "detail": "Invalid email or password",
                "error_type": "auth_failed"
            }
        }

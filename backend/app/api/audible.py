"""
Audible API Endpoints - Connect and manage Audible accounts
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Dict, Any
import logging

from app.core.dependencies import get_current_user, get_db
from app.db.models import User, AudibleAuth, UserMedia, Media
from app.services.audible_service import (
    AudibleService,
    AudibleAuthError,
    AudibleCaptchaRequiredError,
    AudibleTwoFactorRequiredError
)
from app.services.audible_parser import AudibleParser
from app.schemas.audible_schemas import (
    AudibleConnectRequest,
    AudibleConnectResponse,
    AudibleSyncResponse,
    AudibleDisconnectResponse,
    AudibleStatusResponse,
    AudibleErrorResponse
)
from app.core.rate_limiter import limiter
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audible", tags=["audible"])


@router.post(
    "/connect",
    response_model=AudibleConnectResponse,
    responses={
        400: {"model": AudibleErrorResponse},
        401: {"model": AudibleErrorResponse},
        429: {"description": "Too many requests"}
    }
)
@limiter.limit("3/hour")  # Strict rate limit for auth attempts
async def connect_audible(
    request: AudibleConnectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Connect Audible account and import library
    
    This endpoint:
    1. Authenticates with Audible using provided credentials
    2. Registers a virtual device (visible in Amazon device list)
    3. Encrypts and stores auth token with user-specific encryption
    4. Fetches and imports entire Audible library
    5. Never stores the password (only encrypted token)
    
    **Rate Limit:** 3 attempts per hour per user
    
    **2FA Users:** Append your 2FA code to your password (e.g., "mypassword123456")
    """
    audible_service = AudibleService(db)
    audible_parser = AudibleParser(db)
    
    try:
        logger.info(f"Audible connection attempt for user {current_user.id}")
        
        # Check if user already has Audible connected
        existing_auth = await db.execute(
            select(AudibleAuth).where(AudibleAuth.user_id == current_user.id)
        )
        existing = existing_auth.scalar_one_or_none()
        
        if existing:
            # Disconnect existing connection first
            await audible_service.deregister_device(existing.encrypted_token, current_user.id)
            await db.delete(existing)
            await db.commit()
            logger.info(f"Removed existing Audible connection for user {current_user.id}")
        
        # Authenticate with Audible (password only in memory during this call)
        auth_result = await audible_service.authenticate(
            user_id=current_user.id,
            email=request.email,
            password=request.password,  # Password discarded after authentication
            marketplace=request.marketplace
        )
        
        # Password is now out of scope and will be garbage collected
        # Only encrypted token remains
        
        # Store authentication in database
        audible_auth = AudibleAuth(
            user_id=current_user.id,
            encrypted_token=auth_result['encrypted_token'],
            marketplace=auth_result['marketplace'],
            device_name=auth_result['device_name']
        )
        db.add(audible_auth)
        await db.commit()
        await db.refresh(audible_auth)
        
        logger.info(f"Audible auth stored for user {current_user.id}")
        
        # Fetch and import library
        try:
            library_data = await audible_service.fetch_library(
                encrypted_token=audible_auth.encrypted_token,
                user_id=current_user.id
            )
            
            # Parse and import library
            import_stats = await audible_parser.process_library(
                user_id=current_user.id,
                library_data=library_data
            )
            
            # Update last sync time
            audible_auth.last_sync_at = datetime.utcnow()
            await db.commit()
            
            logger.info(f"Audible library imported for user {current_user.id}: {import_stats}")
            
            return AudibleConnectResponse(
                success=True,
                message=f"Successfully imported {import_stats['imported']} audiobooks from Audible",
                device_name=audible_auth.device_name,
                marketplace=audible_auth.marketplace,
                books_imported=import_stats['imported']
            )
            
        except Exception as e:
            # If library import fails, still keep the connection
            # User can try syncing again later
            logger.error(f"Failed to import library but auth stored: {e}", exc_info=True)
            
            return AudibleConnectResponse(
                success=True,
                message=f"Connected but library import failed: {str(e)}. Try syncing again.",
                device_name=audible_auth.device_name,
                marketplace=audible_auth.marketplace,
                books_imported=0
            )
    
    except AudibleCaptchaRequiredError as e:
        logger.warning(f"CAPTCHA required for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": str(e),
                "error_type": "captcha_required",
                "detail": "Audible detected unusual activity. Please try again later or use manual import."
            }
        )
    
    except AudibleTwoFactorRequiredError as e:
        logger.warning(f"2FA required for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": str(e),
                "error_type": "2fa_required",
                "detail": "Please append your 2FA code to your password and try again."
            }
        )
    
    except AudibleAuthError as e:
        logger.warning(f"Auth failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": str(e),
                "error_type": "auth_failed",
                "detail": "Authentication failed. Please check your credentials."
            }
        )
    
    except Exception as e:
        logger.error(f"Unexpected error connecting Audible for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": str(e)
            }
        )


@router.post(
    "/sync",
    response_model=AudibleSyncResponse,
    responses={
        404: {"model": AudibleErrorResponse},
        401: {"model": AudibleErrorResponse}
    }
)
@limiter.limit("10/day")  # 10 syncs per day max
async def sync_audible_library(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync Audible library
    
    Fetches latest library data from Audible and updates database with:
    - New audiobook purchases
    - Updated listening progress
    - Changed metadata
    
    **Rate Limit:** 10 syncs per day per user
    """
    audible_service = AudibleService(db)
    audible_parser = AudibleParser(db)
    
    try:
        # Check if user has Audible connected
        auth_result = await db.execute(
            select(AudibleAuth).where(AudibleAuth.user_id == current_user.id)
        )
        audible_auth = auth_result.scalar_one_or_none()
        
        if not audible_auth:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Audible not connected",
                    "detail": "Please connect your Audible account first"
                }
            )
        
        logger.info(f"Syncing Audible library for user {current_user.id}")
        
        # Fetch library
        library_data = await audible_service.fetch_library(
            encrypted_token=audible_auth.encrypted_token,
            user_id=current_user.id
        )
        
        # Parse and import/update
        import_stats = await audible_parser.process_library(
            user_id=current_user.id,
            library_data=library_data
        )
        
        # Update last sync time
        audible_auth.last_sync_at = datetime.utcnow()
        await db.commit()
        
        total_books = len(library_data.get('items', []))
        
        logger.info(f"Sync complete for user {current_user.id}: {import_stats}")
        
        return AudibleSyncResponse(
            success=True,
            message="Library synced successfully",
            imported=import_stats['imported'],
            updated=import_stats['updated'],
            skipped=import_stats['skipped'],
            errors=import_stats['errors'],
            total=total_books
        )
    
    except AudibleAuthError as e:
        logger.warning(f"Auth error during sync for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": str(e),
                "error_type": "token_expired",
                "detail": "Authentication token expired. Please reconnect your Audible account."
            }
        )
    
    except Exception as e:
        logger.error(f"Error syncing Audible for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Sync failed",
                "detail": str(e)
            }
        )


@router.delete(
    "/disconnect",
    response_model=AudibleDisconnectResponse
)
async def disconnect_audible(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Disconnect Audible account
    
    This will:
    1. Deregister the virtual device from Amazon account
    2. Delete encrypted token from database
    3. Keep imported audiobook data (not deleted)
    
    Note: Audiobooks already imported will remain in your library.
    """
    audible_service = AudibleService(db)
    
    try:
        # Get auth
        auth_result = await db.execute(
            select(AudibleAuth).where(AudibleAuth.user_id == current_user.id)
        )
        audible_auth = auth_result.scalar_one_or_none()
        
        if not audible_auth:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Audible not connected",
                    "detail": "No Audible connection found for this account"
                }
            )
        
        logger.info(f"Disconnecting Audible for user {current_user.id}")
        
        # Deregister device from Amazon
        deregistered = await audible_service.deregister_device(
            encrypted_token=audible_auth.encrypted_token,
            user_id=current_user.id
        )
        
        # Delete from database (even if deregistration failed)
        await db.delete(audible_auth)
        await db.commit()
        
        if deregistered:
            message = "Audible account disconnected successfully. Device removed from Amazon account."
        else:
            message = "Audible connection removed. Note: Device may still appear in Amazon account."
        
        logger.info(f"Audible disconnected for user {current_user.id}")
        
        return AudibleDisconnectResponse(
            success=True,
            message=message
        )
    
    except Exception as e:
        logger.error(f"Error disconnecting Audible for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Disconnect failed",
                "detail": str(e)
            }
        )


@router.get(
    "/status",
    response_model=AudibleStatusResponse
)
async def get_audible_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get Audible connection status
    
    Returns information about the current Audible connection:
    - Connection status
    - Marketplace
    - Last sync time
    - Number of imported audiobooks
    """
    try:
        # Get auth
        auth_result = await db.execute(
            select(AudibleAuth).where(AudibleAuth.user_id == current_user.id)
        )
        audible_auth = auth_result.scalar_one_or_none()
        
        if not audible_auth:
            return AudibleStatusResponse(
                connected=False,
                marketplace=None,
                device_name=None,
                last_sync_at=None,
                books_count=None
            )
        
        # Count audiobooks imported from Audible
        books_count_result = await db.execute(
            select(func.count(UserMedia.id))
            .join(Media, UserMedia.media_id == Media.id)
            .where(
                (UserMedia.user_id == current_user.id) &
                (Media.type == 'audiobook') &
                (UserMedia.imported_from == 'audible_api')
            )
        )
        books_count = books_count_result.scalar_one()
        
        return AudibleStatusResponse(
            connected=True,
            marketplace=audible_auth.marketplace,
            device_name=audible_auth.device_name,
            last_sync_at=audible_auth.last_sync_at,
            books_count=books_count
        )
    
    except Exception as e:
        logger.error(f"Error getting Audible status for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to get status",
                "detail": str(e)
            }
        )

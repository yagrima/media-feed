"""
Audible Browser Extension API Endpoints

Receives scraped library data from browser extension and imports to database.
No authentication with Audible required - extension scrapes from user's session.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from app.core.dependencies import get_current_user, get_db
from app.db.models import User
from app.services.audible_parser import AudibleParser
from app.schemas.audible_schemas import (
    AudibleBookFromExtension,
    AudibleExtensionImportRequest,
    AudibleExtensionImportResponse
)
from app.core.middleware import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audible", tags=["audible-extension"])


@router.post(
    "/import-from-extension",
    response_model=AudibleExtensionImportResponse,
    responses={
        400: {"description": "Invalid data format"},
        429: {"description": "Too many requests"}
    }
)
@limiter.limit("20/hour")  # Reasonable limit for manual syncs
async def import_from_extension(
    request: Request,
    import_data: AudibleExtensionImportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Import audiobooks from browser extension
    
    The browser extension scrapes the user's Audible library page
    (while they're logged in) and sends the data here for import.
    
    No Audible authentication required - user is already logged into
    Audible in their browser.
    
    **Rate Limit:** 20 imports per hour per user
    
    **Request Body:**
    ```json
    {
      "books": [
        {
          "title": "Book Title",
          "authors": ["Author Name"],
          "narrators": ["Narrator Name"],
          "length_minutes": 450,
          "asin": "B07XYZ123",
          "cover_url": "https://...",
          "release_date": "2023-01-15",
          "series": "Series Name #1"
        }
      ],
      "marketplace": "de"
    }
    ```
    """
    try:
        logger.info(
            f"Extension import for user {current_user.id}: "
            f"{len(import_data.books)} books from {import_data.marketplace} marketplace"
        )
        
        if not import_data.books:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No books provided"
            )
        
        # Use AudibleParser to process the scraped data
        audible_parser = AudibleParser(db)
        
        # Convert extension format to library format for parser
        library_items = []
        for book in import_data.books:
            library_items.append({
                'title': book.title,
                'authors': book.authors,
                'narrators': book.narrators,
                'runtime_length_min': book.length_minutes,
                'asin': book.asin,
                'cover_url': book.cover_url,
                'release_date': book.release_date,
                'series': book.series
            })
        
        # Process with parser
        stats = await audible_parser.process_library(
            user_id=current_user.id,
            library_data=library_items
        )
        
        logger.info(
            f"Extension import completed for user {current_user.id}: "
            f"{stats['imported']} imported, {stats['updated']} updated, "
            f"{stats['skipped']} skipped, {stats['errors']} errors"
        )
        
        return AudibleExtensionImportResponse(
            success=True,
            message=f"Successfully processed {len(import_data.books)} audiobooks",
            imported=stats['imported'],
            updated=stats['updated'],
            skipped=stats['skipped'],
            errors=stats['errors'],
            total=len(import_data.books)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to import from extension for user {current_user.id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


@router.get(
    "/extension/status",
    response_model=dict,
    responses={
        401: {"description": "Not authenticated"}
    }
)
async def get_extension_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get Audible import status for extension
    
    Returns count of audiobooks currently in library.
    Used by extension to show sync status.
    """
    try:
        from sqlalchemy import select, func
        from app.db.models import Media, UserMedia
        
        # Count audiobooks for this user
        result = await db.execute(
            select(func.count(Media.id.distinct()))
            .join(UserMedia, UserMedia.media_id == Media.id)
            .where(
                UserMedia.user_id == current_user.id,
                Media.type == 'audiobook'
            )
        )
        count = result.scalar()
        
        return {
            "user_id": str(current_user.id),
            "audiobooks_count": count or 0,
            "last_import": None  # TODO: Track last import timestamp
        }
        
    except Exception as e:
        logger.error(f"Failed to get extension status for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve status"
        )

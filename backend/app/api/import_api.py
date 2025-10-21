"""
Import API - Endpoints for CSV and manual media import
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid
from datetime import datetime

from app.core.dependencies import get_current_user, get_db
from app.core.middleware import limiter
from app.db.models import User, ImportJob
from app.schemas.import_schemas import (
    CSVUploadResponse,
    ImportJobStatus,
    ManualImportRequest,
    ManualImportResponse,
    ImportHistoryResponse,
    ImportStatus,
    ImportSource
)
from app.services.validators import CSVValidator
from app.services.import_service import ImportService

router = APIRouter(prefix="/import", tags=["import"])


@router.post(
    "/csv",
    response_model=CSVUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload CSV file for import"
)
@limiter.limit("5/hour")
async def upload_csv(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload CSV file for background processing.

    Supports Netflix viewing history CSV format.

    **Rate Limit:** 5 uploads per hour per user

    **File Requirements:**
    - Max size: 10MB
    - Format: CSV
    - Max rows: 10,000

    **Returns:**
    - job_id: UUID for tracking import status
    - estimated_rows: Number of rows detected
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are accepted"
        )

    # Read file content
    content = await file.read()

    # Validate file size and content
    try:
        CSVValidator.validate_file_content(content)
        row_count = CSVValidator.count_rows(content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Create import job
    import_service = ImportService(db)
    job = await import_service.create_import_job(
        user_id=current_user.id,
        source=ImportSource.NETFLIX_CSV,
        total_rows=row_count,
        file_content=content,
        filename=file.filename
    )

    # Queue background processing (will be implemented with Celery)
    # For now, we'll process synchronously in development
    # TODO: Replace with Celery task
    # process_csv_import.delay(job.id)

    return CSVUploadResponse(
        job_id=job.id,
        message="CSV upload accepted for processing",
        status=ImportStatus.PENDING,
        estimated_rows=row_count
    )


@router.get(
    "/status/{job_id}",
    response_model=ImportJobStatus,
    summary="Get import job status"
)
async def get_import_status(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get status of an import job.

    **Returns:**
    - Current status (pending, processing, completed, failed)
    - Progress information
    - Error details if any
    """
    import_service = ImportService(db)
    job = await import_service.get_import_job(job_id, current_user.id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import job not found"
        )

    return ImportJobStatus(
        job_id=job.id,
        status=ImportStatus(job.status),
        source=ImportSource(job.source),
        total_rows=job.total_rows,
        processed_rows=job.processed_rows,
        successful_rows=job.successful_rows,
        failed_rows=job.failed_rows,
        errors=job.error_log or [],
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at
    )


@router.post(
    "/manual",
    response_model=ManualImportResponse,
    summary="Manually add media item"
)
@limiter.limit("30/minute")
async def manual_import(
    request: Request,
    data: ManualImportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually add a single media item to your library.

    **Rate Limit:** 30 items per minute

    The system will attempt to match the title against the media database.
    """
    import_service = ImportService(db)

    result = await import_service.manual_import(
        user_id=current_user.id,
        title=data.title,
        platform=data.platform,
        consumed_at=data.consumed_at,
        media_type=data.media_type,
        notes=data.notes
    )

    return ManualImportResponse(
        success=result["success"],
        media_id=result.get("media_id"),
        message=result["message"],
        matched_title=result.get("matched_title")
    )


@router.get(
    "/history",
    response_model=ImportHistoryResponse,
    summary="Get import history"
)
async def get_import_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's import history with pagination.

    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    """
    import_service = ImportService(db)

    result = await import_service.get_user_import_history(
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )

    return result


@router.delete(
    "/job/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel import job"
)
async def cancel_import_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a pending import job.

    Only jobs in 'pending' status can be cancelled.
    """
    import_service = ImportService(db)

    cancelled = await import_service.cancel_import_job(job_id, current_user.id)

    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job cannot be cancelled (not found or already processing)"
        )

    return None

"""
Import Service - Business logic for CSV and manual imports
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime
import hashlib

from app.db.models import ImportJob, UserMedia, Media, User
from app.schemas.import_schemas import (
    ImportStatus,
    ImportSource,
    ImportHistoryResponse,
    ImportHistoryItem
)
from app.services.validators import CSVValidator
from app.services.netflix_parser import NetflixCSVParser


class ImportService:
    """Service for handling media imports"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_import_job(
        self,
        user_id: uuid.UUID,
        source: ImportSource,
        total_rows: int,
        file_content: bytes,
        filename: str
    ) -> ImportJob:
        """
        Create a new import job

        Args:
            user_id: User ID
            source: Import source type
            total_rows: Total rows to process
            file_content: File content for hashing
            filename: Original filename

        Returns:
            Created ImportJob
        """
        # Calculate file hash for deduplication
        file_hash = hashlib.sha256(file_content).hexdigest()

        job = ImportJob(
            user_id=user_id,
            source=source.value,
            status=ImportStatus.PENDING.value,
            total_rows=total_rows,
            filename=filename,
            file_size=len(file_content),
            file_hash=file_hash
        )

        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        return job

    async def get_import_job(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[ImportJob]:
        """
        Get import job by ID

        Args:
            job_id: Job ID
            user_id: User ID (for authorization)

        Returns:
            ImportJob or None
        """
        result = await self.db.execute(
            select(ImportJob).where(
                and_(
                    ImportJob.id == job_id,
                    ImportJob.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_job_status(
        self,
        job_id: uuid.UUID,
        status: ImportStatus,
        processed_rows: int = 0,
        successful_rows: int = 0,
        failed_rows: int = 0,
        errors: Optional[List[Dict]] = None
    ) -> None:
        """
        Update import job status

        Args:
            job_id: Job ID
            status: New status
            processed_rows: Number of processed rows
            successful_rows: Number of successful rows
            failed_rows: Number of failed rows
            errors: Error log
        """
        result = await self.db.execute(
            select(ImportJob).where(ImportJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            return

        job.status = status.value
        job.processed_rows = processed_rows
        job.successful_rows = successful_rows
        job.failed_rows = failed_rows

        if errors:
            job.error_log = errors

        if status == ImportStatus.PROCESSING and not job.started_at:
            job.started_at = datetime.utcnow()

        if status in [ImportStatus.COMPLETED, ImportStatus.FAILED, ImportStatus.PARTIAL]:
            job.completed_at = datetime.utcnow()

        await self.db.commit()

    async def process_csv_import(
        self,
        job_id: uuid.UUID,
        csv_content: bytes
    ) -> None:
        """
        Process CSV import job

        Args:
            job_id: Job ID
            csv_content: CSV file content
        """
        # Get job
        result = await self.db.execute(
            select(ImportJob).where(ImportJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            return

        # Update status to processing
        await self.update_job_status(job_id, ImportStatus.PROCESSING)

        try:
            # Parse CSV
            rows = CSVValidator.parse_csv(csv_content)

            # Determine parser based on source
            if job.source == ImportSource.NETFLIX_CSV.value:
                parser = NetflixCSVParser(self.db)
            else:
                # Add other parsers here
                raise ValueError(f"Unsupported import source: {job.source}")

            # Process rows
            errors = []
            successful = 0
            failed = 0

            for idx, row in enumerate(rows, start=1):
                try:
                    await parser.process_row(job.user_id, row)
                    # Commit each row individually to avoid transaction issues
                    await self.db.commit()
                    successful += 1
                except Exception as e:
                    # Rollback this row's transaction
                    await self.db.rollback()
                    failed += 1
                    errors.append({
                        "row": idx,
                        "error": str(e),
                        "data": row
                    })

                # Update progress periodically
                if idx % 10 == 0:
                    await self.update_job_status(
                        job_id,
                        ImportStatus.PROCESSING,
                        processed_rows=idx,
                        successful_rows=successful,
                        failed_rows=failed,
                        errors=errors[:100]  # Limit error log size
                    )

            # Final status
            if failed == 0:
                final_status = ImportStatus.COMPLETED
            elif successful == 0:
                final_status = ImportStatus.FAILED
            else:
                final_status = ImportStatus.PARTIAL

            await self.update_job_status(
                job_id,
                final_status,
                processed_rows=len(rows),
                successful_rows=successful,
                failed_rows=failed,
                errors=errors[:100]
            )

        except Exception as e:
            # Rollback the transaction to avoid InFailedSQLTransactionError
            await self.db.rollback()
            
            # Mark job as failed
            await self.update_job_status(
                job_id,
                ImportStatus.FAILED,
                errors=[{"error": str(e)}]
            )

    async def manual_import(
        self,
        user_id: uuid.UUID,
        title: str,
        platform: str,
        consumed_at: Optional[str] = None,
        media_type: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Manually import a single media item

        Args:
            user_id: User ID
            title: Media title
            platform: Platform name
            consumed_at: Consumption date
            media_type: Type of media
            notes: User notes

        Returns:
            Import result dictionary
        """
        # Search for matching media in database
        # For now, do exact match (will enhance with fuzzy matching later)
        result = await self.db.execute(
            select(Media).where(
                func.lower(Media.title) == title.lower()
            ).limit(1)
        )
        media = result.scalar_one_or_none()

        # If no match, create new media entry
        if not media:
            media = Media(
                title=title,
                type=media_type or "unknown",
                metadata={"manually_added": True}
            )
            self.db.add(media)
            await self.db.flush()

        # Parse consumed_at if provided
        consumed_date = None
        if consumed_at:
            try:
                from dateutil.parser import parse as parse_date
                consumed_date = parse_date(consumed_at).date()
            except Exception as e:
                # Log error but don't fail the import
                logger.warning(f"Failed to parse consumed_at date: {consumed_at}", extra={"error": str(e)})

        # Add to user's library
        user_media = UserMedia(
            user_id=user_id,
            media_id=media.id,
            platform=platform,
            consumed_at=consumed_date,
            imported_from=ImportSource.MANUAL.value,
            raw_import_data={
                "title": title,
                "notes": notes
            }
        )

        self.db.add(user_media)
        await self.db.commit()

        return {
            "success": True,
            "media_id": media.id,
            "message": "Media added successfully",
            "matched_title": media.title
        }

    async def get_user_import_history(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20
    ) -> ImportHistoryResponse:
        """
        Get user's import history

        Args:
            user_id: User ID
            page: Page number
            page_size: Items per page

        Returns:
            Import history response
        """
        # Count total
        count_result = await self.db.execute(
            select(func.count(ImportJob.id)).where(
                ImportJob.user_id == user_id
            )
        )
        total = count_result.scalar_one()

        # Get paginated results
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(ImportJob)
            .where(ImportJob.user_id == user_id)
            .order_by(ImportJob.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        jobs = result.scalars().all()

        # Convert to response schema
        items = [
            ImportHistoryItem(
                job_id=job.id,
                source=ImportSource(job.source),
                status=ImportStatus(job.status),
                total_rows=job.total_rows,
                successful_rows=job.successful_rows,
                failed_rows=job.failed_rows,
                created_at=job.created_at,
                completed_at=job.completed_at
            )
            for job in jobs
        ]

        return ImportHistoryResponse(
            imports=items,
            total=total,
            page=page,
            page_size=page_size
        )

    async def cancel_import_job(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """
        Cancel a pending import job

        Args:
            job_id: Job ID
            user_id: User ID

        Returns:
            True if cancelled, False otherwise
        """
        result = await self.db.execute(
            select(ImportJob).where(
                and_(
                    ImportJob.id == job_id,
                    ImportJob.user_id == user_id,
                    ImportJob.status == ImportStatus.PENDING.value
                )
            )
        )
        job = result.scalar_one_or_none()

        if not job:
            return False

        job.status = ImportStatus.FAILED.value
        job.completed_at = datetime.utcnow()
        job.error_log = [{"error": "Cancelled by user"}]

        await self.db.commit()
        return True

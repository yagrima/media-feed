"""
Import Schemas - Pydantic models for CSV import
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class ImportStatus(str, Enum):
    """Import job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ImportSource(str, Enum):
    """Import source type"""
    NETFLIX_CSV = "netflix_csv"
    MANUAL = "manual"
    API = "api"


class CSVUploadResponse(BaseModel):
    """Response for CSV upload"""
    job_id: uuid.UUID
    message: str
    status: ImportStatus
    estimated_rows: int

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "message": "CSV upload accepted for processing",
                "status": "pending",
                "estimated_rows": 150
            }
        }


class ImportJobStatus(BaseModel):
    """Import job status response"""
    job_id: uuid.UUID
    status: ImportStatus
    source: ImportSource
    total_rows: int
    processed_rows: int
    successful_rows: int
    failed_rows: int
    errors: Optional[List[Dict[str, Any]]] = []
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "processing",
                "source": "netflix_csv",
                "total_rows": 150,
                "processed_rows": 75,
                "successful_rows": 70,
                "failed_rows": 5,
                "errors": [
                    {"row": 12, "error": "Invalid date format"},
                    {"row": 45, "error": "Title too long"}
                ],
                "created_at": "2025-10-19T10:00:00Z",
                "started_at": "2025-10-19T10:00:05Z",
                "completed_at": None
            }
        }


class ManualImportRequest(BaseModel):
    """Manual media import request"""
    title: str = Field(..., min_length=1, max_length=255)
    platform: str = Field(..., min_length=1, max_length=50)
    consumed_at: Optional[str] = None
    media_type: Optional[str] = Field(None, pattern=r'^(movie|tv_series|book|audiobook)$')
    notes: Optional[str] = Field(None, max_length=1000)

    @validator('title')
    def sanitize_title(cls, v):
        """Sanitize title to prevent injection"""
        # Remove null bytes
        v = v.replace('\x00', '')
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '&', '"', "'"]
        for char in dangerous_chars:
            v = v.replace(char, '')
        return v.strip()

    @validator('platform')
    def validate_platform(cls, v):
        """Validate platform name"""
        # Only allow alphanumeric, underscore, hyphen
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Platform name contains invalid characters')
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Breaking Bad",
                "platform": "netflix",
                "consumed_at": "2024-01-15",
                "media_type": "tv_series",
                "notes": "Completed all seasons"
            }
        }


class ManualImportResponse(BaseModel):
    """Manual import response"""
    success: bool
    media_id: Optional[uuid.UUID] = None
    message: str
    matched_title: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "media_id": "456e7890-e89b-12d3-a456-426614174000",
                "message": "Media added successfully",
                "matched_title": "Breaking Bad (2008)"
            }
        }


class ImportHistoryItem(BaseModel):
    """Import history item"""
    job_id: uuid.UUID
    source: ImportSource
    status: ImportStatus
    total_rows: int
    successful_rows: int
    failed_rows: int
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ImportHistoryResponse(BaseModel):
    """Import history response"""
    imports: List[ImportHistoryItem]
    total: int
    page: int
    page_size: int

    class Config:
        json_schema_extra = {
            "example": {
                "imports": [
                    {
                        "job_id": "123e4567-e89b-12d3-a456-426614174000",
                        "source": "netflix_csv",
                        "status": "completed",
                        "total_rows": 150,
                        "successful_rows": 145,
                        "failed_rows": 5,
                        "created_at": "2025-10-19T10:00:00Z",
                        "completed_at": "2025-10-19T10:05:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20
            }
        }

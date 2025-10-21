"""
Input validation and CSV sanitization
"""
import re
from typing import BinaryIO, List, Dict
from fastapi import HTTPException, status, UploadFile
import csv
import io

from app.core.config import settings


class CSVValidator:
    """CSV file validation and sanitization"""

    MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes
    MAX_ROWS = settings.MAX_CSV_ROWS
    ALLOWED_MIME_TYPES = ['text/csv', 'application/csv', 'text/plain']

    @staticmethod
    async def validate_file(file: UploadFile) -> bytes:
        """
        Validate CSV file size and content

        Args:
            file: Uploaded file

        Returns:
            File contents as bytes

        Raises:
            HTTPException: If validation fails
        """
        # Read file content
        content = await file.read()
        file_size = len(content)

        # Check file size
        if file_size > CSVValidator.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded"
            )

        # Validate it's actually CSV-like content
        try:
            content_str = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content_str = content.decode('latin-1')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File encoding not supported. Use UTF-8 or Latin-1"
                )

        # Check if content looks like CSV
        if not (',' in content_str or '\t' in content_str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File does not appear to be a valid CSV"
            )

        return content

    @staticmethod
    def sanitize_cell(value: str) -> str:
        """
        Sanitize CSV cell value to prevent injection attacks

        Args:
            value: Cell value

        Returns:
            Sanitized value
        """
        if not value:
            return ""

        # Remove null bytes
        value = value.replace('\x00', '')

        # Prevent formula injection (CSV injection)
        if value and value[0] in ['=', '+', '-', '@', '\t', '\r']:
            value = "'" + value

        # Remove potentially dangerous characters for SQL
        # Note: We use parameterized queries, but this is defense in depth
        value = value.replace(';', '')
        value = value.replace('--', '')
        value = value.replace('/*', '')
        value = value.replace('*/', '')

        # Limit length
        if len(value) > 500:
            value = value[:500]

        return value.strip()

    @staticmethod
    def validate_file_content(content: bytes) -> None:
        """
        Validate CSV file content

        Args:
            content: File content as bytes

        Raises:
            ValueError: If validation fails
        """
        file_size = len(content)

        # Check file size
        if file_size > CSVValidator.MAX_FILE_SIZE:
            raise ValueError(f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB")

        if file_size == 0:
            raise ValueError("Empty file")

        # Validate it's CSV-like
        try:
            content_str = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content_str = content.decode('latin-1')
            except UnicodeDecodeError:
                raise ValueError("Unsupported file encoding")

        if not (',' in content_str or '\t' in content_str):
            raise ValueError("File does not appear to be CSV")

    @staticmethod
    def count_rows(content: bytes) -> int:
        """
        Count rows in CSV file

        Args:
            content: CSV content as bytes

        Returns:
            Number of data rows (excluding header)
        """
        try:
            content_str = content.decode('utf-8')
        except UnicodeDecodeError:
            content_str = content.decode('latin-1')

        csv_file = io.StringIO(content_str)
        reader = csv.reader(csv_file)
        return sum(1 for row in reader) - 1  # Subtract header

    @staticmethod
    def parse_csv(content: bytes) -> List[Dict[str, str]]:
        """
        Parse and sanitize CSV content

        Args:
            content: CSV file content

        Returns:
            List of sanitized row dictionaries

        Raises:
            HTTPException: If parsing fails or row limit exceeded
        """
        try:
            # Decode content
            try:
                content_str = content.decode('utf-8')
            except UnicodeDecodeError:
                content_str = content.decode('latin-1')

            # Parse CSV
            csv_file = io.StringIO(content_str)
            reader = csv.DictReader(csv_file)

            rows = []
            for i, row in enumerate(reader):
                if i >= CSVValidator.MAX_ROWS:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Too many rows. Maximum: {CSVValidator.MAX_ROWS}"
                    )

                # Sanitize each cell
                sanitized_row = {
                    key: CSVValidator.sanitize_cell(value)
                    for key, value in row.items()
                    if key  # Skip None keys
                }

                rows.append(sanitized_row)

            if not rows:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No data rows found in CSV"
                )

            return rows

        except csv.Error as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CSV parsing error: {str(e)}"
            )


class InputValidator:
    """General input validation utilities"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format

        Args:
            email: Email address

        Returns:
            True if valid
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def sanitize_search_query(query: str) -> str:
        """
        Sanitize search query to prevent injection

        Args:
            query: Search query

        Returns:
            Sanitized query
        """
        # Remove special SQL/NoSQL characters
        query = re.sub(r'[;<>\"\'\\]', '', query)

        # Remove excessive whitespace
        query = ' '.join(query.split())

        # Limit length
        if len(query) > 255:
            query = query[:255]

        return query.strip()

    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        """
        Validate UUID format

        Args:
            uuid_str: UUID string

        Returns:
            True if valid UUID
        """
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(uuid_str))

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove path separators
        filename = filename.replace('/', '').replace('\\', '').replace('..', '')

        # Allow only alphanumeric, dash, underscore, dot
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

        # Limit length
        if len(filename) > 255:
            filename = filename[-255:]

        return filename

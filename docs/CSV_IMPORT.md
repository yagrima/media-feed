# CSV Import Feature Documentation

## Overview

The CSV import feature allows users to bulk import their media viewing history from Netflix and other platforms. The system includes robust validation, sanitization, and background processing capabilities.

## Features

### Security Features
- ✅ File size validation (max 10MB)
- ✅ Row count validation (max 10,000 rows)
- ✅ CSV injection prevention (formula sanitization)
- ✅ Rate limiting (5 uploads per hour per user)
- ✅ File hash tracking for deduplication
- ✅ Input sanitization for all fields

### Functionality
- ✅ Netflix CSV format support
- ✅ Background job processing (ready for Celery)
- ✅ Progress tracking with detailed status
- ✅ Error logging with row-level details
- ✅ Automatic media matching and creation
- ✅ Manual single-item import

## API Endpoints

### 1. Upload CSV
```http
POST /api/import/csv
Content-Type: multipart/form-data
Authorization: Bearer <token>

file: <csv_file>
```

**Rate Limit:** 5 uploads per hour

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "CSV upload accepted for processing",
  "status": "pending",
  "estimated_rows": 150
}
```

### 2. Check Import Status
```http
GET /api/import/status/{job_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "source": "netflix_csv",
  "total_rows": 150,
  "processed_rows": 75,
  "successful_rows": 70,
  "failed_rows": 5,
  "errors": [
    {
      "row": 12,
      "error": "Invalid date format",
      "data": {...}
    }
  ],
  "created_at": "2025-10-19T10:00:00Z",
  "started_at": "2025-10-19T10:00:05Z",
  "completed_at": null
}
```

### 3. Manual Import
```http
POST /api/import/manual
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Breaking Bad",
  "platform": "netflix",
  "consumed_at": "2024-01-15",
  "media_type": "tv_series",
  "notes": "Completed all seasons"
}
```

**Rate Limit:** 30 items per minute

**Response:**
```json
{
  "success": true,
  "media_id": "456e7890-e89b-12d3-a456-426614174000",
  "message": "Media added successfully",
  "matched_title": "Breaking Bad (2008)"
}
```

### 4. Import History
```http
GET /api/import/history?page=1&page_size=20
Authorization: Bearer <token>
```

**Response:**
```json
{
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
```

### 5. Cancel Import Job
```http
DELETE /api/import/job/{job_id}
Authorization: Bearer <token>
```

**Response:** 204 No Content

**Note:** Only pending jobs can be cancelled.

## Netflix CSV Format

### Expected Format
```csv
Title,Date
"Breaking Bad: Season 1: \"Pilot\"","01/20/2024"
"Inception","04/05/2024"
```

### How to Get Your Netflix History

1. Log into your Netflix account
2. Go to Account > Settings
3. Navigate to "Viewing Activity"
4. Click "Download all" at the bottom
5. You'll receive a CSV file via email

### Title Parsing

The system automatically parses Netflix's title format:

**TV Series:**
```
"Show Name: Season X: Episode Name"
→ Main Title: "Show Name"
→ Type: tv_series
→ Metadata: {season: "Season X", episode: "Episode Name"}
```

**Movies:**
```
"Movie Name"
→ Main Title: "Movie Name"
→ Type: movie
```

**Limited Series:**
```
"Show Name: Limited Series: Episode Name"
→ Main Title: "Show Name"
→ Type: tv_series
→ Metadata: {season: "Limited Series", episode: "Episode Name"}
```

### Date Format Support

Supported date formats:
- `MM/DD/YYYY` (US format)
- `DD/MM/YYYY` (European format)
- `YYYY-MM-DD` (ISO format)

## Database Schema

### ImportJob Table
```sql
CREATE TABLE import_jobs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    source VARCHAR(50),              -- netflix_csv, manual, api
    status VARCHAR(50),               -- pending, processing, completed, failed
    total_rows INTEGER,
    processed_rows INTEGER,
    successful_rows INTEGER,
    failed_rows INTEGER,
    error_log JSONB,                 -- Array of error objects
    filename VARCHAR(255),
    file_size INTEGER,
    file_hash VARCHAR(64),           -- SHA256 for deduplication
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

## Security Validations

### File Validation
1. **Size Check:** Maximum 10MB
2. **Encoding:** UTF-8 or Latin-1 only
3. **Format:** Must contain commas or tabs
4. **Row Limit:** Maximum 10,000 rows

### Cell Sanitization
1. **Formula Injection Prevention:** Cells starting with `=`, `+`, `-`, `@` are prefixed with `'`
2. **SQL Character Removal:** Removes `;`, `--`, `/*`, `*/`
3. **Null Byte Removal:** Strips `\x00` characters
4. **Length Limit:** Maximum 500 characters per cell

### Input Validation (Manual Import)
```python
title: str (1-255 chars, sanitized)
platform: str (alphanumeric + underscore/hyphen only)
consumed_at: Optional date string
media_type: Optional enum (movie, tv_series, book, audiobook)
notes: Optional string (max 1000 chars)
```

## Error Handling

### Common Errors

**File Too Large:**
```json
{
  "detail": "File too large. Maximum size: 10MB"
}
```

**Too Many Rows:**
```json
{
  "detail": "Too many rows. Maximum: 10000"
}
```

**Invalid Date:**
```json
{
  "row": 15,
  "error": "Unable to parse date: 13/45/2024"
}
```

**Missing Title:**
```json
{
  "row": 8,
  "error": "Missing title"
}
```

## Implementation Details

### File Processing Flow
```
1. Upload → Validation (size, format)
2. Create ImportJob (status: pending)
3. Queue background processing
4. Process rows sequentially
   - Parse title format
   - Find or create Media entry
   - Create UserMedia link
   - Update progress every 10 rows
5. Final status update (completed/failed/partial)
```

### Media Matching Strategy

**Current Implementation (v1.0):**
- Exact title match (case-insensitive)
- If no match, create new Media entry

**Future Enhancements:**
- Fuzzy string matching (Levenshtein distance)
- External API lookup (TMDB, OMDB)
- Machine learning-based matching

## Testing

### Sample CSV
Located at: `backend/tests/sample_netflix.csv`

Contains 10 test entries with various formats:
- TV series with seasons/episodes
- Movies
- Limited series

### Manual Testing with curl

**Upload CSV:**
```bash
curl -X POST http://localhost:8000/api/import/csv \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@sample_netflix.csv"
```

**Check Status:**
```bash
curl http://localhost:8000/api/import/status/JOB_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Manual Import:**
```bash
curl -X POST http://localhost:8000/api/import/manual \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Breaking Bad",
    "platform": "netflix",
    "consumed_at": "2024-01-15",
    "media_type": "tv_series"
  }'
```

## Future Enhancements

### Phase 2 (Planned)
- [ ] Celery integration for true background processing
- [ ] WebSocket support for real-time progress updates
- [ ] Duplicate detection (same file hash)
- [ ] Bulk import resume on failure
- [ ] CSV export functionality

### Phase 3 (Planned)
- [ ] Support for other platforms (Amazon Prime, Disney+)
- [ ] Advanced fuzzy matching
- [ ] External API integration (TMDB)
- [ ] Automatic series relationship detection
- [ ] Import scheduling (import at specific times)

## Code Structure

```
backend/app/
├── api/
│   └── import_api.py           # API endpoints
├── services/
│   ├── import_service.py       # Business logic
│   ├── netflix_parser.py       # Netflix CSV parser
│   └── validators.py           # CSV validation
├── schemas/
│   └── import_schemas.py       # Pydantic models
└── db/
    └── models.py               # ImportJob model

backend/tests/
└── sample_netflix.csv          # Test data

backend/alembic/versions/
└── 002_add_import_jobs.py      # Database migration
```

## Performance Considerations

### Current Limits
- **File Size:** 10MB
- **Row Count:** 10,000 rows
- **Processing:** Synchronous (blocks during import)
- **Rate Limit:** 5 uploads/hour, 30 manual imports/minute

### Recommendations for Production
1. **Enable Celery** for async processing
2. **Add Redis caching** for frequently accessed data
3. **Implement pagination** for large result sets
4. **Use connection pooling** for database
5. **Monitor job queue** for performance bottlenecks

## Monitoring

### Key Metrics to Track
- Import job success rate
- Average processing time per row
- Failed import reasons (grouped)
- File size distribution
- Peak usage hours

### Logging
All import operations are logged with:
- User ID
- Job ID
- Status changes
- Error details
- Processing duration

## Support

For issues or questions about CSV import:
1. Check error logs in ImportJob.error_log
2. Verify CSV format matches Netflix export
3. Ensure file size and row limits are met
4. Check rate limit status

## References

- [Technical Specification v1.1](../TECHNICAL_SPEC v1.1.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [Security Guidelines](SECURITY.md)

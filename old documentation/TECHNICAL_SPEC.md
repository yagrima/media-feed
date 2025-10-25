# Me Feed - Technical Specification & Implementation Guide

## Project Overview

**Name:** Me Feed (Media Feed)  
**Purpose:** Personal media consumption tracker with automated update monitoring  
**Target Developer:** Junior developer with project lead oversight  
**Development Timeline:** 4 weeks to MVP  

---

## Core Problem Statement

Users lose track of series continuations across multiple streaming platforms and miss new releases in franchises they follow.

---

## MVP Scope & Features

### 1. Media Database Foundation
- Populate comprehensive media catalog via RapidAPI/API marketplace
- Weekly update cycle (configurable via environment variable)
- Store movies, TV shows, books, audiobooks with metadata
- Track series relationships (sequels, seasons, franchises)

### 2. User Media Import
- CSV import for Netflix viewing history
- Manual entry forms for other platforms
- Simple string matching against database titles
- Store platform-specific IDs in extensible JSON column

### 3. Automated Monitoring
- Cross-reference user's consumed media with database
- Identify available sequels/continuations
- Daily checks against existing database (no API calls)
- Track release dates for upcoming content

### 4. Notifications
- Email alerts when sequels become available
- In-app notification center
- Direct links to media platforms

---

## Technical Stack

### Backend
- **Framework:** FastAPI (async, built-in validation, automatic OpenAPI)
- **Database:** PostgreSQL 15+ with JSONB support
- **ORM:** SQLAlchemy 2.0 (async support)
- **Job Queue:** Celery + Redis (configurable schedules)
- **API Client:** httpx (async requests to RapidAPI)

### Frontend
- **Framework:** Next.js 14 (App Router)
- **UI:** Tailwind CSS + shadcn/ui components
- **State:** TanStack Query (server state management)
- **Forms:** react-hook-form + zod validation

### Infrastructure
- **Containerization:** Docker + docker-compose
- **Environment Config:** python-dotenv / next-config
- **Testing:** pytest (backend), Jest (frontend)

---

## Project Structure

```
me-feed/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # Config, security
│   │   ├── db/           # Models, migrations
│   │   ├── services/     # Business logic
│   │   ├── workers/      # Celery tasks
│   │   └── schemas/      # Pydantic models
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── app/              # Next.js app router
│   ├── components/
│   ├── lib/              # API client, utils
│   └── package.json
├── docker-compose.yml
├── .env.example
└── docs/
    ├── API.md
    └── SETUP.md
```

---

## Database Schema

```sql
-- Core media table
CREATE TABLE media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    type VARCHAR(50), -- movie, tv_series, book, audiobook
    release_date DATE,
    platform_ids JSONB DEFAULT '{}', -- {"netflix": "81234", "tmdb": "456", "audible": "xyz"}
    metadata JSONB DEFAULT '{}', -- {"genres": [], "cast": [], "seasons": 5}
    parent_id UUID REFERENCES media(id), -- for sequels/seasons
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_media_title ON media(title);
CREATE INDEX idx_media_platform_ids ON media USING gin(platform_ids);

-- User table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User consumption tracking
CREATE TABLE user_media (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    media_id UUID REFERENCES media(id) ON DELETE CASCADE,
    status VARCHAR(50), -- watched, reading, completed, in_progress
    platform VARCHAR(50), -- where consumed
    consumed_at DATE,
    imported_from VARCHAR(50), -- csv, manual
    raw_import_data JSONB, -- original CSV row for debugging
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, media_id)
);

-- Monitoring queue for notifications
CREATE TABLE monitoring_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    media_id UUID REFERENCES media(id),
    next_media_id UUID REFERENCES media(id), -- detected sequel/continuation
    notified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_monitoring_queue_user_notified ON monitoring_queue(user_id, notified);
```

---

## API Endpoints

### Authentication
```
POST   /api/auth/register       # User registration
POST   /api/auth/login          # User login
POST   /api/auth/logout         # User logout
GET    /api/auth/me            # Current user info
```

### Media Management
```
GET    /api/media/search?q={query}&type={type}&limit={limit}
GET    /api/media/{id}
POST   /api/media/sync          # Admin only - trigger RapidAPI sync
```

### Import Operations
```
POST   /api/import/csv          # Netflix CSV upload
POST   /api/import/manual       # Single item add
GET    /api/import/status/{job_id}
```

### User Library
```
GET    /api/user/media          # User's library with filters
POST   /api/user/media/{id}     # Add/update media status
DELETE /api/user/media/{id}     # Remove from library
GET    /api/user/notifications  # Pending notifications
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

#### Sprint 1 - Days 1-2: Environment Setup
- [ ] Initialize Git repository with proper .gitignore
- [ ] Create Docker Compose configuration with PostgreSQL, Redis
- [ ] Setup FastAPI application with health check endpoint
- [ ] Initialize Next.js project with Tailwind CSS

#### Sprint 1 - Days 3-4: Database Foundation
- [ ] Create database schema with migrations
- [ ] Setup Alembic for database migrations
- [ ] Implement RapidAPI client service
- [ ] Create seed script for test data

#### Sprint 1 - Day 5: Background Jobs
- [ ] Configure Celery worker with Redis
- [ ] Implement media sync task
- [ ] Add error handling and retry logic
- [ ] Setup configurable schedules

### Phase 2: Import & Matching (Week 3)

#### Sprint 2 - Days 1-2: Import Pipeline
- [ ] Build Netflix CSV parser service
- [ ] Create media matching interface
- [ ] Implement exact title matcher
- [ ] Add import status tracking

#### Sprint 2 - Days 3-4: User System
- [ ] Implement user authentication
- [ ] Create user-media relationship handling
- [ ] Build manual media entry endpoints
- [ ] Add consumption tracking

#### Sprint 2 - Day 5: Frontend Core
- [ ] Implement authentication flow
- [ ] Create protected routes
- [ ] Build media browse/search UI
- [ ] Add CSV upload component

### Phase 3: Monitoring & Notifications (Week 4)

#### Days 1-2: Monitoring Logic
- [ ] Build sequel detection algorithm
- [ ] Implement continuation tracking
- [ ] Create monitoring queue processor
- [ ] Add pattern matching for series

#### Days 3-4: Notification System
- [ ] Setup email service (SendGrid/SES)
- [ ] Create notification templates
- [ ] Build notification batching
- [ ] Implement in-app notifications

#### Day 5: Polish & Testing
- [ ] Error handling improvements
- [ ] Admin dashboard basics
- [ ] User preferences UI
- [ ] Integration testing

---

## Core Services Implementation

### Media Sync Service
```python
# services/media_sync.py
from typing import List
import httpx
from app.core.config import settings

class MediaSyncService:
    def __init__(self):
        self.client = httpx.AsyncClient(
            headers={"X-RapidAPI-Key": settings.RAPIDAPI_KEY}
        )
    
    async def sync_media(self, media_type: str = "all"):
        """Fetch and update media database from RapidAPI"""
        # Implementation for different media types
        pass
    
    async def update_relationships(self):
        """Identify and link sequels/seasons"""
        pass
```

### Matching Service
```python
# services/matching.py
from abc import ABC, abstractmethod

class MatcherInterface(ABC):
    @abstractmethod
    def match(self, title: str, year: int = None) -> List[Media]:
        pass

class ExactMatcher(MatcherInterface):
    def match(self, title: str, year: int = None) -> List[Media]:
        """Simple exact string matching"""
        # Normalize title (lowercase, remove special chars)
        # Query database
        # Return matches
        pass

class FuzzyMatcher(MatcherInterface):
    """Future implementation for post-MVP"""
    pass
```

### Monitoring Service
```python
# services/monitoring.py
class MonitoringService:
    def check_for_continuations(self, user_id: UUID):
        """Daily job - no API calls, just DB queries"""
        # 1. Get user's completed media
        # 2. Check media.parent_id relationships
        # 3. Find unwatched sequels/next seasons
        # 4. Queue notifications for new discoveries
        
    def identify_sequel_patterns(self, media: Media):
        """Match common sequel patterns"""
        patterns = [
            r"{title} 2|II|Part 2",
            r"{title}: Season \d+",
            r"{title}: Book \d+",
        ]
        # Returns potential matches for review
```

---

## Configuration Management

### Environment Variables (.env)
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/mefeed
REDIS_URL=redis://localhost:6379

# API Keys
RAPIDAPI_KEY=your_key_here
RAPIDAPI_HOST=your_host_here

# Job Scheduling
MEDIA_UPDATE_INTERVAL=weekly  # weekly|daily|hourly
MONITORING_SCHEDULE=daily
NOTIFICATION_BATCH_SIZE=50

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your_sendgrid_key

# Security
SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# Feature Flags
MATCHING_STRATEGY=exact  # exact|fuzzy|ml
ENABLE_IMPORT_LIMIT=false
MAX_IMPORT_PER_MONTH=100
```

### Configuration Class
```python
# core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    RAPIDAPI_KEY: str
    SECRET_KEY: str
    
    MEDIA_UPDATE_INTERVAL: str = "weekly"
    MONITORING_SCHEDULE: str = "daily"
    
    @property
    def update_cron(self):
        schedules = {
            "hourly": "0 * * * *",
            "daily": "0 0 * * *",
            "weekly": "0 0 * * 0"
        }
        return schedules.get(self.MEDIA_UPDATE_INTERVAL, "0 0 * * 0")
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Testing Strategy

### Unit Tests (Target: 80% coverage)
```python
# tests/test_matching.py
def test_netflix_csv_parser():
    """Test CSV parsing functionality"""
    # Valid CSV format
    # Missing columns handling
    # Unicode title support

def test_media_matching():
    """Test matching algorithms"""
    # Exact match
    # Case insensitive
    # Special characters

# tests/test_monitoring.py  
def test_sequel_detection():
    """Test sequel detection logic"""
    # Direct sequels (parent_id)
    # Season progression
    # No false positives
```

### Integration Tests
- RapidAPI mock responses
- CSV import → matching → storage flow
- Notification trigger → email send
- Database transaction rollbacks

### E2E Test Scenarios
1. User registration → CSV upload → view library
2. Media sync → monitoring run → notification received
3. Manual entry → sequel detection → notification

---

## Deployment Considerations

### Development Setup
```yaml
# docker-compose.yml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: mefeed
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  backend:
    build: ./backend
    depends_on:
      - db
      - redis
    environment:
      DATABASE_URL: postgresql://dev:dev@db/mefeed
      REDIS_URL: redis://redis:6379
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
  
  celery:
    build: ./backend
    command: celery -A app.workers worker --loglevel=info
    depends_on:
      - redis
      - db
    environment:
      DATABASE_URL: postgresql://dev:dev@db/mefeed
      REDIS_URL: redis://redis:6379
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    volumes:
      - ./frontend:/app
```

### Production Deployment Decision (Defer until Week 3)
- **Option A:** Managed Platform (DigitalOcean App Platform, Render, Railway)
  - Higher cost ($50-100/mo)
  - Automatic SSL, scaling, monitoring
  - Lower maintenance burden
  
- **Option B:** VPS Self-Managed (DigitalOcean Droplet, Linode)
  - Lower cost ($10-20/mo)
  - Full control and portability
  - Requires DevOps knowledge

---

## MVP Completion Checklist

### Pre-Launch Requirements
- [ ] 100+ media items populated in database
- [ ] Netflix CSV import tested with 5+ format variations
- [ ] Email delivery verified in production
- [ ] 48-hour stability test completed
- [ ] Database backup/restore verified
- [ ] API documentation complete
- [ ] User guide for CSV export created

### Go/No-Go Metrics
- ✓ Import success rate > 90%
- ✓ Sequel detection accuracy > 95%
- ✓ Page load times < 2 seconds
- ✓ Zero critical bugs in staging
- ✓ All E2E tests passing

---

## Critical Implementation Notes

### Security Considerations
1. **Authentication:** Use JWT tokens with proper expiration
2. **Rate Limiting:** Implement on all public endpoints
3. **Input Validation:** Sanitize all user inputs, especially CSV data
4. **API Keys:** Never expose in frontend code
5. **CORS:** Configure properly for production domain

### Performance Optimizations
1. **Database Indexes:** On title, platform_ids, user_id
2. **Caching Strategy:** Redis for frequently accessed media
3. **Pagination:** Required for all list endpoints
4. **Lazy Loading:** For frontend media browsing
5. **Background Jobs:** Never block API responses

### Error Handling
1. **API Rate Limits:** Exponential backoff with circuit breaker
2. **Import Failures:** Queue for manual review
3. **Notification Failures:** Dead letter queue with retry
4. **Database Constraints:** Proper error messages to user

---

## Post-MVP Roadmap

### Tier 1: Enhanced Core (Months 1-2)
- Fuzzy string matching with Levenshtein distance
- Alias resolution system
- Streaming availability APIs (JustWatch/Watchmode)
- Platform deep linking
- Manual match correction UI

### Tier 2: Social Features (Months 3-4)
- Multi-tenant architecture
- Friend/contact system
- Shared watchlists
- Social recommendations
- Progress tracking

### Tier 3: Monetization (Months 5-6)
- Affiliate link generation
- Premium tier features
- API access for developers
- Advanced analytics dashboard

---

## Developer Resources

### Quick Start Commands
```bash
# Clone and setup
git clone [repo-url]
cd me-feed
cp .env.example .env

# Start development environment
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Seed test data
docker-compose exec backend python scripts/seed.py

# Run tests
docker-compose exec backend pytest
docker-compose exec frontend npm test

# Access services
# API: http://localhost:8000/docs
# Frontend: http://localhost:3000
# Database: localhost:5432
# Redis: localhost:6379
```

### Key Files to Create First
1. `backend/app/core/config.py` - Configuration management
2. `backend/app/db/models.py` - SQLAlchemy models
3. `backend/app/api/deps.py` - Common dependencies
4. `backend/app/services/media_sync.py` - RapidAPI integration
5. `frontend/lib/api.ts` - API client wrapper

---

## Contact & Support

**Project Lead:** Available for code review and architectural decisions  
**Documentation:** This document is the source of truth  
**Updates:** Any scope changes will be documented here first  

---

*Last Updated: Current Version - Ready for Claude Code CLI Implementation*
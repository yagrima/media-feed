# Me Feed - MVP Roadmap (Frontend-First Strategy)

**Document Version**: 1.0
**Last Updated**: October 19, 2025
**Strategy**: Deliver user-facing value first, complete infrastructure later
**Timeline**: 3 weeks to usable MVP, 6 weeks to full feature set

---

## Executive Summary

**Current Status**: Backend complete (Weeks 1-3A), Frontend starting (Week 3B)

**Strategic Shift**: Instead of building perfect infrastructure before user validation, we're pivoting to a frontend-first approach:
- ✅ **Week 1-2**: Secure backend foundation (DONE)
- ✅ **Week 3A**: CSV import backend (DONE)
- 🚧 **Week 3B**: Minimal viable frontend (CURRENT)
- 📋 **Week 4**: Core value features (sequel detection + notifications)
- 📋 **Week 5-6**: Enhanced UX + scale features

**Key Principle**: All features preserved, only resequenced for faster user validation.

---

## Week-by-Week Breakdown

### Week 1-2: Secure Foundation ✅ COMPLETE

**Status**: 100% Complete

**Achievements**:
- [x] JWT authentication with RS256
- [x] Refresh token rotation
- [x] Database models (PostgreSQL)
- [x] Rate limiting middleware
- [x] Input validation and sanitization
- [x] Audit logging
- [x] Docker setup with secrets management
- [x] Security headers and CORS

**Security Rating**: A- (Very Strong) ⬆️
**Container Security**: ✅ Non-root user (appuser:1000)

---

### Week 3A: CSV Import Backend ✅ COMPLETE

**Status**: 100% Complete

**Achievements**:
- [x] CSV upload API endpoint
- [x] Netflix CSV parser (title extraction, season detection)
- [x] Import job tracking (status, errors, progress)
- [x] File validation (size, format, injection prevention)
- [x] Rate limiting (5 uploads/hour)
- [x] SHA256 file hashing
- [x] Comprehensive documentation

**Files Created**: 8 new files, ~1,200 LOC

---

### Week 3B: Security Fixes + Minimal Viable Frontend 🚧 CURRENT

**Duration**: 5 days (Days 4-8 of Week 3)
**Goal**: Complete critical security fixes, then deliver usable web interface
**Priority**: 🔴 CRITICAL - Security first, then user testing

---

#### Day 1 Morning (2 hours): Critical Security Quick Wins 🔒

**Priority**: 🔴 CRITICAL - Complete before frontend work
**Rationale**: Small time investment (2h) for A- security rating

**Security Tasks** (Sequential execution):
```bash
# Fix 1: Environment Validation (15 min)
- [ ] Add DATABASE_URL validator to backend/app/core/config.py
- [ ] Add REDIS_URL validator to backend/app/core/config.py
- [ ] Test with placeholder passwords (should fail in production mode)

# Fix 2: Origin Header Validation (30 min)
- [ ] Add origin_validation_middleware to backend/app/core/middleware.py
- [ ] Register middleware in backend/app/main.py
- [ ] Test with valid/invalid origins

# Fix 3: Dependency Updates (1 hour)
- [ ] Update requirements.txt (cryptography 41→43, fastapi 0.104→0.115)
- [ ] Run pip install --upgrade
- [ ] Run existing tests to verify compatibility
- [ ] Test server startup and basic endpoints
```

**Deliverable**: 4 of 5 critical security fixes complete (80%), A- security rating achieved

**Note**: Structured logging (2h) will be implemented in parallel during frontend setup

---

#### Day 1 Afternoon - Day 2: Core UI Foundation

**Tasks**:
```bash
# Project Setup
- [ ] Initialize Next.js 14 with TypeScript
      npx create-next-app@latest frontend --typescript --tailwind --app
- [ ] Install dependencies
      - shadcn/ui (component library)
      - axios (HTTP client)
      - react-hook-form + zod (form validation)
      - @tanstack/react-query (server state)
      - sonner (toast notifications)
- [ ] Configure environment variables (.env.local)
      NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Authentication Pages**:
```
/app/
├── (auth)/
│   ├── login/page.tsx          # Login form
│   ├── register/page.tsx       # Registration form
│   └── layout.tsx              # Auth layout (centered, no nav)
├── (dashboard)/
│   ├── layout.tsx              # Dashboard layout (with nav)
│   └── page.tsx                # Home/Library page
└── layout.tsx                  # Root layout
```

**Core Components**:
- [x] Login form (email, password, remember me)
- [x] Register form (email, password, confirm password)
- [x] Form validation with zod schemas
- [x] Error handling and display
- [x] Loading states

**API Integration**:
```typescript
// lib/api/auth.ts
export const authApi = {
  login: (email: string, password: string) =>
    axios.post('/api/auth/login', { email, password }),
  register: (email: string, password: string) =>
    axios.post('/api/auth/register', { email, password }),
  refresh: (refreshToken: string) =>
    axios.post('/api/auth/refresh', { refresh_token: refreshToken }),
  logout: () => axios.post('/api/auth/logout')
}

// lib/auth/token-manager.ts
- JWT storage in localStorage
- Automatic refresh on 401
- Axios interceptors for auth headers
```

**Protected Routes**:
```typescript
// components/auth/protected-route.tsx
- Redirect to /login if not authenticated
- Show loading spinner during auth check
- Refresh token if expired
```

**PARALLEL TASK** (During frontend setup):
```bash
# Fix 4: Structured Logging (2 hours, backend work)
- [ ] Add python-json-logger to requirements.txt
- [ ] Create backend/app/core/logging_config.py
- [ ] Replace print() statements in services
- [ ] Test log output format
```

**Deliverable**:
- Users can register, login, see protected dashboard
- All 5 critical security fixes complete (100%) ✅
- Security rating: A- (Very Strong)

---

#### Day 3-4: CSV Import UI

**Tasks**:

**Upload Component**:
```typescript
// app/(dashboard)/import/page.tsx
- [x] Drag-and-drop zone (react-dropzone)
- [x] File size validation (client-side)
- [x] File type validation (.csv only)
- [x] Upload button
- [x] Progress bar during upload
```

**Import Status Tracking**:
```typescript
// components/import/import-status.tsx
- [x] Poll API every 2 seconds for job status
- [x] Show progress (processed/total rows)
- [x] Display errors with row numbers
- [x] Success/failure notifications (sonner)
- [x] Cancel job button (for pending jobs)
```

**Import History**:
```typescript
// components/import/import-history.tsx
- [x] Table of past imports
- [x] Columns: Date, Filename, Status, Rows, Actions
- [x] Status badges (pending/processing/completed/failed)
- [x] View details button (modal with errors)
- [x] Pagination (if >20 imports)
```

**API Integration**:
```typescript
// lib/api/import.ts
export const importApi = {
  uploadCSV: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return axios.post('/api/import/csv', formData)
  },
  getStatus: (jobId: string) =>
    axios.get(`/api/import/status/${jobId}`),
  getHistory: (page: number) =>
    axios.get(`/api/import/history?page=${page}`),
  cancelJob: (jobId: string) =>
    axios.delete(`/api/import/job/${jobId}`)
}
```

**Deliverable**: Users can upload Netflix CSV and track import progress

---

#### Day 5: Library View (Basic)

**Tasks**:

**Media Grid Component**:
```typescript
// app/(dashboard)/library/page.tsx
- [x] Fetch user media from API
- [x] Grid layout (responsive: 1/2/3/4 columns)
- [x] Media cards with:
      - Title
      - Type badge (Movie/TV Series)
      - Platform icon
      - Consumed date
- [x] Empty state ("Upload your first CSV to get started")
- [x] Loading skeleton
```

**Filtering**:
```typescript
// components/library/filters.tsx
- [x] Tabs: All / Movies / TV Series
- [x] Update API query on filter change
- [x] Active filter indication
```

**State Management**:
```typescript
// Using @tanstack/react-query
const { data, isLoading, error } = useQuery({
  queryKey: ['user-media', filters],
  queryFn: () => mediaApi.getUserMedia(filters)
})
```

**API Integration**:
```typescript
// lib/api/media.ts
export const mediaApi = {
  getUserMedia: (filters?: { type?: string }) =>
    axios.get('/api/user/media', { params: filters })
}

// Backend endpoint to implement:
GET /api/user/media
  - Query params: type (movie/tv_series), page, limit
  - Returns: { items: UserMedia[], total: number }
```

**Deliverable**: Users see their imported media in a browsable library

---

**Week 3B Success Criteria**:
- ✅ Users can register and login
- ✅ Users can upload Netflix CSV via UI
- ✅ Users see import progress in real-time
- ✅ Users view their media library
- ✅ Responsive design (mobile-friendly)
- ✅ Error handling for all API calls

**Estimated Effort**: 40 hours (8h/day × 5 days)

---

### Week 4: Core Value Features

**Duration**: 5 days
**Goal**: End-to-end sequel notification flow
**Priority**: 🔴 CRITICAL - Core product value

#### Day 1-2: Sequel Detection Backend

**Database Schema Updates**:
```sql
-- Add to media table
ALTER TABLE media ADD COLUMN base_title VARCHAR(255);
ALTER TABLE media ADD COLUMN season_number INTEGER;
ALTER TABLE media ADD COLUMN tmdb_id INTEGER;
ALTER TABLE media ADD COLUMN imdb_id VARCHAR(20);

-- Indexes
CREATE INDEX idx_media_base_title ON media(base_title);
CREATE INDEX idx_media_tmdb ON media(tmdb_id);
```

**Title Parsing Service**:
```python
# backend/app/services/title_parser.py
class TitleParser:
    def extract_base_title(self, netflix_title: str) -> dict:
        """
        Extract base title and season from Netflix format
        "Breaking Bad: Season 5: Episode 1" →
        { base: "Breaking Bad", season: 5, type: "tv_series" }
        """
        # Regex patterns for various formats
        # Return: base_title, season_number, episode_name
```

**Sequel Matching Algorithm**:
```python
# backend/app/services/sequel_detector.py
class SequelDetector:
    def find_sequels(self, user_media: UserMedia) -> List[Media]:
        """
        Find potential sequels for user's consumed media
        1. Extract base title
        2. Find media with same base_title
        3. Filter for higher season numbers
        4. Check release date (must be available)
        """
        # Returns list of sequel candidates with confidence scores
```

**TMDB API Integration**:
```python
# backend/app/services/tmdb_client.py
class TMDBClient:
    def search_tv(self, title: str) -> dict:
        """Search TMDB for TV series metadata"""

    def get_season_info(self, series_id: int, season: int) -> dict:
        """Get season details (release date, episode count)"""

    def enrich_media(self, media: Media) -> Media:
        """Add TMDB metadata to media object"""
```

**Background Job**:
```python
# backend/app/workers/tasks.py
@celery.task
def check_for_sequels():
    """
    Daily task to check for new sequels
    1. Get all users
    2. For each user, get their media
    3. Check for sequels
    4. Create notification if found
    """
```

**API Endpoints**:
```python
# New endpoints needed
GET /api/user/sequels          # List detected sequels
POST /api/admin/run-detection  # Manually trigger sequel check (dev only)
```

**Deliverable**: Backend can detect sequels and create notifications

---

#### Day 3-4: Email Notification System

**Database Model**:
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    type VARCHAR(50),              -- sequel_found, season_released
    media_id UUID REFERENCES media(id),
    sequel_id UUID REFERENCES media(id),
    read BOOLEAN DEFAULT false,
    emailed BOOLEAN DEFAULT false,
    unsubscribe_token VARCHAR(255),
    created_at TIMESTAMP
);

CREATE TABLE notification_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    email_enabled BOOLEAN DEFAULT true,
    email_frequency VARCHAR(20) DEFAULT 'daily',  -- daily, weekly, instant
    in_app_enabled BOOLEAN DEFAULT true
);
```

**Email Service**:
```python
# backend/app/services/email_service.py
class EmailService:
    def __init__(self):
        self.smtp_client = SMTPClient(settings.SMTP_HOST)

    def send_sequel_notification(self, user: User, sequels: List[Media]):
        """Send email about newly found sequels"""
        # HTML + plain text templates
        # Unsubscribe link
        # Platform links

    def send_daily_digest(self):
        """Send daily summary to all users with new notifications"""
```

**Email Templates**:
```html
<!-- backend/app/templates/emails/sequel_found.html -->
<h1>New Sequels Found!</h1>
<p>Hi {{ user.email }},</p>
<p>We found {{ sequels|length }} new sequel(s) for shows you've watched:</p>

{% for sequel in sequels %}
<div class="sequel-card">
    <h2>{{ sequel.title }}</h2>
    <p>{{ sequel.base_title }} - Season {{ sequel.season_number }}</p>
    <a href="{{ sequel.platform_link }}">Watch on {{ sequel.platform }}</a>
</div>
{% endfor %}

<a href="{{ unsubscribe_url }}">Unsubscribe</a>
```

**Celery Tasks**:
```python
# backend/app/workers/tasks.py
@celery.task
def send_daily_digest():
    """
    Run at 9am daily
    1. Get users with email_enabled=true and frequency='daily'
    2. Get their unread notifications
    3. Send digest email
    4. Mark notifications as emailed
    """

@celery.beat_schedule
schedule = {
    'sequel-check': {
        'task': 'tasks.check_for_sequels',
        'schedule': crontab(hour=3, minute=0),  # 3am daily
    },
    'daily-digest': {
        'task': 'tasks.send_daily_digest',
        'schedule': crontab(hour=9, minute=0),  # 9am daily
    }
}
```

**API Endpoints**:
```python
GET /api/notifications                 # List user's notifications
PUT /api/notifications/{id}/read       # Mark as read
GET /api/notifications/preferences     # Get preferences
PUT /api/notifications/preferences     # Update preferences
GET /api/notifications/unsubscribe     # Unsubscribe via token
```

**Deliverable**: Users receive email notifications for sequels

---

#### Day 5: Notifications UI

**Notification Center Component**:
```typescript
// app/(dashboard)/notifications/page.tsx
- [x] List of notifications (newest first)
- [x] Notification card:
      - Sequel title + season
      - Platform badge
      - "Watch Now" link
      - Mark as read button
- [x] Filter: Unread / All
- [x] "Mark all as read" button
- [x] Empty state ("No notifications yet")
```

**Badge in Navbar**:
```typescript
// components/layout/navbar.tsx
- [x] Bell icon with unread count badge
- [x] Dropdown preview (latest 5 notifications)
- [x] "View All" link to /notifications
- [x] Real-time updates (poll every 30s)
```

**Notification Preferences UI**:
```typescript
// app/(dashboard)/settings/notifications/page.tsx
- [x] Toggle: Email notifications on/off
- [x] Select: Email frequency (instant/daily/weekly)
- [x] Toggle: In-app notifications on/off
- [x] Test notification button
```

**API Integration**:
```typescript
// lib/api/notifications.ts
export const notificationsApi = {
  getAll: () => axios.get('/api/notifications'),
  markRead: (id: string) =>
    axios.put(`/api/notifications/${id}/read`),
  markAllRead: () =>
    axios.put('/api/notifications/mark-all-read'),
  getPreferences: () =>
    axios.get('/api/notifications/preferences'),
  updatePreferences: (prefs: NotificationPrefs) =>
    axios.put('/api/notifications/preferences', prefs)
}
```

**Deliverable**: Users see and manage notifications in the UI

---

**Week 4 Success Criteria**:
- ✅ System detects sequels for user's media
- ✅ Users receive daily email digest
- ✅ In-app notification center works
- ✅ Users can manage notification preferences
- ✅ Background jobs run on schedule

**This is the CORE VALUE delivery week**

---

### Week 5: Enhanced User Experience

**Duration**: 5 days
**Goal**: Polished user interface and manual management
**Priority**: 🟡 HIGH - Improves usability

#### Day 1-2: Manual Media Management

**Add Media Form**:
```typescript
// app/(dashboard)/library/add/page.tsx
- [x] Search TMDB for titles (autocomplete)
- [x] Select from search results
- [x] Form fields:
      - Title (auto-filled from search)
      - Platform (dropdown: Netflix, Prime, etc.)
      - Type (auto-filled)
      - Consumed date
      - Notes (optional)
- [x] Submit and add to library
```

**Edit Media**:
```typescript
// components/library/media-card.tsx
- [x] Edit button (opens modal)
- [x] Editable fields: platform, consumed date, notes
- [x] Save changes
```

**Delete Media**:
```typescript
- [x] Delete button with confirmation
- [x] Optimistic UI update
- [x] Undo option (toast notification)
```

**Bulk Actions**:
```typescript
// components/library/bulk-actions.tsx
- [x] Checkbox selection
- [x] "Select All" checkbox
- [x] Bulk delete
- [x] Bulk change platform
```

**Backend Endpoints**:
```python
POST   /api/user/media           # Add media manually
PUT    /api/user/media/{id}      # Update media
DELETE /api/user/media/{id}      # Delete media
POST   /api/user/media/bulk      # Bulk operations
GET    /api/media/search         # Search TMDB
```

---

#### Day 3-4: Advanced Library Features

**Search and Filters**:
```typescript
// components/library/search-filter.tsx
- [x] Search input (filter by title)
- [x] Platform filter (multi-select)
- [x] Type filter (movie/series)
- [x] Date range filter
- [x] Clear filters button
```

**Sort Options**:
```typescript
- [x] Sort by: Date added, Title (A-Z), Platform
- [x] Ascending/descending toggle
- [x] Remember user's preference (localStorage)
```

**Pagination**:
```typescript
// For libraries >50 items
- [x] Page size selector (20/50/100)
- [x] Page navigation (prev/next)
- [x] Jump to page input
- [x] Total count display
```

**Media Detail View**:
```typescript
// app/(dashboard)/library/[id]/page.tsx
- [x] Full media details
- [x] TMDB metadata (poster, synopsis, rating)
- [x] Related media (sequels/prequels)
- [x] Watch history (if multiple views)
- [x] Edit/delete buttons
```

**UI Enhancements**:
```typescript
- [x] View toggle: Grid / List
- [x] Media posters (from TMDB)
- [x] Platform icons and colors
- [x] Type badges styling
- [x] Smooth transitions
```

---

#### Day 5: User Settings & Profile

**Profile Page**:
```typescript
// app/(dashboard)/settings/profile/page.tsx
- [x] Email (read-only)
- [x] Change password form
- [x] Account created date
- [x] Statistics:
      - Total media tracked
      - Sequels found
      - Notifications received
```

**Active Sessions**:
```typescript
// app/(dashboard)/settings/sessions/page.tsx
- [x] List active sessions
      - Device info (user agent)
      - IP address
      - Last active
      - Current session indicator
- [x] Revoke session button
- [x] Revoke all other sessions
```

**Data Export (GDPR)**:
```typescript
// app/(dashboard)/settings/data/page.tsx
- [x] Export all data button
      - Downloads JSON file
      - Includes: media, notifications, preferences
- [x] Delete account button
      - Confirmation modal
      - Password verification
      - Irreversible warning
```

**Backend Endpoints**:
```python
PUT    /api/auth/change-password
GET    /api/user/export            # GDPR data export
DELETE /api/user/account           # Account deletion
```

---

**Week 5 Success Criteria**:
- ✅ Users can manually add/edit/delete media
- ✅ Advanced search and filtering works
- ✅ Media detail pages are informative
- ✅ User settings are comprehensive
- ✅ GDPR compliance features implemented

---

### Week 6: Scale & Optimization

**Duration**: 5 days
**Goal**: Production-ready performance and scale
**Priority**: 🟡 HIGH - Required for launch

#### Day 1-2: Celery Integration

**Why Now**: CSV imports block requests, background jobs needed for scale

**Celery Setup**:
```python
# backend/app/workers/celery_app.py
from celery import Celery

celery_app = Celery(
    'mefeed',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
```

**Async CSV Processing**:
```python
# backend/app/workers/tasks.py
@celery.task(bind=True)
def process_csv_import(self, job_id: str, file_path: str):
    """
    Process CSV import in background
    - Update job status to 'processing'
    - Parse CSV rows
    - Update progress every 10 rows (self.update_state)
    - Handle errors
    - Update job status to 'completed'/'failed'
    """
```

**Progress Tracking**:
```python
# Use Celery task states
self.update_state(
    state='PROGRESS',
    meta={'current': 50, 'total': 100}
)

# Frontend polls task status
GET /api/import/task/{task_id}
```

**Retry Logic**:
```python
@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_email(self, user_id: str, notification_id: str):
    try:
        # Send email
    except SMTPException as exc:
        raise self.retry(exc=exc)
```

---

#### Day 3-4: Advanced Matching & Multi-Platform

**Fuzzy String Matching**:
```python
# backend/app/services/fuzzy_matcher.py
from fuzzywuzzy import fuzz

class FuzzyMatcher:
    def match_title(self, query: str, candidates: List[str]) -> List[tuple]:
        """
        Use Levenshtein distance for fuzzy matching
        Returns: [(title, confidence_score), ...]
        """
        scores = [(c, fuzz.ratio(query, c)) for c in candidates]
        return sorted(scores, key=lambda x: x[1], reverse=True)
```

**Alias Detection**:
```python
# backend/app/services/alias_detector.py
# Handle alternate titles:
# "Game of Thrones" = "GoT" = "A Song of Ice and Fire"
ALIASES = {
    "got": "Game of Thrones",
    "bb": "Breaking Bad",
    # Load from database or JSON
}
```

**Multi-Platform CSV Parsers**:
```python
# backend/app/services/parsers/
├── netflix_parser.py      # Already done
├── prime_parser.py        # New
├── disney_parser.py       # New
└── generic_parser.py      # Fallback

# Parser detection logic
def detect_parser(csv_content: str) -> Parser:
    """Auto-detect platform from CSV headers/format"""
```

**Platform-Specific Links**:
```python
# backend/app/services/platform_links.py
PLATFORM_URLS = {
    'netflix': 'https://www.netflix.com/title/{id}',
    'prime': 'https://www.amazon.com/dp/{id}',
    'disney': 'https://www.disneyplus.com/series/{slug}',
}
```

---

#### Day 5: Testing Suite

**Backend Unit Tests**:
```python
# backend/tests/
├── test_auth.py           # Auth service tests
├── test_import.py         # CSV import tests
├── test_sequel_detection.py
├── test_notifications.py
└── test_security.py       # Injection, validation tests

# Run with coverage
pytest --cov=app --cov-report=html
```

**Frontend Tests**:
```typescript
// frontend/__tests__/
├── components/
│   ├── auth/login.test.tsx
│   └── library/media-grid.test.tsx
├── pages/
│   └── library.test.tsx
└── utils/
    └── token-manager.test.ts

// Run with Jest
npm run test
```

**Integration Tests**:
```python
# backend/tests/integration/
└── test_full_flow.py
    - Test: Register → Login → Upload CSV → View Library → Get Notification
```

**E2E Tests (Playwright)**:
```typescript
// frontend/e2e/
└── user-journey.spec.ts
    - Complete user flow from signup to notification
```

---

**Week 6 Success Criteria**:
- ✅ CSV imports don't block requests (Celery)
- ✅ Background jobs run reliably
- ✅ Fuzzy matching improves accuracy
- ✅ Multi-platform support works
- ✅ Test coverage >70%

---

### Week 7+: Production Hardening

**Duration**: Ongoing
**Goal**: Launch-ready application
**Priority**: 🟢 MEDIUM - Can ship without, improve iteratively

#### Security Hardening

**Critical Fixes** (from Security Audit):
```bash
# 1. Docker container non-root user
# backend/Dockerfile
RUN groupadd -g 1000 mefeed && useradd -u 1000 -g mefeed mefeed
USER mefeed

# 2. Environment validation
# backend/app/core/config.py
@validator('DATABASE_URL')
def validate_no_defaults(cls, v):
    if 'CHANGE_THIS_PASSWORD' in v:
        raise ValueError('Default passwords not allowed')

# 3. Origin header validation
# backend/app/core/middleware.py
async def validate_origin(request: Request):
    origin = request.headers.get('origin')
    if origin not in settings.allowed_origins_list:
        raise HTTPException(403, "Invalid origin")

# 4. Structured logging
# Replace all print() with proper logging
import structlog
logger = structlog.get_logger()
```

**Dependency Updates**:
```bash
# Update outdated packages
pip install --upgrade cryptography fastapi sqlalchemy
pip-audit  # Check for vulnerabilities
```

---

#### Performance Optimization

**Database**:
```sql
-- Add missing indexes
CREATE INDEX idx_user_media_user_type ON user_media(user_id, type);
CREATE INDEX idx_notifications_user_read ON notifications(user_id, read);

-- Query optimization
EXPLAIN ANALYZE SELECT ...;  -- Find slow queries
```

**Redis Caching**:
```python
# Cache frequently accessed data
@cache.memoize(timeout=3600)
def get_user_media(user_id: str):
    # Cache user's media library for 1 hour
```

**API Response Compression**:
```python
# backend/app/main.py
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

**Frontend Optimization**:
```typescript
// Code splitting
const MediaLibrary = lazy(() => import('./components/MediaLibrary'))

// Image optimization
import Image from 'next/image'
<Image src={poster} width={300} height={450} />

// API response caching
queryClient.setDefaultOptions({
  queries: { staleTime: 5 * 60 * 1000 } // 5 minutes
})
```

---

#### Monitoring & Observability

**Prometheus Metrics**:
```python
# backend/app/monitoring/metrics.py
from prometheus_client import Counter, Histogram

http_requests_total = Counter('http_requests_total', 'Total HTTP requests')
import_duration = Histogram('csv_import_duration_seconds', 'CSV import duration')
```

**Error Tracking (Sentry)**:
```python
# backend/app/main.py
import sentry_sdk
sentry_sdk.init(dsn=settings.SENTRY_DSN)
```

**Logging (Structured)**:
```python
# backend/app/core/logging_config.py
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
```

**Uptime Monitoring**:
- UptimeRobot or Pingdom
- Monitor /health endpoint
- Alert on 5xx errors

---

**Week 7+ Success Criteria**:
- ✅ Security audit passes (all HIGH issues fixed)
- ✅ Dependencies updated and scanned
- ✅ API response time <200ms (p95)
- ✅ Error rate <0.1%
- ✅ Monitoring dashboards operational

---

## Timeline Summary

```
Week 1-2:  Backend Foundation            ✅ DONE
Week 3A:   CSV Import Backend            ✅ DONE
Week 3B:   Frontend MVP (5 days)         🚧 CURRENT → Usable Product
Week 4:    Sequel Detection + Notify     📋 NEXT    → Core Value
Week 5:    Enhanced UX                   📋 PLANNED → Polished Product
Week 6:    Celery + Scale Features       📋 PLANNED → Production Ready
Week 7+:   Security + Optimization       📋 ONGOING → Launch Ready
```

**Key Milestones**:
- **Day 8 (Week 3B end)**: First usable MVP → User testing starts
- **Day 13 (Week 4 end)**: Core value delivered → Product validation
- **Day 20 (Week 5 end)**: Polished UX → Beta launch
- **Day 27 (Week 6 end)**: Production ready → Public launch
- **Week 7+**: Iterate based on user feedback

---

## Success Metrics

### Week 3B (Frontend MVP)
- ✅ 5 early testers can register and use the app
- ✅ CSV upload works without errors
- ✅ Library view displays media correctly
- ✅ Mobile responsive (works on phone)

### Week 4 (Core Value)
- ✅ Sequel detection finds >80% of obvious sequels
- ✅ Email notifications delivered successfully
- ✅ <5% false positive rate
- ✅ Users report "this is useful" (qualitative)

### Week 6 (Launch Ready)
- ✅ 100 beta users signed up
- ✅ 50+ CSV imports completed
- ✅ 20+ sequel notifications sent
- ✅ No critical bugs
- ✅ Security audit passed

---

## Risk Mitigation

### Risk: Frontend Takes Longer Than 5 Days
**Mitigation**:
- Use shadcn/ui for pre-built components
- Focus on functionality over perfection
- Skip animations and polish initially
- Can extend to 7 days if needed

### Risk: TMDB API Rate Limits
**Mitigation**:
- Cache TMDB responses in database
- Rate limit user searches (10/minute)
- Fallback to local data if API unavailable

### Risk: Email Deliverability Issues
**Mitigation**:
- Use SendGrid (established sender reputation)
- Configure SPF/DKIM records
- Start with small batches
- In-app notifications as fallback

### Risk: Low User Engagement
**Mitigation**:
- This is WHY we ship Week 3B - early validation
- Gather feedback and iterate
- Adjust features based on user needs
- Pivot if necessary

---

## Resources Required

### Team
- **1 Full-Stack Developer** (Weeks 3B-6)
  - Frontend: React/Next.js
  - Backend: Python/FastAPI
  - 40 hours/week

### External Services
- **TMDB API**: Free (up to 50 req/sec)
- **SendGrid**: Free tier (100 emails/day, then $15/mo)
- **Hosting** (Week 7+):
  - Backend: Heroku/Railway ($7/mo)
  - Database: Managed PostgreSQL ($15/mo)
  - Frontend: Vercel (free tier)
  - **Total**: ~$25/mo

### Optional
- **Freelance Designer**: Landing page ($500, Week 5)
- **Penetration Testing**: Security audit ($1K, Week 7)

---

## Deliverables by Phase

### Phase 2B (Week 3B) - MVP UI
- [x] Next.js project with auth pages
- [x] CSV upload interface
- [x] Media library grid view
- [x] Responsive design
- [x] API integration complete

### Phase 3 (Week 4) - Core Value
- [x] Sequel detection working
- [x] Email notification system
- [x] In-app notification center
- [x] Background jobs running

### Phase 4 (Week 5) - Enhanced UX
- [x] Manual media management
- [x] Advanced filtering
- [x] User settings
- [x] GDPR compliance

### Phase 5 (Week 6) - Scale
- [x] Celery background processing
- [x] Multi-platform support
- [x] Testing suite
- [x] Performance optimized

### Phase 6 (Week 7+) - Launch
- [x] Security hardened
- [x] Monitoring enabled
- [x] Documentation complete
- [x] Production deployed

---

## Conclusion

**This roadmap prioritizes user-facing value first**, enabling rapid validation before investing in infrastructure perfection.

**All features are preserved** - nothing is cut, only resequenced for optimal delivery.

**The strategy works because**:
1. Backend is already solid (Weeks 1-3A done)
2. Frontend is critical path to user testing
3. Core value (sequel detection) builds on existing foundation
4. Scale features come after validation

**Next Action**: Start Week 3B (Frontend MVP) immediately.

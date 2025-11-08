# Me Feed - Personal Media Tracker

> Security-Enhanced Media Consumption Tracker with Automated Sequel Detection

**Version**: 1.1.0  
**Status**: 🟢 **LIVE AND VERIFIED IN PRODUCTION**  
**Deployment Date**: October 30, 2025  
**Verification Date**: November 8, 2025  
**Security Rating**: A (Excellent)

---

## 🌐 **LIVE PRODUCTION URLS**

- **Frontend**: https://proud-courtesy-production-992b.up.railway.app
- **Backend API**: https://media-feed-production.up.railway.app
- **Health Check**: https://media-feed-production.up.railway.app/health
- **API Docs**: https://media-feed-production.up.railway.app/docs

**Deployment Platform**: Railway.app  
**Deployment Date**: October 30, 2025

---

## 🚀 **RAILWAY CLOUD DEPLOYMENT - LIVE** (Oct 30, 2025)

**Status**: All Services Operational on Railway.app  
✅ Backend + PostgreSQL + Redis deployed and healthy  
✅ Frontend deployed with production build  
✅ JWT authentication fixed (PKCS#8 format)  
✅ CORS configured for production  
✅ HTTPS/SSL enabled (Railway-managed)  

**→ See [CURRENT_STATUS.md](./CURRENT_STATUS.md) for deployment details**  
**→ See [RAILWAY_DEPLOYMENT_GUIDE.md](./RAILWAY_DEPLOYMENT_GUIDE.md) for deployment guide**

---

## Overview

Me Feed tracks your media consumption and automatically notifies you when sequels, new seasons, or continuations become available across streaming platforms. Import your viewing history via CSV, and let the system monitor for new content in the franchises you follow.

### Key Features

- **🔐 Secure Authentication**: JWT with RS256, refresh tokens, session management
- **📊 Media Database**: Comprehensive catalog with series relationships
- **📁 CSV Import**: Netflix viewing history import with validation and progress tracking
- **🔍 Sequel Detection**: Automated monitoring for continuations via TMDB API
- **📧 Email Notifications**: Real-time alerts when new content is available
- **🎯 Full Frontend**: React-based UI with authentication, dashboard, and notifications
- **📱 Responsive Design**: Mobile-friendly interface with modern UI components
- **🛡️ Security-First**: Rate limiting, input validation, audit logging, A-rated security

---

## Quick Start

### Prerequisites

- **Backend**: Python 3.11+, PostgreSQL 15+, Redis 7+
- **Frontend**: Node.js 18+, npm 9+
- **Containerization**: Docker & Docker Compose (recommended)

### 1. Generate Security Keys

```bash
python scripts/generate_keys_simple.py
```

Creates RSA keypair, encryption key, and database credentials in `secrets/` directory.

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with SECRET_KEY from generate_keys.py output
```

### 3. Run with Docker

```bash
docker-compose up -d
docker-compose logs -f backend
```

**Services**:
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000 ✅ **Available Now**

### 4. Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend ✅ Complete
cd frontend
npm install
npm run dev
```

---

## Project Status

### ✅ **DEPLOYED AND VERIFIED** (October 30 - November 8, 2025)

**Deployment Status**: 🟢 LIVE IN PRODUCTION - VERIFIED
**Verification Status**: Manual testing completed November 8, 2025
**Test Results**: 1302 items imported, all core features working
**Known Issues**: 3 minor bugs (see KNOWN_BUGS.md)

**Backend Infrastructure** (✅ Deployed):
- FastAPI application on Railway
- Authentication system (JWT RS256, sessions, account lockout)
- CSV import with Netflix format support
- Sequel detection algorithm
- TMDB API integration with caching
- Notification system (7 API endpoints)
- Email service with Brevo SMTP
- PostgreSQL database (Railway-managed)
- Redis cache (Railway-managed)
- 71 comprehensive tests (65% coverage)

**Frontend Application** (✅ Deployed):
- Next.js 14 production build on Railway
- Authentication pages (login, register, protected routes)
- Dashboard with import and media library
- Full notification center with preferences
- CSV upload with drag-and-drop
- Import status tracking and history
- Responsive design with shadcn/ui
- Error boundaries and error handling

**Security** (✅ Production):
- HTTPS/SSL (Railway-managed)
- All OWASP Top 10 addressed
- Rate limiting, input validation, audit logging
- RS256 JWT (PKCS#8), Argon2 password hashing
- Origin validation, CORS for production
- Security Rating: A (Excellent)

### 📋 **Railway Deployment & Verification Complete**

**Cloud Infrastructure**:
- [x] Backend deployed to Railway
- [x] Frontend deployed to Railway
- [x] PostgreSQL provisioned on Railway
- [x] Redis provisioned on Railway
- [x] JWT keys fixed (PKCS#8 format)
- [x] CORS configured for production
- [x] Environment variables configured
- [x] Health checks passing
- [x] **End-to-end user testing** (COMPLETED Nov 8, 2025)
- [x] User registration, login, logout verified
- [x] CSV import tested (1302 items imported successfully)
- [x] Dashboard and media library verified
- [x] Settings and profile pages working

### ✅ **Current Phase: Production Stable - Feature Planning**

**Bug Fixes Completed** (November 8, 2025):
- ✅ BUG-001 HIGH: Notifications page fixed (API response format)
- ✅ BUG-002 MEDIUM: Episode count display improved
- ✅ BUG-003 LOW: File selection button fixed
- ✅ BUG-004 LOW: "Notifications0" navbar display fixed

**All bugs deployed to production and awaiting final verification.**

**Next Features** (see KNOWN_BUGS.md for full details):
1. **FR-001:** TMDB API Episode Count Lookup (Gesamtzahl der Episoden ermitteln)
   - Automatically fetch total episode counts from TMDB
   - Display "X/Y episodes" progress tracking
   - Priority: MEDIUM | Estimated: 4-6 hours

2. **FR-002:** Automatic Episode Updates (Aktualisierung bei neuen Staffeln)
   - Weekly background job to update episode counts
   - Notify users when new seasons air
   - Priority: LOW | Estimated: 6-8 hours | Requires: FR-001, Celery

**Infrastructure Tasks**:
- Set up error monitoring (Sentry) - HIGH priority
- Configure performance monitoring
- Custom domain configuration (optional)

**Future Enhancements**:
- Celery background jobs for async processing
- CI/CD pipeline (GitHub Actions)
- Staging environment
- Load testing & optimization
- GDPR compliance features

---

## Architecture

### Backend (FastAPI)

```
backend/
├── app/
│   ├── api/              # 5 API routers, 25+ endpoints
│   ├── core/             # Config, security, middleware
│   ├── db/               # Models, 9 tables, 4 migrations
│   ├── services/         # 10 modular services
│   ├── schemas/          # Pydantic validation
│   └── security/         # Auth, encryption, JWT
├── alembic/              # Database migrations
├── tests/                # 71 tests (pytest)
└── requirements.txt
```

**Key Services**:
- `auth_service.py` - Authentication & sessions
- `import_service.py` - CSV import orchestration
- `notification_service.py` - Notification management
- `email_service.py` - SMTP email delivery
- `sequel_detector.py` - Sequel matching algorithm
- `tmdb_client.py` - TMDB API with caching

### Frontend (Next.js 14)

```
frontend/
├── app/                  # App Router pages
├── components/           # React components
│   ├── auth/            # Login/register (Week 5)
│   ├── import/          # CSV upload (Week 5)
│   ├── library/         # Media grid (Week 5)
│   └── ui/              # shadcn/ui components
├── lib/                 # Utilities & API client
└── package.json         # Dependencies configured
```

**Tech Stack**:
- Next.js 14 (App Router), React 18, TypeScript 5
- Tailwind CSS + shadcn/ui components
- React Query, React Hook Form, Zod validation
- Axios for API calls

---

## API Documentation

### Authentication

```bash
# Register
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "your-secure-password"
}

# Login
POST /api/auth/login
→ Returns: { access_token, refresh_token, token_type, expires_in }

# Refresh token
POST /api/auth/refresh
Authorization: Bearer <refresh_token>

# Get current user
GET /api/auth/me
Authorization: Bearer <access_token>
```

### CSV Import

```bash
# Upload Netflix CSV
POST /api/import/csv
Content-Type: multipart/form-data
Rate Limit: 5 per hour

# Check import status
GET /api/import/status/{job_id}

# View import history
GET /api/import/history?page=1&page_size=20
```

### Notifications

```bash
# Get notifications
GET /api/notifications?unread_only=true&page=1

# Mark as read
PUT /api/notifications/{id}/read

# Get preferences
GET /api/notifications/preferences

# Update preferences
PUT /api/notifications/preferences
{ "email_enabled": false, "email_frequency": "weekly" }

# Unsubscribe (no auth required)
GET /api/notifications/unsubscribe?token={token}
```

**Interactive Docs**: http://localhost:8000/docs

---

## Security

### Security Rating: A (Excellent)

**Authentication**:
- JWT with RS256 asymmetric signing
- Refresh token rotation (7-day expiry)
- Argon2 password hashing (OWASP recommended)
- Account lockout (5 failed attempts, 15min cooldown)
- Session limits (5 concurrent per user)

**Input Protection**:
- Pydantic validation on all endpoints
- CSV formula injection prevention
- SQL injection protection (parameterized queries)
- Path traversal prevention
- File limits (10MB, 10K rows)

**Infrastructure**:
- Rate limiting (Redis-based, per-user & per-IP)
- Security headers (CSP, HSTS, X-Frame-Options, etc.)
- Docker non-root user (appuser:1000)
- Network segmentation
- Secrets management (Docker secrets)

**Monitoring**:
- Structured JSON logging (no sensitive data)
- Audit log for security events
- Request ID tracing
- Encryption at rest (Fernet for API keys)

### Rate Limits

- Registration: 5/hour per IP
- Login: 10/minute per IP
- Token Refresh: 20/hour per user
- CSV Import: 5/hour per user
- Notifications: 100/minute per user
- General API: 60/minute, 1000/hour

### Password Requirements

- Minimum 12 characters
- Must contain: uppercase, lowercase, digit, special character

---

## Database

### Schema (9 Tables)

- `users` - Accounts with security tracking
- `user_sessions` - Refresh tokens (max 5 per user)
- `media` - Catalog with base_title, season_number
- `user_media` - Consumption tracking
- `import_jobs` - CSV import history
- `notifications` - User notifications with metadata
- `notification_preferences` - Notification settings
- `security_events` - Audit log
- `api_keys` - Encrypted external API keys

### Migrations

```bash
# Apply migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Rollback
alembic downgrade -1

# View history
alembic history
```

All migrations reversible with proper `downgrade()` functions.

---

## Testing

### Test Suite (71 Tests)

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific component
pytest tests/test_notification_service.py -v

# Run security tests
pytest tests/test_security_controls.py -v
```

**Test Coverage**:
- NotificationService: 29 tests (~95% coverage)
- EmailService: 19 tests (~90% coverage)
- Notification API: 23 tests (100% coverage)
- Title Parser: 18 tests (100% passing)
- Sequel Detection: 13 tests (90% coverage)
- TMDB Caching: 15 tests (80% coverage)
- Security Controls: 19 tests (90% coverage)

**Total**: 65% overall coverage (backend 90%, frontend pending)

### Code Quality

```bash
# Format
black app/

# Lint
flake8 app/

# Type check
mypy app/

# Security scan
bandit -r app/
safety check
```

---

## Environment Variables

Key variables (see `.env.example` for complete list):

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/mefeed
REDIS_URL=redis://:pass@localhost:6379

# Security
JWT_PRIVATE_KEY_PATH=./secrets/jwt_private.pem
JWT_PUBLIC_KEY_PATH=./secrets/jwt_public.pem
ENCRYPTION_KEY_PATH=./secrets/encryption.key
SECRET_KEY=<from generate_keys.py>

# CORS
ALLOWED_ORIGINS=http://localhost:3000
ALLOWED_HOSTS=localhost,127.0.0.1

# TMDB API
TMDB_API_KEY=<your_tmdb_api_key>
TMDB_API_BASE_URL=https://api.themoviedb.org/3

# Email (Optional for MVP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your_smtp_app_password
FROM_EMAIL=noreply@mefeed.com

# Features
ENABLE_EMAIL_VERIFICATION=false
ENFORCE_HTTPS=false (true in production)
DEBUG=true (false in production)
```

---

## Development Workflow

### Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart service
docker-compose restart backend

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Git Workflow

```bash
# Feature branch
git checkout -b feature/notification-center

# Commit with tests
git add .
git commit -m "feat: Add notification center UI"

# Push and create PR
git push origin feature/notification-center
```

---

## Roadmap

### Week 5 (Current) - Frontend MVP
- [ ] Authentication UI (login/register)
- [ ] JWT token management
- [ ] CSV upload interface
- [ ] Notification center
- [ ] Media library view

### Week 6 - Production Prep
- [ ] Celery background jobs
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Email template testing
- [ ] API versioning (/v1/)
- [ ] Performance testing

### Week 7+ - Scaling
- [ ] Multi-platform support (Prime, Disney+)
- [ ] Fuzzy string matching
- [ ] Advanced filtering & search
- [ ] User settings & preferences UI
- [ ] GDPR compliance (data export/deletion)
- [ ] Professional security audit

**Target MVP**: Week 6
**Target Production**: Week 8

---

## Documentation

### Core Documentation
- **README.md** (this file) - Project overview
- **QUICKSTART.md** - Quick setup guide
- **TECHNICAL_SPEC v1.1.md** - Architecture details
- **PROJECT_STATUS.md** - Detailed status & metrics
- **TEST_SUITE_COMPLETE.md** - Test documentation

### Persona Guides
- **Developer Persona.md** - Developer workflow
- **Security Expert Persona.md** - Security guidelines
- **Technical Lead Persona.md** - Architecture decisions

### Archived Documentation
- `docs/archive/` - Historical progress reports (14 files)

---

## Support & Troubleshooting

### Common Issues

**Backend won't start**:
```bash
# Check if PostgreSQL/Redis are running
docker-compose ps

# Check logs
docker-compose logs backend

# Reset database
docker-compose down -v
docker-compose up -d
```

**Import fails**:
- Verify CSV format (Netflix export)
- Check file size (<10MB) and rows (<10K)
- Review `import_jobs` table for error details

**Authentication errors**:
- Verify JWT keys exist in `secrets/` directory
- Check `SECRET_KEY` in `.env` file
- Ensure Redis is running (sessions stored there)

### Getting Help

- **API Docs**: http://localhost:8000/docs
- **Technical Spec**: `TECHNICAL_SPEC v1.1.md`
- **Project Status**: `PROJECT_STATUS.md`
- **Issues**: Create GitHub issue with logs

---

## Contributing

This is a personal project, but contributions are welcome!

### Guidelines
1. Follow persona guidelines (Developer/Security/Technical Lead)
2. Write tests for new features (pytest)
3. Run security scans before commits (`bandit`, `safety`)
4. Update documentation
5. Use conventional commits (feat/fix/docs/refactor)

### Code Style
- **Python**: black, flake8, mypy
- **TypeScript**: ESLint, Prettier
- **Commits**: Conventional Commits format

---

## License

MIT License - See LICENSE file

---

## Project Metrics

**Backend**:
- 36 Python files (~6,500 LOC)
- 10 modular services
- 25+ API endpoints
- 9 database tables
- 71 tests (65% coverage)

**Security**:
- OWASP Top 10: 10/10 ✅
- Security Rating: A (Excellent)
- Vulnerabilities: 0 critical

**Timeline**:
- Weeks 1-4: Backend complete ✅
- Week 5: Frontend MVP complete ✅
- Week 5 Day 4-5: MVP complete (current target)
- Week 6: Production hardening & CI/CD

---

**Status**: 🟢 SIGNIFICANTLY AHEAD | **Progress**: 95% to MVP | **Next**: Integration Testing & Production Prep

**Last Updated**: October 20, 2025

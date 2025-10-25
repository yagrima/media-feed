# Me Feed v1.1 - Security-Enhanced Technical Specification

## Project Overview

**Name:** Me Feed (Media Feed)
**Version:** 1.2 (MVP-Optimized)
**Purpose:** Personal media consumption tracker with automated update monitoring
**Target Developer:** Junior developer with project lead oversight
**Development Timeline:** 3 weeks to usable MVP, 6 weeks to full feature set
**Strategy:** Frontend-First MVP for rapid user validation  

---

## Security Changes Summary (v1.0 → v1.1)

### Critical Security Additions
1. **Authentication:** JWT with RS256, refresh tokens, session management
2. **Data Protection:** Encryption at rest for sensitive data, secure secrets management
3. **Input Validation:** Enhanced CSV sanitization, SQL injection prevention
4. **Rate Limiting:** Per-user and per-endpoint protection
5. **Audit Logging:** Security event tracking for compliance

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
- **[Security v1.1]** Encrypted API key storage with rotation

### 2. User Media Import
- CSV import for Netflix viewing history with size/content validation
- Manual entry forms with input sanitization
- Simple string matching against database titles
- Store platform-specific IDs in extensible JSON column
- **[Security v1.1]** File upload scanning and quarantine

### 3. Automated Monitoring
- Cross-reference user's consumed media with database
- Identify available sequels/continuations
- Daily checks against existing database (no API calls)
- Track release dates for upcoming content
- **[Security v1.1]** Rate-limited background jobs

### 4. Notifications
- Email alerts when sequels become available
- In-app notification center
- Direct links to media platforms
- **[Security v1.1]** Notification preferences with unsubscribe tokens

---

## Technical Stack

### Backend
- **Framework:** FastAPI (async, built-in validation, automatic OpenAPI)
- **Database:** PostgreSQL 15+ with JSONB support
- **ORM:** SQLAlchemy 2.0 (async support)
- **Job Queue:** Celery + Redis (configurable schedules)
- **API Client:** httpx (async requests to RapidAPI)
- **Security:** PyJWT, passlib, python-jose, cryptography

### Frontend
- **Framework:** Next.js 14 (App Router)
- **UI:** Tailwind CSS + shadcn/ui components
- **State:** TanStack Query (server state management)
- **Forms:** react-hook-form + zod validation
- **Security:** axios with interceptors, secure cookie handling

### Infrastructure
- **Containerization:** Docker + docker-compose with secrets management
- **Environment Config:** python-dotenv / next-config
- **Testing:** pytest (backend), Jest (frontend), security scanning
- **Monitoring:** Structured logging with sensitive data masking

---

## Project Structure

```
me-feed/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # Config, security, middleware
│   │   ├── db/           # Models, migrations
│   │   ├── services/     # Business logic
│   │   ├── workers/      # Celery tasks
│   │   ├── schemas/      # Pydantic models
│   │   └── security/     # Auth, encryption, validation
│   ├── tests/
│   ├── secrets/          # Local development secrets
│   └── requirements.txt
├── frontend/
│   ├── app/              # Next.js app router
│   ├── components/
│   ├── lib/              # API client, utils, security
│   └── package.json
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .gitignore            # Updated for secrets
└── docs/
    ├── API.md
    ├── SECURITY.md
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
    platform_ids JSONB DEFAULT '{}', -- {"netflix": "81234", "tmdb": "456"}
    metadata JSONB DEFAULT '{}', -- {"genres": [], "cast": [], "seasons": 5}
    parent_id UUID REFERENCES media(id), -- for sequels/seasons
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_media_title ON media(title);
CREATE INDEX idx_media_platform_ids ON media USING gin(platform_ids);

-- Enhanced user table with security features
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT false,
    password_hash VARCHAR(255) NOT NULL,
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMP,
    totp_secret VARCHAR(32), -- Optional 2FA
    refresh_token_hash VARCHAR(255),
    last_login_at TIMESTAMP,
    last_login_ip INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

-- User sessions for token management
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_sessions_token ON user_sessions(refresh_token_hash);

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
    next_media_id UUID REFERENCES media(id), -- detected sequel
    notified BOOLEAN DEFAULT false,
    notification_token VARCHAR(255), -- Unsubscribe token
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_monitoring_queue_user_notified ON monitoring_queue(user_id, notified);

-- API key management
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service VARCHAR(50) NOT NULL, -- rapidapi, sendgrid
    key_hash VARCHAR(255) NOT NULL,
    encrypted_key TEXT NOT NULL, -- Encrypted with master key
    last_rotated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Security audit log
CREATE TABLE security_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    event_type VARCHAR(50), -- login_success, login_failed, csv_import, etc
    ip_address INET,
    user_agent TEXT,
    metadata JSONB, -- Additional context
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_security_events_user ON security_events(user_id, created_at);
CREATE INDEX idx_security_events_type ON security_events(event_type, created_at);
```

---

## API Endpoints

### Authentication & Security
```
POST   /api/auth/register       # User registration with email verification
POST   /api/auth/login          # User login (returns access + refresh tokens)
POST   /api/auth/refresh        # Refresh access token
POST   /api/auth/logout         # Invalidate refresh token
POST   /api/auth/verify-email   # Email verification
POST   /api/auth/forgot-password # Password reset request
POST   /api/auth/reset-password  # Password reset confirm
GET    /api/auth/me            # Current user info
GET    /api/auth/sessions       # Active sessions
DELETE /api/auth/sessions/{id}  # Revoke specific session
```

### Media Management
```
GET    /api/media/search?q={query}&type={type}&limit={limit}
GET    /api/media/{id}
POST   /api/media/sync          # Admin only - trigger RapidAPI sync
```

### Import Operations (Rate Limited)
```
POST   /api/import/csv          # Netflix CSV upload (max 10MB, 10k rows)
POST   /api/import/manual       # Single item add
GET    /api/import/status/{job_id}
GET    /api/import/history      # User's import history
```

### User Library
```
GET    /api/user/media          # User's library with filters
POST   /api/user/media/{id}     # Add/update media status
DELETE /api/user/media/{id}     # Remove from library
GET    /api/user/notifications  # Pending notifications
PUT    /api/user/preferences    # Notification preferences
```

### Admin Endpoints
```
GET    /api/admin/audit-log     # Security events
GET    /api/admin/metrics       # System health metrics
POST   /api/admin/rotate-keys   # Rotate API keys
```

---

## Security Implementation

### Authentication Service
```python
# core/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import secrets

class SecurityConfig:
    JWT_ALGORITHM = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    PASSWORD_MIN_LENGTH = 12
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

class AuthService:
    def __init__(self, private_key: str, public_key: str):
        self.private_key = private_key
        self.public_key = public_key
        self.fernet = Fernet(settings.ENCRYPTION_KEY)
    
    def create_access_token(self, user_id: str) -> str:
        expire = datetime.utcnow() + timedelta(minutes=15)
        payload = {
            "sub": user_id,
            "exp": expire,
            "type": "access",
            "jti": secrets.token_urlsafe(16)
        }
        return jwt.encode(payload, self.private_key, algorithm="RS256")
    
    def create_refresh_token(self, user_id: str) -> str:
        expire = datetime.utcnow() + timedelta(days=7)
        payload = {
            "sub": user_id,
            "exp": expire,
            "type": "refresh",
            "jti": secrets.token_urlsafe(32)
        }
        return jwt.encode(payload, self.private_key, algorithm="RS256")
    
    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)
    
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted: str) -> str:
        return self.fernet.decrypt(encrypted.encode()).decode()
```

### Input Validation
```python
# services/validators.py
import re
import magic
from typing import BinaryIO
from fastapi import HTTPException

class CSVValidator:
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_ROWS = 10000
    ALLOWED_MIME = ['text/csv', 'application/csv']
    
    @staticmethod
    def validate_file(file: BinaryIO) -> bool:
        # Check file size
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        
        if size > CSVValidator.MAX_FILE_SIZE:
            raise HTTPException(400, "File too large")
        
        # Verify MIME type
        mime = magic.from_buffer(file.read(2048), mime=True)
        file.seek(0)
        
        if mime not in CSVValidator.ALLOWED_MIME:
            raise HTTPException(400, "Invalid file type")
        
        return True
    
    @staticmethod
    def sanitize_cell(value: str) -> str:
        # Remove formula injections
        if value and value[0] in ['=', '+', '-', '@']:
            value = "'" + value
        
        # Remove potential SQL injection
        value = re.sub(r'[;<>\"\'\\]', '', value)
        
        # Limit length
        return value[:500] if value else ""

# schemas/validation.py
from pydantic import BaseModel, validator, constr, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=12, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain digit')
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', v):
            raise ValueError('Password must contain special character')
        return v

class MediaImport(BaseModel):
    title: constr(max_length=255, regex=r'^[^<>&]*$')
    platform: constr(regex=r'^[a-zA-Z0-9_-]+$')
    consumed_at: str
    
    @validator('title')
    def sanitize_title(cls, v):
        # Additional sanitization
        return v.strip().replace('\x00', '')
```

### Rate Limiting
```python
# core/middleware.py
from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
import redis

redis_client = redis.from_url(settings.REDIS_URL)

def get_rate_limit_key(request: Request) -> str:
    # Use user ID if authenticated, IP otherwise
    user = getattr(request.state, "user", None)
    if user:
        return f"rate_limit:user:{user.id}"
    return f"rate_limit:ip:{get_remote_address(request)}"

limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["60/minute", "1000/hour"]
)

# Specific endpoint limits
@limiter.limit("5/hour")
async def csv_upload_endpoint():
    pass

@limiter.limit("10/minute")
async def login_endpoint():
    pass
```

### Security Headers Middleware
```python
# core/middleware.py
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS.split(",")
)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

@app.middleware("http")
async def audit_logging(request: Request, call_next):
    # Log security-relevant events
    if request.url.path in ["/api/auth/login", "/api/import/csv"]:
        await log_security_event(
            user_id=getattr(request.state, "user_id", None),
            event_type=request.url.path,
            ip_address=get_remote_address(request),
            user_agent=request.headers.get("user-agent")
        )
    
    response = await call_next(request)
    return response
```

---

## Configuration Management

### Environment Variables (.env)
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/mefeed
REDIS_URL=redis://localhost:6379

# Security - CRITICAL
JWT_PRIVATE_KEY_PATH=/run/secrets/jwt_private.pem
JWT_PUBLIC_KEY_PATH=/run/secrets/jwt_public.pem
ENCRYPTION_KEY_PATH=/run/secrets/encryption.key
SECRET_KEY=  # 32+ char random string

# CORS & Hosts
ALLOWED_ORIGINS=http://localhost:3000
ALLOWED_HOSTS=localhost,127.0.0.1

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
LOGIN_RATE_LIMIT=10/minute
IMPORT_RATE_LIMIT=5/hour

# API Keys (Encrypted)
RAPIDAPI_KEY_ENCRYPTED=  # Encrypted with ENCRYPTION_KEY
RAPIDAPI_HOST=your_host_here
API_KEY_ROTATION_DAYS=90

# Job Scheduling
MEDIA_UPDATE_INTERVAL=weekly  # weekly|daily|hourly
MONITORING_SCHEDULE=daily
NOTIFICATION_BATCH_SIZE=50

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD_ENCRYPTED=  # Encrypted

# Session Management
SESSION_TIMEOUT_MINUTES=30
MAX_SESSIONS_PER_USER=5

# Feature Flags
ENABLE_2FA=false
ENABLE_EMAIL_VERIFICATION=true
ENFORCE_HTTPS=true
MATCHING_STRATEGY=exact  # exact|fuzzy|ml
```

### Configuration Class
```python
# core/config.py
from pydantic import BaseSettings, validator
from typing import List
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    REDIS_URL: str
    
    # Security
    JWT_PRIVATE_KEY_PATH: str
    JWT_PUBLIC_KEY_PATH: str
    ENCRYPTION_KEY_PATH: str
    SECRET_KEY: str
    ALLOWED_ORIGINS: str
    ALLOWED_HOSTS: str
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # API Keys
    RAPIDAPI_KEY_ENCRYPTED: str
    
    @property
    def jwt_private_key(self) -> str:
        with open(self.JWT_PRIVATE_KEY_PATH, 'r') as f:
            return f.read()
    
    @property
    def jwt_public_key(self) -> str:
        with open(self.JWT_PUBLIC_KEY_PATH, 'r') as f:
            return f.read()
    
    @property
    def encryption_key(self) -> bytes:
        with open(self.ENCRYPTION_KEY_PATH, 'rb') as f:
            return f.read()
    
    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

---

## Docker Security Configuration

### docker-compose.yml (Development)
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: mefeed
      POSTGRES_USER_FILE: /run/secrets/db_user
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_user
      - db_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - backend-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
  
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    secrets:
      - redis_password
    networks:
      - backend-network
    volumes:
      - redis_data:/data
  
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db/mefeed
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
      JWT_PRIVATE_KEY_PATH: /run/secrets/jwt_private_key
      JWT_PUBLIC_KEY_PATH: /run/secrets/jwt_public_key
      ENCRYPTION_KEY_PATH: /run/secrets/encryption_key
    secrets:
      - jwt_private_key
      - jwt_public_key
      - encryption_key
    ports:
      - "8000:8000"
    networks:
      - backend-network
      - frontend-network
    volumes:
      - ./backend:/app:ro  # Read-only mount
    user: "1000:1000"  # Non-root user
  
  celery:
    build: ./backend
    command: celery -A app.workers worker --loglevel=info
    depends_on:
      - redis
      - db
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db/mefeed
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
    secrets:
      - encryption_key
    networks:
      - backend-network
    user: "1000:1000"
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NODE_ENV: production
    networks:
      - frontend-network
    user: "1000:1000"

secrets:
  db_user:
    file: ./secrets/db_user.txt
  db_password:
    file: ./secrets/db_password.txt
  redis_password:
    file: ./secrets/redis_password.txt
  jwt_private_key:
    file: ./secrets/jwt_private.pem
  jwt_public_key:
    file: ./secrets/jwt_public.pem
  encryption_key:
    file: ./secrets/encryption.key

networks:
  backend-network:
    driver: bridge
    internal: true  # No external access
  frontend-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

### Dockerfile (Backend)
```dockerfile
FROM python:3.11-slim-bookworm

# Security updates
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install dependencies as root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Testing Strategy

### Security Testing
```python
# tests/test_security.py
import pytest
from fastapi.testclient import TestClient

class TestAuthentication:
    def test_jwt_token_expiry(self, client):
        """Test that JWT tokens expire correctly"""
        pass
    
    def test_rate_limiting(self, client):
        """Test rate limiting on login endpoint"""
        for i in range(11):
            response = client.post("/api/auth/login", ...)
        assert response.status_code == 429
    
    def test_sql_injection(self, client):
        """Test SQL injection prevention"""
        malicious = "'; DROP TABLE users; --"
        response = client.get(f"/api/media/search?q={malicious}")
        assert response.status_code == 200
        # Verify tables still exist

class TestCSVUpload:
    def test_file_size_limit(self, client):
        """Test file size validation"""
        large_file = b"x" * (11 * 1024 * 1024)  # 11MB
        response = client.post("/api/import/csv", files={"file": large_file})
        assert response.status_code == 400
    
    def test_csv_formula_injection(self, client):
        """Test CSV formula injection prevention"""
        malicious_csv = "Title,Date\n=1+1,2024-01-01"
        # Verify sanitization

class TestEncryption:
    def test_api_key_encryption(self):
        """Test that API keys are encrypted at rest"""
        # Query database directly
        # Verify no plaintext keys

# tests/test_penetration.py
class TestOWASPTop10:
    """Tests for OWASP Top 10 vulnerabilities"""
    
    def test_broken_authentication(self):
        """A07:2021 – Identification and Authentication Failures"""
        pass
    
    def test_security_misconfiguration(self):
        """A05:2021 – Security Misconfiguration"""
        # Check security headers
        # Verify error messages don't leak info
```

### Performance & Security Monitoring
```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Security metrics
failed_login_attempts = Counter('auth_failed_login_total', 'Failed login attempts')
successful_logins = Counter('auth_successful_login_total', 'Successful logins')
active_sessions = Gauge('auth_active_sessions', 'Active user sessions')
csv_upload_size = Histogram('import_csv_size_bytes', 'CSV upload file sizes')
api_key_rotation = Gauge('security_api_key_age_days', 'Days since API key rotation')

# Performance metrics
request_duration = Histogram('http_request_duration_seconds', 'Request duration')
db_query_duration = Histogram('db_query_duration_seconds', 'Database query duration')
```

---

## Security Checklist

### Pre-Launch Security Requirements
- [ ] All secrets in environment variables or secrets management
- [ ] HTTPS enforced in production
- [ ] Rate limiting tested on all endpoints
- [ ] Input validation on all user inputs
- [ ] SQL injection testing completed
- [ ] XSS prevention verified
- [ ] CSRF tokens implemented
- [ ] Security headers configured
- [ ] Error messages don't leak sensitive info
- [ ] Logging excludes sensitive data
- [ ] API keys encrypted at rest
- [ ] Password policy enforced
- [ ] Session timeout implemented
- [ ] Audit logging functional
- [ ] Docker containers run as non-root
- [ ] Dependencies scanned for vulnerabilities
- [ ] Penetration testing basics completed

### Security Go/No-Go Metrics
- ✓ Zero high/critical vulnerabilities
- ✓ All OWASP Top 10 addressed
- ✓ Security headers score A+ (securityheaders.com)
- ✓ SSL Labs score A+ (production)
- ✓ No secrets in codebase
- ✓ Rate limiting prevents abuse

---

## Implementation Roadmap (MVP-Optimized)

**Strategy**: Build user-facing features first for rapid validation, complete infrastructure later.

### Phase 1: Secure Foundation ✅ COMPLETE (Week 1-2)

#### Sprint 1 - Days 1-2: Secure Environment Setup
- [x] Initialize Git with .gitignore for secrets
- [x] Generate RSA keypair for JWT
- [x] Create encryption keys
- [x] Setup Docker with secrets management
- [x] Configure secure PostgreSQL and Redis

#### Sprint 1 - Days 3-4: Authentication System
- [x] Implement JWT with RS256
- [x] Create refresh token system
- [x] Add password validation
- [x] Setup rate limiting
- [x] Implement audit logging

#### Sprint 1 - Day 5: Database & Security
- [x] Create secure database schema
- [x] Setup encrypted API key storage
- [x] Implement session management
- [x] Add security middleware
- [x] Create security event logging

### Phase 2A: CSV Import Backend ✅ COMPLETE (Week 3 - Part 1)

#### Sprint 2A - Days 1-3: Secure Import Pipeline
- [x] Build CSV validator with size/content checks
- [x] Implement formula injection prevention
- [x] Add import rate limiting
- [x] Netflix CSV parser implementation
- [x] Import job tracking

### Phase 2B: Minimal Viable Frontend 🚧 IN PROGRESS (Week 3)

**PRIORITY: User-facing value delivery**

#### Days 1-2: Core UI Foundation
- [ ] Next.js 14 project setup (App Router)
- [ ] Tailwind CSS + shadcn/ui integration
- [ ] Authentication pages (Login/Register)
- [ ] JWT token management (axios interceptors)
- [ ] Protected route wrapper
- [ ] Responsive layout shell

#### Days 3-4: CSV Import UI
- [ ] File upload component with drag-and-drop
- [ ] Upload progress indicator
- [ ] Import status polling
- [ ] Success/error notifications
- [ ] Import history view

#### Day 5: Library View (Basic)
- [ ] Media grid/list view
- [ ] Basic filtering (all/movies/series)
- [ ] Empty state design
- [ ] Loading states
- [ ] Error handling

**Deliverable**: Functional UI for existing backend features

### Phase 3: Core Value Features (Week 4)

**PRIORITY: Sequel detection and notifications**

#### Days 1-2: Sequel Detection Logic
- [ ] Title parsing service (extract base title from "Show: Season X")
- [ ] Season number extraction
- [ ] Sequel matching algorithm (exact title + season++)
- [ ] Media relationship mapping (parent_id usage)
- [ ] TMDB API integration for metadata enrichment
- [ ] Confidence scoring for matches

#### Days 3-4: Email Notification System
- [ ] SendGrid/SMTP integration
- [ ] Email template design (HTML + text)
- [ ] Notification preferences model
- [ ] Daily digest job (Celery task)
- [ ] Unsubscribe token generation
- [ ] Notification history tracking

#### Day 5: Monitoring Queue UI
- [ ] Notifications center in frontend
- [ ] "X new sequels found" badge
- [ ] Sequel detail view with platform links
- [ ] Mark as read functionality
- [ ] User preference toggles

**Deliverable**: End-to-end sequel notification flow

### Phase 4: Enhanced User Experience (Week 5)

#### Days 1-2: Manual Media Management
- [ ] Add media manually form
- [ ] Search external APIs (TMDB integration)
- [ ] Edit media details
- [ ] Delete from library
- [ ] Bulk actions (select multiple)

#### Days 3-4: Advanced Library Features
- [ ] Search/filter UI
- [ ] Sort options (date added, title, platform)
- [ ] Pagination for large libraries
- [ ] Media detail modal/page
- [ ] Platform badges and icons
- [ ] Watched status tracking

#### Day 5: User Settings & Profile
- [ ] Profile page
- [ ] Email notification preferences
- [ ] Platform preferences (which services to check)
- [ ] Account management (password change)
- [ ] Active sessions view
- [ ] Export data (GDPR compliance)

**Deliverable**: Polished user experience

### Phase 5: Background Processing & Scale (Week 6)

#### Days 1-2: Celery Integration
- [ ] Celery worker configuration
- [ ] Async CSV processing task
- [ ] Progress tracking with Celery signals
- [ ] Retry logic for failed imports
- [ ] Task queue monitoring

#### Days 3-4: Advanced Matching
- [ ] Fuzzy string matching (Levenshtein distance)
- [ ] Alias detection (alternate titles)
- [ ] Year-based disambiguation
- [ ] Machine learning preparation (feature extraction)
- [ ] User feedback loop (correct matches)

#### Day 5: Multi-Platform Support
- [ ] Amazon Prime CSV parser
- [ ] Disney+ CSV parser
- [ ] Generic CSV format support
- [ ] Platform detection logic
- [ ] Platform-specific link generation

**Deliverable**: Production-ready scalability

### Phase 6: Polish & Production Hardening (Week 7+)

#### Security Hardening
- [ ] Docker container user creation (non-root)
- [ ] Environment variable validation
- [ ] Origin header validation middleware
- [ ] Structured logging implementation
- [ ] Dependency vulnerability scanning
- [ ] Penetration testing

#### Performance Optimization
- [ ] Database query optimization
- [ ] Redis caching layer
- [ ] API response compression
- [ ] Frontend code splitting
- [ ] Image optimization
- [ ] CDN integration

#### Monitoring & Observability
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Error tracking (Sentry)
- [ ] Uptime monitoring
- [ ] Log aggregation (ELK stack)
- [ ] Alerting rules

**Deliverable**: Production-ready deployment
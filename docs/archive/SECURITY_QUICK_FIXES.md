# Security Quick Fixes - Implementation Guide

**Priority**: High (Before MVP Launch)
**Estimated Time**: 1.5-2 developer days ⬇️ *reduced from 2-3 days*
**Based on**: SECURITY_AUDIT.md (October 19, 2025 - Updated)
**Progress**: 1 of 5 fixes complete ✅

---

## ✅ Fix 0: Docker User Creation - **COMPLETE**

**Risk**: ~~HIGH~~ → **RESOLVED**
**File**: `backend/Dockerfile`
**Status**: ✅ **ALREADY IMPLEMENTED**

The backend/Dockerfile (lines 14-29) correctly implements:
- Non-root user `appuser` (UID 1000)
- Proper file ownership (`--chown=appuser:appuser`)
- USER directive switches to non-root before runtime

**No action needed** - This fix is complete.

---

## Fix 1: Environment Variable Validation

**Risk**: HIGH - Hardcoded/default passwords in production
**File**: `backend/app/core/config.py`
**Time**: 30 minutes
**Status**: ⚠️ **PARTIALLY COMPLETE** (SECRET_KEY done, DB/Redis pending)

### Implementation

**Current implementation** (config.py:80-85):
```python
# ✅ ALREADY EXISTS
@validator('SECRET_KEY')
def validate_secret_key(cls, v):
    """Ensure SECRET_KEY is sufficiently long"""
    if len(v) < 32:
        raise ValueError('SECRET_KEY must be at least 32 characters')
    return v
```

**Add these additional validators** after line 85:

```python
@validator('DATABASE_URL')
def validate_database_url(cls, v):
    """Ensure production database password is not a placeholder"""
    if 'CHANGE_THIS_PASSWORD' in v or 'localhost' in v:
        if not cls.DEBUG:
            raise ValueError(
                'Production database configuration required. '
                'DATABASE_URL contains placeholder or localhost.'
            )
    return v

@validator('REDIS_URL')
def validate_redis_url(cls, v):
    """Ensure production Redis password is not a placeholder"""
    if 'CHANGE_THIS_PASSWORD' in v or 'localhost' in v:
        if not cls.DEBUG:
            raise ValueError(
                'Production Redis configuration required. '
                'REDIS_URL contains placeholder or localhost.'
            )
    return v

@validator('SMTP_PASSWORD')
def validate_smtp_password(cls, v):
    """Warn if email password is placeholder"""
    if v and ('your_' in v or 'CHANGE' in v):
        import warnings
        warnings.warn('SMTP_PASSWORD appears to be a placeholder')
    return v
```

### Testing
```bash
# Should fail with DEBUG=false
DATABASE_URL=postgresql://user:CHANGE_THIS_PASSWORD@localhost/db DEBUG=false python -c "from app.core.config import settings"

# Should succeed with DEBUG=true
DATABASE_URL=postgresql://user:CHANGE_THIS_PASSWORD@localhost/db DEBUG=true python -c "from app.core.config import settings"
```

---

## Fix 2: Docker Security Hardening (Additional)

**Risk**: MEDIUM - Missing security constraints
**Files**: `docker-compose.yml`
**Time**: 15 minutes
**Status**: ⚠️ **OPTIONAL ENHANCEMENT**

**Note**: The critical Docker user fix is already complete. This adds defense-in-depth.

### Frontend Dockerfile

Create `frontend/Dockerfile`:

```dockerfile
FROM node:18-alpine

# Security: Create non-root user
RUN addgroup -g 1000 mefeed && \
    adduser -u 1000 -G mefeed -s /bin/sh -D mefeed

WORKDIR /app

# Install dependencies as root
COPY package*.json ./
RUN npm ci --production

# Copy application code
COPY --chown=mefeed:mefeed . .

# Build application
RUN npm run build

# Switch to non-root user
USER mefeed

EXPOSE 3000

CMD ["npm", "start"]
```

### Additional Hardening in docker-compose.yml

Add security constraints to backend service:

```yaml
backend:
  # ... existing config ...
  security_opt:
    - no-new-privileges:true
  cap_drop:
    - ALL
  cap_add:
    - NET_BIND_SERVICE  # Only if binding to port <1024
```

### Verification
```bash
# Verify user is non-root
docker-compose run --rm backend whoami
# Expected output: appuser

# Verify cannot escalate privileges
docker-compose run --rm backend id
# Expected: uid=1000(appuser) gid=1000(appuser)
```

---

## Fix 3: Origin Header Validation

**Risk**: MEDIUM - Missing CSRF protection
**File**: `backend/app/core/middleware.py`
**Time**: 30 minutes

### Implementation

Add new middleware function:

```python
async def origin_validation_middleware(request: Request, call_next: Callable):
    """
    Validate Origin/Referer headers for state-changing requests

    Mitigates CSRF attacks when JWT tokens could be leaked to malicious sites

    Args:
        request: FastAPI request
        call_next: Next middleware in chain

    Returns:
        Response or 403 if invalid origin
    """
    # Only validate state-changing methods
    if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
        origin = request.headers.get('origin')
        referer = request.headers.get('referer')

        # Check if origin or referer is present
        header_value = origin or referer

        if header_value:
            # Validate against allowed origins
            is_valid = any(
                header_value.startswith(allowed_origin)
                for allowed_origin in settings.allowed_origins_list
            )

            if not is_valid:
                # Log security event
                from app.services.auth_service import AuthService
                from app.db.base import get_db

                # Note: This is async, may need adjustment based on your setup
                # Consider logging to file/stdout instead for middleware
                print(f"SECURITY: Invalid origin blocked: {header_value} from {request.client.host if request.client else 'unknown'}")

                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Invalid request origin"}
                )

    return await call_next(request)
```

### Register Middleware

In `backend/app/main.py`, add after other middleware:

```python
from app.core.middleware import (
    security_headers_middleware,
    audit_logging_middleware,
    request_id_middleware,
    origin_validation_middleware  # Add this
)

# Add middleware (order matters - LIFO execution)
app.middleware("http")(origin_validation_middleware)  # Add this line
app.middleware("http")(security_headers_middleware)
app.middleware("http")(audit_logging_middleware)
app.middleware("http")(request_id_middleware)
```

### Testing

```bash
# Valid origin - should succeed
curl -X POST http://localhost:8000/api/auth/login \
  -H "Origin: http://localhost:3000" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'

# Invalid origin - should fail with 403
curl -X POST http://localhost:8000/api/auth/login \
  -H "Origin: http://evil.com" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'
```

---

## Fix 4: Structured Logging

**Risk**: MEDIUM - print() statements leak sensitive data
**Files**: Multiple files using print()
**Time**: 2 hours

### Step 1: Add logging dependency

Update `backend/requirements.txt`:

```
# Add after existing utilities
python-json-logger==2.0.7
```

### Step 2: Create logging configuration

Create `backend/app/core/logging_config.py`:

```python
"""
Structured logging configuration with sensitive data filtering
"""
import logging
import sys
from pythonjsonlogger import jsonlogger

class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive information from logs"""

    SENSITIVE_KEYS = [
        'password', 'token', 'secret', 'api_key', 'apikey',
        'authorization', 'auth', 'jwt', 'session_id',
        'ssn', 'credit_card', 'cvv'
    ]

    def filter(self, record):
        """Redact sensitive data from log record"""
        if hasattr(record, 'args') and record.args:
            # Redact args
            if isinstance(record.args, dict):
                record.args = self._redact_dict(record.args)

        # Redact message
        if hasattr(record, 'msg'):
            for key in self.SENSITIVE_KEYS:
                if key in str(record.msg).lower():
                    record.msg = record.msg.replace(str(key), f"{key}=***REDACTED***")

        return True

    def _redact_dict(self, data: dict) -> dict:
        """Recursively redact sensitive keys from dictionary"""
        redacted = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = self._redact_dict(value)
            else:
                redacted[key] = value
        return redacted


def setup_logging():
    """Configure structured JSON logging"""

    # Create JSON formatter
    json_formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s %(pathname)s %(lineno)d',
        rename_fields={
            'levelname': 'level',
            'asctime': 'timestamp',
            'name': 'logger'
        },
        timestamp=True
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(json_formatter)
    console_handler.addFilter(SensitiveDataFilter())

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

    return root_logger


# Create global logger instance
logger = setup_logging()
```

### Step 3: Replace print() statements

In `backend/app/services/import_service.py` and similar files:

```python
# OLD
print(f"Processing row {i}: {row}")

# NEW
import logging
logger = logging.getLogger(__name__)

logger.info("Processing CSV row", extra={
    "row_number": i,
    "user_id": user_id,
    "import_job_id": str(job.id)
})
```

### Step 4: Initialize in main.py

In `backend/app/main.py`:

```python
from app.core.logging_config import setup_logging
import logging

# Setup logging before anything else
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME)

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting", extra={
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG
    })
```

### Testing

```python
# Test sensitive data filtering
import logging
logger = logging.getLogger(__name__)

# This should be redacted
logger.info("User login", extra={
    "email": "user@example.com",
    "password": "secret123"  # Will be redacted
})

# Output should show: {"password": "***REDACTED***"}
```

---

## Fix 5: Dependency Updates

**Risk**: MEDIUM - Known vulnerabilities in outdated packages
**File**: `backend/requirements.txt`
**Time**: 1 hour + testing

### Updated requirements.txt

```
# Web Framework
fastapi==0.115.0  # Updated from 0.104.1
uvicorn[standard]==0.31.0  # Updated from 0.24.0
pydantic==2.9.2  # Updated from 2.5.0
pydantic-settings==2.6.0  # Updated from 2.1.0

# Database
sqlalchemy==2.0.36  # Updated from 2.0.23
asyncpg==0.29.0
alembic==1.13.3  # Updated from 1.12.1
psycopg2-binary==2.9.10  # Updated from 2.9.9

# Security
python-jose[cryptography]==3.3.0
passlib[argon2]==1.7.4
python-multipart==0.0.12  # Updated from 0.0.6
cryptography==43.0.3  # Updated from 41.0.7 - CRITICAL UPDATE
argon2-cffi==23.1.0

# Authentication
PyJWT==2.9.0  # Updated from 2.8.0

# Rate Limiting
slowapi==0.1.9
redis==5.2.0  # Updated from 5.0.1

# Background Jobs
celery==5.4.0  # Updated from 5.3.4

# HTTP Client
httpx==0.27.2  # Updated from 0.25.2

# Email
python-dotenv==1.0.1  # Updated from 1.0.0
aiosmtplib==3.0.2  # Updated from 3.0.1
email-validator==2.2.0  # Updated from 2.1.0

# CSV Processing
pandas==2.2.3  # Updated from 2.1.4
python-magic==0.4.27

# Logging
python-json-logger==2.0.7  # NEW

# Utilities
python-dateutil==2.9.0  # Updated from 2.8.2

# Testing
pytest==8.3.3  # Updated from 7.4.3
pytest-asyncio==0.24.0  # Updated from 0.21.1
pytest-cov==6.0.0  # Updated from 4.1.0

# Security Testing
bandit==1.7.10  # Updated from 1.7.5
safety==3.2.8  # NEW - for vulnerability scanning

# Code Quality
black==24.10.0  # Updated from 23.12.0
flake8==7.1.1  # Updated from 6.1.0
mypy==1.13.0  # Updated from 1.7.1
```

### Migration Steps

```bash
# Backup current environment
cd backend
pip freeze > requirements.old.txt

# Update packages
pip install -r requirements.txt --upgrade

# Run tests to verify compatibility
pytest

# Check for breaking changes
python -c "from app.main import app; print('Import successful')"

# Start server and verify
uvicorn app.main:app --reload
```

### Breaking Changes to Watch

1. **FastAPI 0.115.0**: Check if any route decorators need updates
2. **Pydantic 2.9**: Validate that all model validations still work
3. **SQLAlchemy 2.0.36**: Verify async query syntax
4. **Cryptography 43.x**: Critical security fixes - test JWT signing/verification

### Rollback Plan

If issues occur:
```bash
pip install -r requirements.old.txt
```

---

## Verification Checklist

After implementing all fixes:

### Security
- [ ] Application fails to start with `DATABASE_URL=...CHANGE_THIS_PASSWORD` and `DEBUG=false`
- [ ] Docker containers run as user `mefeed` (UID 1000)
- [ ] POST requests with invalid Origin header return 403
- [ ] Logs output JSON format with timestamps
- [ ] Sensitive fields (password, token) are redacted in logs
- [ ] All dependencies updated to latest secure versions

### Functionality
- [ ] Authentication flow works (register, login, logout)
- [ ] CSV import still functions correctly
- [ ] Rate limiting still enforced
- [ ] Database connections successful
- [ ] All tests pass

### Performance
- [ ] No significant performance degradation
- [ ] Logging doesn't cause slowdown
- [ ] Docker image sizes reasonable

---

## Deployment Checklist

Before deploying to production:

1. **Environment Configuration**
   ```bash
   # Verify no placeholder passwords
   grep -i "CHANGE_THIS" .env && echo "ERROR: Placeholder passwords found!"

   # Verify DEBUG is false
   grep "DEBUG=false" .env || echo "ERROR: DEBUG should be false in production"
   ```

2. **Docker Build**
   ```bash
   # Build with security scanner
   docker-compose build
   docker scan mefeed_backend:latest
   docker scan mefeed_frontend:latest
   ```

3. **Security Scan**
   ```bash
   # Dependency scan
   cd backend
   safety check --file requirements.txt

   # Code scan
   bandit -r app/ -ll
   ```

4. **Smoke Test**
   ```bash
   # Start services
   docker-compose up -d

   # Health check
   curl http://localhost:8000/health

   # Test authentication
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"SecurePass123!"}'
   ```

---

## Timeline

| Fix | Time | Priority | Status |
|-----|------|----------|--------|
| ~~Docker User Creation~~ | ~~1 hour~~ | ~~Critical~~ | ✅ Complete |
| Environment Validation | 30 min | High | ⚠️ Partial (50%) |
| Origin Validation | 30 min | High | ❌ Not started |
| Structured Logging | 2 hours | High | ❌ Not started |
| Dependency Updates | 1 hour | High | ❌ Not started |
| Docker Hardening | 15 min | Medium | ❌ Optional |
| Testing & Verification | 1.5 hours | Critical | ❌ Pending |
| **TOTAL** | **5.5 hours** ⬇️ | | **20% Complete** |

**Recommended Approach**: Implement remaining fixes in order listed, test after each fix.

---

## Support & Resources

- Full audit report: `SECURITY_AUDIT.md`
- Docker security: https://docs.docker.com/engine/security/
- FastAPI security: https://fastapi.tiangolo.com/tutorial/security/
- OWASP Top 10: https://owasp.org/www-project-top-ten/

**Questions?** Review the Security Expert Persona document for guidance.

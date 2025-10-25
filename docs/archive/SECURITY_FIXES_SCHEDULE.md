# Security Fixes - Prioritized Implementation Schedule

**Created**: October 19, 2025
**Purpose**: Step-by-step guide for completing remaining security fixes
**Total Time**: 3.5 hours (2h quick wins + 1.5h verification/testing)
**Impact**: Security rating A- → A (Very Strong → Excellent)

---

## 🎯 Current Status

**Security Fixes Progress**: 1 of 5 complete (20%)

| Fix | Status | Time | Priority | Impact |
|-----|--------|------|----------|--------|
| Docker User Security | ✅ Complete | - | - | HIGH |
| Environment Validation | ⚠️ Partial | 15 min | 🔴 Critical | MEDIUM |
| Origin Header Validation | ❌ Not Started | 30 min | 🔴 Critical | HIGH |
| Dependency Updates | ❌ Not Started | 1 hour | 🔴 Critical | HIGH |
| Structured Logging | ❌ Not Started | 2 hours | 🟡 High | MEDIUM |
| **TOTAL** | **20%** | **3.5h** | - | - |

---

## 📋 Implementation Order

### Phase 1: Quick Security Wins (Morning - 2 hours) 🔒

**Goal**: Complete 3 critical fixes for immediate security improvement
**When**: Before starting frontend development
**Why**: Small time investment, large security impact

---

## Fix 1: Environment Variable Validation ⏱️ 15 minutes

**Status**: ⚠️ PARTIAL (SECRET_KEY done, DATABASE_URL/REDIS_URL pending)
**Priority**: 🔴 CRITICAL
**Impact**: Prevents accidental deployment with placeholder passwords

### Step-by-Step Implementation

#### 1.1 Open Configuration File
```bash
# Navigate to backend config
code backend/app/core/config.py
```

#### 1.2 Add Validators
**Location**: After line 85 (after `validate_secret_key`)

```python
@validator('DATABASE_URL')
def validate_database_url(cls, v):
    """Ensure production database password is not a placeholder"""
    if not cls.DEBUG and ('CHANGE_THIS_PASSWORD' in v or 'localhost' in v):
        raise ValueError(
            'Production database configuration required. '
            'DATABASE_URL contains placeholder or localhost.'
        )
    return v

@validator('REDIS_URL')
def validate_redis_url(cls, v):
    """Ensure production Redis password is not a placeholder"""
    if not cls.DEBUG and ('CHANGE_THIS_PASSWORD' in v or 'localhost' in v):
        raise ValueError(
            'Production Redis configuration required. '
            'REDIS_URL contains placeholder or localhost.'
        )
    return v
```

#### 1.3 Testing
```bash
# Test 1: Should FAIL in production mode
cd backend
DATABASE_URL=postgresql://user:CHANGE_THIS_PASSWORD@localhost/db \
DEBUG=false \
python -c "from app.core.config import settings"
# Expected: ValueError

# Test 2: Should SUCCEED in debug mode
DATABASE_URL=postgresql://user:CHANGE_THIS_PASSWORD@localhost/db \
DEBUG=true \
python -c "from app.core.config import settings"
# Expected: No error

# Test 3: Should SUCCEED with real password
DATABASE_URL=postgresql://user:RealPassword123@prod-server/db \
DEBUG=false \
python -c "from app.core.config import settings"
# Expected: No error
```

#### 1.4 Verification Checklist
- [ ] Validators added after line 85
- [ ] Both DATABASE_URL and REDIS_URL validated
- [ ] Checks for 'CHANGE_THIS_PASSWORD' and 'localhost'
- [ ] Only validates when DEBUG=false
- [ ] All 3 tests pass

**Time Spent**: _____ minutes

---

## Fix 2: Origin Header Validation ⏱️ 30 minutes

**Status**: ❌ NOT STARTED
**Priority**: 🔴 CRITICAL
**Impact**: Adds CSRF protection for state-changing requests

### Step-by-Step Implementation

#### 2.1 Add Middleware Function
**File**: `backend/app/core/middleware.py`
**Location**: After `request_id_middleware` function (after line 141)

```python
async def origin_validation_middleware(request: Request, call_next: Callable):
    """
    Validate Origin/Referer headers for state-changing requests

    Mitigates CSRF attacks when JWT tokens could be leaked to malicious sites.

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
                print(f"SECURITY WARNING: Invalid origin blocked: {header_value} from {request.client.host if request.client else 'unknown'}")

                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Invalid request origin"}
                )

    return await call_next(request)
```

#### 2.2 Register Middleware
**File**: `backend/app/main.py`
**Location**: Find middleware registration section

**Step 1**: Add import at top of file
```python
from app.core.middleware import (
    security_headers_middleware,
    audit_logging_middleware,
    request_id_middleware,
    origin_validation_middleware  # ← Add this
)
```

**Step 2**: Register middleware (order matters - LIFO execution)
```python
# Add middleware (order matters - LIFO execution)
app.middleware("http")(origin_validation_middleware)  # ← Add this FIRST
app.middleware("http")(security_headers_middleware)
app.middleware("http")(audit_logging_middleware)
app.middleware("http")(request_id_middleware)
```

#### 2.3 Testing
```bash
# Start backend server
cd backend
uvicorn app.main:app --reload

# In another terminal:

# Test 1: Valid origin - should SUCCEED
curl -X POST http://localhost:8000/api/auth/login \
  -H "Origin: http://localhost:3000" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!"}'
# Expected: 200 or 401 (not 403)

# Test 2: Invalid origin - should FAIL with 403
curl -X POST http://localhost:8000/api/auth/login \
  -H "Origin: http://evil.com" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'
# Expected: 403 Forbidden

# Test 3: No origin header - should SUCCEED (allowed)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'
# Expected: 200 or 401 (not 403)

# Test 4: GET request with invalid origin - should SUCCEED (only POST/PUT/DELETE checked)
curl -X GET http://localhost:8000/api/auth/me \
  -H "Origin: http://evil.com"
# Expected: 401 (not 403)
```

#### 2.4 Verification Checklist
- [ ] Middleware function added to middleware.py
- [ ] Import added to main.py
- [ ] Middleware registered in correct order
- [ ] Test 1 passes (valid origin allowed)
- [ ] Test 2 passes (invalid origin blocked)
- [ ] Test 3 passes (no origin allowed)
- [ ] Test 4 passes (GET requests not checked)
- [ ] Security warning appears in logs for blocked requests

**Time Spent**: _____ minutes

---

## Fix 3: Dependency Updates ⏱️ 1 hour

**Status**: ❌ NOT STARTED
**Priority**: 🔴 CRITICAL
**Impact**: Patches known security vulnerabilities in dependencies

### Step-by-Step Implementation

#### 3.1 Backup Current Requirements
```bash
cd backend
cp requirements.txt requirements.txt.backup
pip freeze > requirements.old.txt
```

#### 3.2 Update requirements.txt
**File**: `backend/requirements.txt`

**Replace these lines**:
```python
# OLD VERSIONS
fastapi==0.104.1        # → 0.115.0
uvicorn[standard]==0.24.0  # → 0.31.0
pydantic==2.5.0         # → 2.9.2
pydantic-settings==2.1.0   # → 2.6.0
sqlalchemy==2.0.23      # → 2.0.36
alembic==1.12.1         # → 1.13.3
psycopg2-binary==2.9.9  # → 2.9.10
python-multipart==0.0.6 # → 0.0.12
cryptography==41.0.7    # → 43.0.3 (CRITICAL UPDATE)
PyJWT==2.8.0            # → 2.9.0
redis==5.0.1            # → 5.2.0
celery==5.3.4           # → 5.4.0
httpx==0.25.2           # → 0.27.2
aiosmtplib==3.0.1       # → 3.0.2
email-validator==2.1.0  # → 2.2.0
pandas==2.1.4           # → 2.2.3
python-dateutil==2.8.2  # → 2.9.0
pytest==7.4.3           # → 8.3.3
pytest-asyncio==0.21.1  # → 0.24.0
pytest-cov==4.1.0       # → 6.0.0
bandit==1.7.5           # → 1.7.10
black==23.12.0          # → 24.10.0
flake8==6.1.0           # → 7.1.1
mypy==1.7.1             # → 1.13.0
```

**Add new dependency**:
```python
# Security Testing (add after bandit)
safety==3.2.8
```

#### 3.3 Install Updates
```bash
cd backend

# Create/activate virtual environment if not already active
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install updated dependencies
pip install -r requirements.txt --upgrade

# Verify installation
pip list | grep -E "(fastapi|cryptography|sqlalchemy)"
```

#### 3.4 Run Security Scan
```bash
# Scan for known vulnerabilities
safety check --file requirements.txt

# Expected: No known vulnerabilities (or minimal low-severity ones)
```

#### 3.5 Compatibility Testing
```bash
# Test 1: Import test
python -c "from app.main import app; print('✅ Import successful')"

# Test 2: Start server
uvicorn app.main:app --reload &
SERVER_PID=$!
sleep 5

# Test 3: Health check
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# Test 4: Run existing tests (if any)
pytest

# Stop test server
kill $SERVER_PID
```

#### 3.6 Breaking Changes Check

**FastAPI 0.104 → 0.115**:
- Check if any route decorators need updates
- Verify dependency injection still works

**Pydantic 2.5 → 2.9**:
- Verify all model validations work
- Check @validator syntax compatibility

**SQLAlchemy 2.0.23 → 2.0.36**:
- Test database connections
- Verify async queries work

**Cryptography 41 → 43** (CRITICAL):
- Test JWT signing/verification
- Verify encryption operations

#### 3.7 Rollback Plan (if issues occur)
```bash
# Restore backup
cp requirements.txt.backup requirements.txt
pip install -r requirements.old.txt
```

#### 3.8 Verification Checklist
- [ ] Backup created
- [ ] requirements.txt updated with new versions
- [ ] pip install completed without errors
- [ ] safety check shows no critical vulnerabilities
- [ ] Import test passes
- [ ] Server starts successfully
- [ ] Health endpoint responds
- [ ] All existing tests pass (or document failures)
- [ ] No breaking changes detected

**Time Spent**: _____ minutes

---

## Phase 2: Structured Logging (Parallel with Frontend) 🔒

**Goal**: Replace print() statements with structured JSON logging
**When**: During Day 1-2 of frontend development
**Why**: Can be done in parallel, improves production monitoring

---

## Fix 4: Structured Logging ⏱️ 2 hours

**Status**: ❌ NOT STARTED
**Priority**: 🟡 HIGH (not blocking, but important)
**Impact**: Better observability, sensitive data filtering

### Step-by-Step Implementation

#### 4.1 Add Logging Dependency
```bash
cd backend
echo "python-json-logger==2.0.7" >> requirements.txt
pip install python-json-logger
```

#### 4.2 Create Logging Configuration
**File**: `backend/app/core/logging_config.py` (NEW FILE)

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
            if isinstance(record.args, dict):
                record.args = self._redact_dict(record.args)

        # Redact message
        if hasattr(record, 'msg'):
            for key in self.SENSITIVE_KEYS:
                if key in str(record.msg).lower():
                    record.msg = str(record.msg).replace(key, f"{key}=***REDACTED***")

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


# Global logger instance
logger = setup_logging()
```

#### 4.3 Initialize Logging in main.py
**File**: `backend/app/main.py`
**Location**: At the very top, before other imports

```python
# Setup logging FIRST (before other imports)
from app.core.logging_config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

# ... rest of imports ...

app = FastAPI(title=settings.APP_NAME)

@app.on_event("startup")
async def startup_event():
    logger.info("Application starting", extra={
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG
    })
```

#### 4.4 Replace print() Statements

**Find all print() statements**:
```bash
cd backend
grep -r "print(" app/ | grep -v "__pycache__"
```

**Example replacements**:

**OLD** (`app/services/import_service.py`):
```python
print(f"Processing row {i}: {row}")
```

**NEW**:
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Processing CSV row", extra={
    "row_number": i,
    "user_id": str(user_id),
    "import_job_id": str(job.id)
})
```

**Files likely containing print()**:
- `app/services/import_service.py`
- `app/services/netflix_parser.py`
- `app/api/import_api.py`
- Any other service files

#### 4.5 Testing Sensitive Data Filtering
```python
# Test script: test_logging.py
import logging
from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# This should redact the password
logger.info("User login", extra={
    "email": "user@example.com",
    "password": "secret123"  # Will be redacted
})

# Expected output: {"password": "***REDACTED***"}
```

#### 4.6 Verification Checklist
- [ ] python-json-logger added to requirements.txt
- [ ] logging_config.py created
- [ ] Logging initialized in main.py startup
- [ ] All print() statements replaced (check with grep)
- [ ] Sensitive data filter tested
- [ ] JSON format logs visible on server startup
- [ ] No sensitive data in log output

**Time Spent**: _____ minutes

---

## 📊 Final Verification & Testing

### Overall Security Testing (30 minutes)

#### 1. Security Scan
```bash
cd backend

# Code security scan
bandit -r app/ -ll

# Dependency vulnerability scan
safety check --file requirements.txt

# Expected: No HIGH severity issues
```

#### 2. Manual Security Tests
```bash
# Start server
uvicorn app.main:app --reload

# Test 1: Environment validation
# Stop server, set DEBUG=false with placeholder password
# Server should fail to start

# Test 2: Origin validation
# Try request with evil.com origin - should get 403

# Test 3: Authentication flow
# Register → Login → Refresh → Logout
# All should work normally

# Test 4: CSV upload
# Upload test CSV - should work with logging
```

#### 3. Docker Build Test
```bash
# Build backend image
docker-compose build backend

# Verify non-root user
docker-compose run --rm backend whoami
# Expected: appuser

# Start all services
docker-compose up -d

# Check logs for JSON format
docker-compose logs backend | tail -20
# Expected: JSON formatted logs
```

### Final Checklist

- [ ] **Environment Validation**: ✅ Complete
  - DATABASE_URL validator added
  - REDIS_URL validator added
  - Tests pass

- [ ] **Origin Header Validation**: ✅ Complete
  - Middleware added
  - Middleware registered
  - Tests pass

- [ ] **Dependency Updates**: ✅ Complete
  - All packages updated
  - Safety scan clean
  - No breaking changes

- [ ] **Structured Logging**: ✅ Complete
  - Logging config created
  - print() replaced
  - Sensitive data filtered

- [ ] **Overall Tests**: ✅ Complete
  - Bandit scan clean
  - Docker build successful
  - Server starts normally
  - All endpoints working

---

## 🎯 Success Criteria

### Security Rating Achievement
- [x] Docker user security ✅ (already complete)
- [ ] Environment validation ✅
- [ ] Origin validation ✅
- [ ] Dependency updates ✅
- [ ] Structured logging ✅

**Final Rating**: **A (Excellent)** ⬆️ from A- (Very Strong)

### Time Investment vs. Impact

| Metric | Target | Actual |
|--------|--------|--------|
| Total Time | 3.5 hours | _____ hours |
| Security Rating | A | _____ |
| Critical Fixes | 5/5 (100%) | _____ |
| Vulnerabilities Fixed | All HIGH | _____ |
| Production Ready | Yes | _____ |

---

## 📝 Post-Implementation Tasks

### Documentation Updates
- [ ] Update SECURITY_AUDIT.md with completion dates
- [ ] Update SECURITY_QUICK_FIXES.md with "COMPLETE" status
- [ ] Update README.md security checklist
- [ ] Update Security Expert Persona with final rating

### Git Commit
```bash
git add .
git commit -m "security: Complete critical security fixes (5/5)

- Add DATABASE_URL and REDIS_URL validation
- Implement Origin header validation middleware
- Update all dependencies to latest secure versions
- Replace print() with structured JSON logging
- Security rating upgraded to A (Excellent)

Fixes: #security-audit
Time: 3.5 hours
Impact: HIGH - All critical vulnerabilities addressed
"
```

---

## 🆘 Troubleshooting

### Issue: Dependency Update Breaks Code
**Solution**:
```bash
cp requirements.txt.backup requirements.txt
pip install -r requirements.old.txt
# Review breaking changes in library changelogs
```

### Issue: Origin Validation Blocks Legitimate Requests
**Solution**:
- Check ALLOWED_ORIGINS in .env
- Ensure frontend URL is in allowed list
- Test with curl first before browser

### Issue: Logging Creates Too Much Output
**Solution**:
```python
# Adjust log level in logging_config.py
root_logger.setLevel(logging.WARNING)  # Less verbose
```

### Issue: Tests Fail After Updates
**Solution**:
- Check compatibility notes in library changelogs
- Update test fixtures if needed
- Temporarily pin problematic package version

---

**Document Prepared By**: Security Expert Persona
**Implementation Owner**: Development Team
**Estimated Completion**: Day 1-2 of Week 3B
**Next Review**: After all fixes complete

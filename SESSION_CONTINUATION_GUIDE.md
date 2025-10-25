# Session Continuation Guide - Me Feed

## 🚨 Current Issues (2025-10-22)

### Issue A: Pending Upload Stuck
**Problem:** Old CSV upload is still pending, blocking new uploads

**Root Cause:** 
- Background job processing may be stuck or failed
- Database has job records but no cleanup
- Redis may have stale job status

**Files to Check:**
- `backend/app/services/import_service.py` - Job processing logic
- `backend/app/db/models.py` - ImportJob model status handling
- Redis keys: `import_job:*`, `job:job_id:*`

**Fixes Needed:**
1. Clear stuck job records from database
2. Clear Redis job cache
3. Add job timeout/cleanup logic
4. Implement job retry mechanism

---

### Issue B: 403 Forbidden on CSV Upload
**Problem:** Server responds with 403 Forbidden when uploading CSV

**Root Cause:**
- Missing authentication token in upload request
-_TOKEN MANAGER_ variables not available in browser
- CORS middleware blocking unauthorized requests

**Files to Check:**
- `frontend/lib/auth/token-manager.ts` - Token storage/retrieval
- `frontend/lib/api/import.ts` - API client auth headers
- User login/session state

**Fixes Needed:**
1. Verify token storage mechanism
2. Add refresh token rotation
3. Fix API client authentication headers
4. Add authentication state validation

---

### Issue C: Failed to fetch unread count (Expected)
**Problem:** Console shows 403 Forbidden error on unread count query

**Root Cause:**
- No valid authentication token
- Endpoint requires valid JWT token
- User not properly authenticated

**Temporary Fix Applied:**
- Added fallback return 0 for failed requests
- Added error handling with try-catch

**Ultimate Fix Needed:**
1. Verify user authentication flow
2. Ensure token persistence across browser sessions
3. Add login state management

---

## 🔧 Technical Debt & Fixes Backlog

### High Priority (Blocking Features)

#### 1. Authentication System
**Files:** `frontend/lib/auth/token-manager.ts`, `frontend/components/layout/navbar.tsx`
**Issues:**
- Token not persisting/accessible
- Invalid token in API calls

**Required Changes:**
- Check token storage mechanism (localStorage vs cookies)
- Add token validation before API calls
- Implement automatic token refresh
- Add login timeout handling

#### 2. Import Job Processing
**Files:** `backend/app/services/import_service.py`, `backend/app/api/import_api.py`
**Issues:**
- Jobs stuck in processing state
- No job timeout/cleanup
- Failed job retry

**Required Changes:**
- Add job timeout mechanism (30 minutes max)
- Implement automatic cleanup of stuck jobs
- Add job retry logic for transient failures
- Update database schema for job timestamps

#### 3. Database Job Management
**Files:** `backend/migrations/`, `backend/app/db/models/import.py`
**Issues:**
- Stale job records in database
- No job status tracking
- Missing job history/archive

**Required Changes:**
- Add `completed_at`, `failed_at`, `timeout_at` columns
- Implement job archiving/cleanup
- Add job status change logging

### Medium Priority (Quality)

#### 4. Error Handling & User Feedback
**Files:** `frontend/components/import/csv-uploader.tsx`, `backend/app/api/errors.py`
**Issues:**
- Poor user feedback on failures
- Generic error messages
- No retry mechanism for transient errors

#### 5. Redis Configuration
**Files:** `backend/app/services/cache_service.py`, Redis setup scripts
**Issues:**
- Possible Redis authentication issues
- Cache invalidation problems
- Job status caching conflicts

### Low Priority (Future Enhancements)

#### 6. Testing & CI/CD
**Files:** `backend/tests/`, `frontend/tests/`
**Issues:**
- Limited integration tests
- No end-to-end testing for import flow
- Missing API contract tests

---

## 🗂️ Quick Fix Instructions

### Fix Issue A: Clear Stuck Upload (Immediate)
```bash
# Backend: Clear database stuck jobs
python -c "
import asyncio
from app.db.base import engine
from sqlalchemy import text

async def clear_stuck_jobs():
    async with engine.begin() as conn:
        # Clear stuck jobs (older than 1 hour)
        await conn.execute(text('''
            DELETE FROM import_jobs 
            WHERE status IN ('processing', 'pending') 
            AND created_at < NOW() - INTERVAL '1 hour'
        '''))
    print('Cleared stuck jobs')
        
asyncio.run(clear_stuck_jobs())

# Clear Redis job cache
docker exec mefeed_redis_dev redis-cli FLUSHALL
```

### Fix Issue B: Authentication (Moderate)
```bash
# Check token storage
browser -> Application -> Local Storage -> 
# Look for: access_token, refresh_token

# Test user flow
1. Clear browser local storage
2. Login with existing user
3. Check token appears in storage
4. Try CSV upload
```

---

## 📁 Key Files to Modify

### Authentication Fix
- `frontend/lib/auth/token-manager.ts` - Token persistence
- `frontend/lib/api/client.ts` - Request headers 
- `frontend/components/layout/navbar.tsx` - Auth state

### Import Job Fix  
- `backend/app/services/import_service.py` - Job processing logic
- `backend/app/db/models/import.py` - Job model timestamps
- `backend/app/api/import_api.py` - Job status handling

### Database Schema Updates
```sql
ALTER TABLE import_jobs 
ADD COLUMN completed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN failed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN timeout_at TIMESTAMP WITH TIME ZONE;
```

---

## 🧪 Testing Checklist

### Before Next Session:
1. [ ] Clear browser local storage completely
2. [ ] Login with user account
3. [ ] Verify token appears in storage  
4. [ ] Test unread count in navbar
5. [ ] Try CSV upload

### After Fixes:
1. [ ] Upload should work (200 OK)
2. [ ] Unread count shows number (or 0)
3. [ ] Job processes and completes
4. [ ] New uploads show in library

---

## 📚 Documentation Status

**Updated Files:**
- ✅ `SESSION_CONTINUATION_GUIDE.md` (this file)
- ✅ `DATABASE_SETUP.md`  
- ❌ `PROJECT_STATUS.md` (needs update)

**To Update Documentation:**
- Add authentication troubleshooting guide
- Update CSV upload process documentation
- Add import job management section

---

## 🚀 Next Session Start Point

1. **Clear Browser Storage**
2. **Run Database Cleanup Script**
3. **Test Authentication**
4. **Verify CSV Upload**
5. **Test Import Processing**

**All fixes identified and documented for smooth continuation!** 🎯

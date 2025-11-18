# Frontend Railway Deployment - Debug Session Report

**Date**: 2025-10-28/29  
**Duration**: ~3 hours  
**Status**: ⚠️ UNRESOLVED - Frontend cannot communicate with Backend  
**Primary Issue**: CORS + JWT Key Configuration

---

## 🎯 Session Goal

Deploy the Next.js frontend to Railway and establish working communication with the already-deployed FastAPI backend.

---

## 📊 Initial State

### ✅ What Was Working
- **Backend**: Deployed on Railway at `https://media-feed-production.up.railway.app`
  - Health endpoint responding: `GET /health` returns 200
  - PostgreSQL and Redis services running
  - Docker-based deployment using `RAILWAY_DOCKERFILE_PATH` environment variable

- **Frontend**: Running locally on `http://localhost:3000`
  - All features implemented (auth, CSV upload, media library, notifications)
  - Local development working correctly

- **Local Setup**: Both services communicating successfully via `http://localhost:8000` and `http://localhost:3000`

### ❌ What Needed Fixing
- Frontend not deployed to Railway
- No production environment for frontend
- CORS not configured for production frontend URL

---

## 🔄 Deployment Process & Issues Encountered

### Phase 1: Initial Frontend Service Creation (30 minutes)

#### Issue 1.1: Railway Configuration Confusion
**Problem**: 
- Railway removed "Root Directory" UI option
- Documentation was outdated suggesting Root Directory setting
- Initial confusion about how to deploy frontend from monorepo

**Attempted Solutions**:
1. ❌ Tried to use non-existent "Root Directory" setting
2. ❌ Created `railway.json` in frontend folder with `dockerfilePath: "Dockerfile"` and `dockerContext: "."`
3. ✅ **Solution**: Use `RAILWAY_DOCKERFILE_PATH` environment variable

**Result**: Understood Railway's current approach using env vars instead of UI config

---

#### Issue 1.2: Frontend Service Building Backend Code
**Problem**: 
```
Build Logs showed:
COPY backend/requirements.txt .
ERROR: JWT_PRIVATE_KEY environment variable not set
```

Frontend service was using the ROOT `railway.json` which pointed to `backend/Dockerfile`.

**Root Cause**: 
- ROOT `railway.json` was read by ALL services from the same repo
- Both backend and frontend services used the same configuration file

**Attempted Solutions**:
1. ❌ Created `frontend/railway.json` (ignored by Railway)
2. ❌ Set `RAILWAY_DOCKERFILE_PATH=frontend/Dockerfile` (overridden by railway.json)
3. ✅ **Solution**: Renamed ROOT `railway.json` to `railway.backend.json`
4. ✅ Set `RAILWAY_DOCKERFILE_PATH` for BOTH services:
   - Backend: `RAILWAY_DOCKERFILE_PATH=backend/Dockerfile`
   - Frontend: `RAILWAY_DOCKERFILE_PATH=frontend/Dockerfile`

**Files Modified**:
- `railway.json` → `railway.backend.json` (renamed)
- Commit: `ec80748` - "fix: Remove root railway.json to allow per-service Dockerfile configuration"

**Result**: Frontend now builds correctly using `frontend/Dockerfile`

---

#### Issue 1.3: Redis Missing Secrets Declaration
**Problem**:
```
Redis logs:
ERROR: cat: can't open '/run/secrets/redis_password': No such file or directory
*** FATAL CONFIG FILE ERROR (Redis 7.4.6) ***
```

**Root Cause**: `docker-compose.yml` Redis service missing `secrets:` declaration

**Solution**:
```yaml
redis:
  image: redis:7-alpine
  secrets:
    - redis_password  # <-- Added this
```

**Files Modified**:
- `docker-compose.yml`

**Result**: Local Redis now starts correctly

---

#### Issue 1.4: Frontend Dockerfile Context Mismatch
**Problem**: 
Frontend Dockerfile had `COPY package.json` assuming context was `/frontend`, but `dockerContext: "."` was at repo root.

**Solution**: Updated Dockerfile to copy from correct path:
```dockerfile
# Before:
COPY package.json package-lock.json* ./

# After:
COPY frontend/package.json frontend/package-lock.json* ./
COPY frontend/ .
```

**Files Modified**:
- `frontend/Dockerfile`
- Commit: `b3d9e50` - "fix: Adapt frontend Dockerfile for Railway root context deployment"

**Result**: Frontend Docker build succeeds

---

### Phase 2: Port Configuration (10 minutes)

#### Issue 2.1: Frontend Running on Wrong Port
**Problem**: 
```
Frontend Logs:
✓ Ready in 86ms
- Local: http://localhost:8080
```

Railway auto-set `PORT=8080` but Next.js standalone was listening on 8080, while Railway health check expected port 3000.

**Attempted Solutions**:
1. ❌ Remove PORT env var (Railway sets it automatically)
2. ✅ **Solution**: Changed Railway port setting from 3000 to 8080 in Dashboard

**Result**: Frontend deployment successful, accessible at `https://proud-courtesy-production-992b.up.railway.app`

---

### Phase 3: CORS & Backend Communication (2+ hours) ⚠️ UNRESOLVED

#### Issue 3.1: Initial CORS Errors
**Problem**:
```
Browser Console:
Access to XMLHttpRequest at 'https://media-feed-production.up.railway.app/api/auth/register' 
from origin 'https://proud-courtesy-production-992b.up.railway.app' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present
```

**Root Cause Analysis**:
This error indicates the backend is NOT sending CORS headers at all, which means:
1. Backend is crashing (500 error) before CORS middleware runs, OR
2. CORS middleware is not configured with the frontend URL

**Investigation**:
```
Direct backend test:
POST /api/auth/register → 500 Internal Server Error
GET /health → 200 OK
```

Conclusion: Backend crashes on auth endpoints but health check works → Issue is in route-specific code

---

#### Issue 3.2: Backend 500 Error - JWSError
**Problem**:
```
Backend Logs:
jose.exceptions.JWSError: ('Could not deserialize key data. 
The data may be in an incorrect format, the provided password may be incorrect, 
it may be encrypted with an unsupported algorithm...')
```

**Root Cause**: JWT Keys in Railway were in wrong format
- Keys were generated using PowerShell `New-Object Security.Cryptography.RSACryptoServiceProvider`
- This creates Microsoft CryptoAPI Blob format
- `python-jose` requires OpenSSL PEM format (PKCS#8)

**Attempted Solutions**:

1. **Attempt 1**: Fixed Pydantic env_file loading
   ```python
   # Problem: env_file was interfering with Railway env vars
   class Config:
       env_file = str(DEFAULT_ENV_FILE)  # Wrong in Railway
   
   # Solution:
   class Config:
       env_file = str(DEFAULT_ENV_FILE) if not os.getenv("RAILWAY_ENVIRONMENT") else None
   ```
   - Commit: `dd89ac8` - "fix: Disable env_file loading in Railway"
   - **Result**: ❌ Still had 500 errors

2. **Attempt 2**: Updated hardcoded ALLOWED_ORIGINS
   ```python
   # backend/app/core/config.py
   ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:3001,https://proud-courtesy-production-992b.up.railway.app"
   ```
   - Commit: `60ed43d` - "feat: Add Railway frontend URL to CORS allowed origins"
   - **Result**: ❌ Still had 500 errors (backend crashed before CORS headers sent)

3. **Attempt 3**: Set ALLOWED_ORIGINS Environment Variable in Railway
   - Set in Railway Dashboard: 
     ```
     ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,https://proud-courtesy-production-992b.up.railway.app
     ```
   - **Result**: ❌ Still had 500 errors (JWT keys still wrong)

4. **Attempt 4**: Generated new JWT keys using cryptography library
   - Created `scripts/generate-railway-keys.py`
   - Used `cryptography.hazmat.primitives` with PKCS8 format
   - **Issue**: Script had Unicode encoding errors preventing file save
   - **Result**: ⚠️ Keys generated but not properly saved to files

5. **Attempt 5**: Manually copied generated keys to Railway
   - Copied JWT_PRIVATE_KEY and JWT_PUBLIC_KEY to Railway Dashboard
   - Format: PEM with `\n` as literal text (not actual newlines)
   - **Result**: ⚠️ Keys updated in Railway but still showing errors

---

#### Issue 3.3: Current Unresolved State

**Latest Backend Logs** (from deployment 20 minutes ago):
```
Deploy Logs:
Railway Entrypoint: Setting up secrets...
JWT private key written to file
JWT public key written to file
Encryption key written to file

Runtime Logs:
ERROR: Exception in ASGI application
jwt priv key -----BEGIN RSA PRIVATE KEY-----\n...
```

**Critical Finding**: Backend logs show `-----BEGIN RSA PRIVATE KEY-----` 
- This is PKCS#1 format (old, wrong)
- Should be `-----BEGIN PRIVATE KEY-----` (PKCS#8 format)
- This means the keys in Railway Variables are STILL the old, incorrect keys

**Why Backend Crashes**:
1. Request comes to `/api/auth/register`
2. AuthService tries to create JWT token
3. `python-jose` tries to deserialize JWT_PRIVATE_KEY
4. Key format is wrong (PKCS#1 vs PKCS#8)
5. JWSError raised
6. Unhandled exception → 500 error
7. CORS headers never sent (crash happens before response)
8. Browser sees CORS error (but real issue is 500)

---

## 🔍 Technical Details

### Architecture Overview
```
User Browser
    ↓
Frontend (Next.js) - proud-courtesy-production-992b.up.railway.app:8080
    ↓ API Request
Backend (FastAPI) - media-feed-production.up.railway.app:8080
    ↓
PostgreSQL + Redis
```

### CORS Middleware Chain (main.py)
```python
# Order matters - LIFO execution
if settings.DEBUG:
    app.add_middleware(CORSMiddleware, allow_origins=["*"])  # Debug mode
else:
    app.add_middleware(CORSMiddleware, 
                      allow_origins=settings.allowed_origins_list)  # Production

if not settings.DEBUG:
    app.middleware("http")(origin_validation_middleware)  # Custom validation
app.middleware("http")(security_headers_middleware)
app.middleware("http")(audit_logging_middleware)
app.middleware("http")(request_id_middleware)
```

### JWT Token Creation Flow
```python
# app/services/auth_service.py
async def create_tokens(user_id: str) -> TokenResponse:
    payload = {...}
    # This line fails:
    access_token = jwt.encode(
        payload, 
        settings.jwt_private_key,  # <-- Wrong format key
        algorithm="RS256"
    )
```

### Environment Variables in Railway

**Backend Service** (`media-feed`):
```
DATABASE_URL=postgresql://...  (auto from Postgres service)
REDIS_URL=redis://...  (auto from Redis service)
RAILWAY_DOCKERFILE_PATH=backend/Dockerfile
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,https://proud-courtesy-production-992b.up.railway.app
DEBUG=false
JWT_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----\n...  (WRONG FORMAT!)
JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----\n...  (Correct)
ENCRYPTION_KEY=...
SECRET_KEY=...
SMTP_HOST=smtp-relay.brevo.com
SMTP_USER=...
SMTP_PASSWORD=...
```

**Frontend Service** (`proud-courtesy`):
```
RAILWAY_DOCKERFILE_PATH=frontend/Dockerfile
NEXT_PUBLIC_API_URL=https://media-feed-production.up.railway.app
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1
PORT=8080  (auto-set by Railway)
```

---

## 📁 Files Modified During Session

### Configuration Files
1. `railway.json` → `railway.backend.json` (renamed)
2. `frontend/railway.json` (created, then path updated)
3. `frontend/.env.production` (created)
4. `docker-compose.yml` (added Redis secrets)

### Source Code
1. `backend/app/core/config.py`:
   - Added frontend URL to ALLOWED_ORIGINS default
   - Fixed env_file loading for Railway
   
2. `frontend/Dockerfile`:
   - Updated COPY paths for root dockerContext

3. `start-bulletproof.ps1`:
   - Fixed PowerShell ternary operator syntax

### Scripts Created
1. `scripts/generate-railway-keys.py` - Generate proper PKCS#8 JWT keys
2. `scripts/clear-users.py` - Clear users table in Railway DB
3. `scripts/check-users.py` - Verify user count
4. `scripts/deploy-frontend-railway.ps1` - Deployment helper (not used due to encoding issues)

### Git Commits
- `9cce7e6` - feat: Add Railway frontend deployment configuration
- `fdd863b` - fix: Update frontend railway.json to use correct Dockerfile path
- `b3d9e50` - fix: Adapt frontend Dockerfile for Railway root context deployment
- `ec80748` - fix: Remove root railway.json to allow per-service Dockerfile configuration
- `60ed43d` - feat: Add Railway frontend URL to CORS allowed origins
- `dd89ac8` - fix: Disable env_file loading in Railway to prioritize environment variables

---

## 🎯 Root Cause Summary

### The Core Problem
**JWT Key Format Mismatch** causing all downstream issues:

1. **Primary Issue**: JWT_PRIVATE_KEY in Railway is PKCS#1 format (`BEGIN RSA PRIVATE KEY`)
   - `python-jose` library requires PKCS#8 format (`BEGIN PRIVATE KEY`)
   
2. **Symptom**: Backend crashes with JWSError on any auth endpoint
   - `/api/auth/register` → 500
   - `/api/auth/login` → 500
   
3. **Cascade Effect**: 500 error prevents CORS headers from being sent
   - Browser sees "CORS policy" error
   - Real issue is backend crash, not CORS configuration
   
4. **Misleading Signals**: 
   - CORS *is* configured correctly in code
   - ALLOWED_ORIGINS *does* include frontend URL
   - Issue happens *before* CORS middleware can execute

### Why This Is Hard to Debug
- Error message says "CORS" but root cause is "JWT keys"
- Backend health check works (doesn't need JWT)
- Config changes don't fix it (keys are the problem)
- Multiple layers of middleware obscure the real issue

---

## ✅ What Actually Works

1. **Deployment Infrastructure**: Both services deploy successfully
2. **Docker Configuration**: Dockerfiles build correctly
3. **Environment Variables**: Loading correctly (verified via logs)
4. **Database**: PostgreSQL accessible and working (user table cleared successfully)
5. **CORS Middleware**: Configured correctly (just never executes due to crash)
6. **Frontend Build**: Next.js standalone mode works
7. **Port Configuration**: Both services listening on correct ports

---

## ❌ What Doesn't Work

1. **JWT Key Format**: Private key in wrong format for python-jose
2. **Backend Auth Endpoints**: Crash on token generation
3. **Frontend-Backend Communication**: Blocked by backend crashes
4. **Key Generation Script**: Unicode encoding issues prevent file saving

---

## 🔧 Required Solution

### Immediate Action Required
**Generate and upload correct PKCS#8 format JWT keys to Railway**

### Steps to Fix

1. **Generate proper PKCS#8 keys** (NOT PKCS#1):
   ```python
   from cryptography.hazmat.primitives.asymmetric import rsa
   from cryptography.hazmat.primitives import serialization
   from cryptography.hazmat.backends import default_backend
   
   # Generate keypair
   private_key = rsa.generate_private_key(
       public_exponent=65537,
       key_size=2048,
       backend=default_backend()
   )
   
   # CRITICAL: Use PKCS8 format (not PKCS1)
   private_pem = private_key.private_bytes(
       encoding=serialization.Encoding.PEM,
       format=serialization.PrivateFormat.PKCS8,  # Results in "BEGIN PRIVATE KEY"
       encryption_algorithm=serialization.NoEncryption()
   )
   
   public_key = private_key.public_key()
   public_pem = public_key.public_bytes(
       encoding=serialization.Encoding.PEM,
       format=serialization.PublicFormat.SubjectPublicKeyInfo
   )
   ```

2. **Format for Railway Environment Variables**:
   - Convert actual newlines to literal `\n` text
   - Example: `-----BEGIN PRIVATE KEY-----\nMIIEvgIBADA...\n-----END PRIVATE KEY-----`

3. **Upload to Railway**:
   - Backend Service → Variables
   - Replace `JWT_PRIVATE_KEY` with PKCS#8 version
   - Replace `JWT_PUBLIC_KEY` with matching public key
   - Both must be from the SAME keypair

4. **Verify Format**:
   - Private key starts with: `-----BEGIN PRIVATE KEY-----` (NO "RSA"!)
   - Public key starts with: `-----BEGIN PUBLIC KEY-----`

5. **Redeploy Backend**:
   - Railway will auto-redeploy with new variables
   - Wait 2-3 minutes

6. **Test**:
   ```bash
   # Should return 201 Created (not 500)
   curl -X POST https://media-feed-production.up.railway.app/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"Test123!","username":"test"}'
   ```

### Alternative: Use OpenSSL Command Line
If Python cryptography continues to have issues:

```bash
# Generate PKCS#8 private key
openssl genpkey -algorithm RSA -out jwt_private.pem -pkeyopt rsa_keygen_bits:2048

# Extract public key
openssl rsa -pubout -in jwt_private.pem -out jwt_public.pem

# Convert to single line for Railway
cat jwt_private.pem | tr '\n' '|' | sed 's/|/\\n/g'
cat jwt_public.pem | tr '\n' '|' | sed 's/|/\\n/g'
```

---

## 📊 System State

### Railway Services

**Backend** (`media-feed`):
- Status: ✅ Running (but crashes on auth endpoints)
- URL: https://media-feed-production.up.railway.app
- Health: ✅ `GET /health` returns 200
- Auth: ❌ `POST /api/auth/register` returns 500 (JWSError)
- Last Deploy: 20 minutes ago
- Issue: JWT_PRIVATE_KEY wrong format

**Frontend** (`proud-courtesy`):
- Status: ✅ Running
- URL: https://proud-courtesy-production-992b.up.railway.app
- Port: 8080
- Last Deploy: 1 hour ago
- Issue: Cannot communicate with backend (backend crashes)

**Postgres**:
- Status: ✅ Running
- URL: Internal + External (caboose.proxy.rlwy.net:15681)
- Data: User table cleared (0 users)

**Redis**:
- Status: ✅ Running
- Secrets: ✅ Configured correctly

### Local Environment

**Database Secrets**: Generated in `secrets/` folder
- ✅ `jwt_private.pem` - Contains RSA PRIVATE KEY (PKCS#1 - wrong!)
- ✅ `jwt_public.pem` - Contains PUBLIC KEY (correct)
- ✅ `encryption.key`
- ✅ `secret_key.txt`
- ✅ `db_user.txt`, `db_password.txt`, `redis_password.txt`

**Issue**: Local secrets also have wrong key format - need regeneration

---

## 🚫 What NOT to Do

1. **Don't use DEBUG=true** as a workaround
   - This bypasses security checks
   - Doesn't fix the root problem
   - Not acceptable for production

2. **Don't regenerate keys without fixing format**
   - PowerShell CryptoServiceProvider creates PKCS#1
   - Must use proper cryptography library with PKCS#8

3. **Don't assume CORS is the problem**
   - CORS error is a symptom
   - Backend crash is the cause

4. **Don't update ALLOWED_ORIGINS again**
   - It's already correct
   - Won't fix JWT key issue

---

## 💡 Lessons Learned

1. **Railway Configuration Evolution**:
   - UI options removed over time
   - Must use environment variables for service-specific config
   - Documentation lags behind product changes

2. **Monorepo Deployment Challenges**:
   - Single `railway.json` at root affects all services
   - Solution: Remove root config, use `RAILWAY_DOCKERFILE_PATH` per service

3. **Error Message Interpretation**:
   - Browser "CORS error" doesn't always mean CORS misconfiguration
   - Check backend logs for 500 errors first
   - CORS headers only sent if request completes successfully

4. **JWT Key Format Matters**:
   - PKCS#1 (`BEGIN RSA PRIVATE KEY`) ≠ PKCS#8 (`BEGIN PRIVATE KEY`)
   - Different libraries expect different formats
   - python-jose requires PKCS#8

5. **Environment Variable Priority**:
   - Pydantic `env_file` can interfere with Railway's native env vars
   - Must conditionally disable `env_file` in cloud environments

---

## 📝 Next Steps for Resolution

### Priority 1: Fix JWT Keys (HIGH - BLOCKER)
1. Generate PKCS#8 format keys using proper method
2. Upload to Railway Backend Variables
3. Verify format in logs after deploy
4. Test auth endpoints

### Priority 2: Verify CORS (MEDIUM)
1. After JWT fix, test OPTIONS request
2. Confirm `Access-Control-Allow-Origin` header present
3. Test actual registration from frontend

### Priority 3: Production Hardening (LOW)
1. Remove hardcoded ALLOWED_ORIGINS from code (rely on env var)
2. Set DEBUG=false (already done)
3. Monitor logs for any other issues

### Priority 4: Documentation (LOW)
1. Document Railway deployment process
2. Update RAILWAY_DEPLOYMENT_GUIDE.md with final working solution
3. Add troubleshooting section for common issues

---

## 🔗 Related Files for Next Session

**Configuration**:
- `backend/app/core/config.py` - Settings and env var loading
- `backend/app/main.py` - CORS middleware setup
- `backend/app/core/middleware.py` - origin_validation_middleware
- `railway.backend.json` - Backend Railway config reference

**Deployment**:
- `backend/Dockerfile` - Working backend Docker config
- `frontend/Dockerfile` - Working frontend Docker config  
- `backend/railway-entrypoint.sh` - Secret setup script

**Scripts**:
- `scripts/generate-railway-keys.py` - JWT key generator (needs fix for file saving)
- `scripts/clear-users.py` - Database cleanup utility

**Secrets**:
- `secrets/jwt_private.pem` - WRONG FORMAT - needs regeneration
- `secrets/jwt_public.pem` - Correct format

---

## 🎓 Technical Context for AI Assistant

### Key Concepts to Understand

**PKCS#1 vs PKCS#8**:
- PKCS#1: RSA-specific format, header `BEGIN RSA PRIVATE KEY`
- PKCS#8: Generic format, header `BEGIN PRIVATE KEY`
- python-jose library ONLY accepts PKCS#8
- Microsoft CryptoAPI generates PKCS#1 by default

**Railway Environment Variables**:
- Multi-line values must use `\n` as literal text
- Example: `KEY=-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----`
- NOT actual newlines in the variable value

**FastAPI Middleware Execution Order**:
- Added last = executes first (LIFO)
- If any middleware crashes, subsequent middleware doesn't run
- CORS middleware runs early, but after error handling
- Uncaught exceptions prevent CORS headers from being sent

**Railway Service Configuration**:
- `RAILWAY_DOCKERFILE_PATH` overrides automatic detection
- Required for monorepo with multiple Dockerfiles
- Each service needs its own value
- No more "Root Directory" UI option

---

## ✅ Success Criteria

Deployment will be successful when:

1. ✅ Frontend loads at `https://proud-courtesy-production-992b.up.railway.app`
2. ✅ Backend `/health` returns 200
3. ✅ Backend `/api/auth/register` returns 201 (not 500)
4. ✅ Browser console shows NO CORS errors
5. ✅ User can register successfully
6. ✅ User can login successfully
7. ✅ JWT tokens are generated and validated
8. ✅ Frontend-backend communication works end-to-end

---

**End of Session Report**

Total Issues Encountered: 8  
Issues Resolved: 6  
Issues Remaining: 2 (JWT keys, downstream CORS verification)  
Estimated Time to Resolution: 30-60 minutes with correct JWT key generation

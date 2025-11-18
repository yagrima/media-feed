# Railway Deployment Guide

**Status**: Production Ready  
**Last Updated**: November 18, 2025  

---

## 📋 Overview

Me(dia) Feed is deployed on [Railway](https://railway.app) using a monorepo structure.
- **Frontend**: Next.js 14 (Standalone Docker)
- **Backend**: FastAPI (Python 3.11 Docker)
- **Database**: PostgreSQL (Railway Plugin)
- **Cache**: Redis (Railway Plugin)

---

## 🚀 Quick Start

### Prerequisites
- Railway Account
- GitHub Repository Access
- Railway CLI (optional but recommended)

### Deployment Steps

1.  **Connect GitHub**: Create a new project on Railway and select "Deploy from GitHub repo".
2.  **Add Services**:
    *   Add **PostgreSQL** plugin.
    *   Add **Redis** plugin.
3.  **Configure Backend**:
    *   Root Directory: `backend`
    *   Variables: Import from `Media Feed Secrets` (see Secrets section).
4.  **Configure Frontend**:
    *   Root Directory: `/frontend`
    *   Variables: `NEXT_PUBLIC_API_URL` pointing to backend.

---

## 🔐 Configuration & Secrets

### Environment Variables

#### Backend Service
```bash
# Secrets (PKCS#8 format for Keys)
JWT_PRIVATE_KEY=...
JWT_PUBLIC_KEY=...
ENCRYPTION_KEY=...
SECRET_KEY=...

# Database & Cache (Auto-set by Railway)
DATABASE_URL=...
REDIS_URL=...

# Email (Brevo SMTP)
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
FROM_EMAIL=...

# App Config
DEBUG=false
ALLOWED_ORIGINS=https://your-frontend.railway.app
TMDB_API_KEY=...
SENTRY_DSN=...
```

#### Frontend Service
```bash
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_SENTRY_DSN=...
NODE_ENV=production
```

### ⚠️ Critical: JWT Key Format
Railway requires **PKCS#8** format for RSA keys.
- Use `\n` for newlines in the Railway dashboard variable editor.
- Do not use "RSA PRIVATE KEY" header (PKCS#1), use "BEGIN PRIVATE KEY" (PKCS#8).

---

## 🔍 Verification Checklist

After deployment, perform these checks to verify stability.

### 1. Backend Health
- [ ] GET `/health` returns 200 OK.
- [ ] Logs show "Application startup complete".

### 2. Frontend Accessibility
- [ ] Homepage loads without 500/404 errors.
- [ ] Static assets (CSS/JS) load correctly.

### 3. Critical User Flows
- [ ] **Registration**: Create a new user. Check for email (if enabled).
- [ ] **Login**: Log in with new user. Verify JWT in localStorage.
- [ ] **Dashboard**: Access protected route.

### 4. Integrations
- [ ] **Audible**: Connect/Sync flows (note: check logs for 400/403 errors instead of 401).
- [ ] **TMDB**: Search for media.
- [ ] **CSV Import**: Upload a test file.

---

## 🛠️ Troubleshooting Tips

### 🚨 CRITICAL: Railway Dashboard Caching
**Problem**: Dashboard shows old/stale deployment data.
**Solution**: **ALWAYS use Incognito Mode** to check deployment status. The dashboard caches aggressively.

### Common Issues

#### 1. "Deployment Stuck" or "No New Deployment"
- **Cause**: Browser cache or filtered view.
- **Fix**: Open Incognito window. Check "Show More" in deployments list.

#### 2. build Failed: "Module not found"
- **Cause**: Missing dependencies or wrong Root Directory.
- **Fix**: Ensure `package.json` includes all deps. Check `RAILWAY_DOCKERFILE_PATH`.

#### 3. Auth Logout Bug (Audible)
- **Cause**: 401 errors from backend trigger frontend logout.
- **Fix**: Backend must return 400 or 403 for third-party auth failures. (Fixed Nov 18, 2025).

#### 4. CORS Errors
- **Cause**: `ALLOWED_ORIGINS` mismatch.
- **Fix**: Add frontend URL (without trailing slash) to backend env vars.

### CLI Debugging
Use Railway CLI for direct logs if dashboard is laggy:
```bash
railway login
railway logs
```

---

## 📚 Reference

- **Project ID**: [Your Project ID]
- **Production URL**: https://proud-courtesy-production-992b.up.railway.app
- **Backend URL**: https://media-feed-production.up.railway.app

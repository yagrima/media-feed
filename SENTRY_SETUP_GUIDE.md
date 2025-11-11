# Sentry Error Monitoring Setup Guide

**Goal:** Implement comprehensive error tracking for Me Feed application

**Duration:** 2-3 hours

---

## Step 1: Sentry Account Setup (5 minutes)

### Create Account
1. Go to https://sentry.io/signup/
2. Sign up (free tier is sufficient for MVP)
3. Create new organization (e.g., "Me Feed")

### Create Projects
Create TWO projects (one for each service):

**Backend Project:**
- Name: me-feed-backend
- Platform: Python / FastAPI
- Copy DSN (Data Source Name) - looks like: `https://xxxxx@yyyy.ingest.sentry.io/zzzzzz`

**Frontend Project:**
- Name: me-feed-frontend
- Platform: Next.js
- Copy DSN (different from backend DSN)

**Why two projects?** Separates frontend and backend errors for better debugging.

---

## Step 2: Backend Integration (30-45 minutes)

### Install Sentry SDK

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install sentry-sdk[fastapi]
pip freeze > requirements.txt
```

### Configure Sentry in Backend

Create `backend/app/core/sentry.py`:

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from app.core.config import settings

def init_sentry():
    """Initialize Sentry error tracking"""
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,  # 10% performance monitoring
            profiles_sample_rate=0.1,  # 10% profiling
            environment=settings.ENVIRONMENT,  # "production" or "development"
            release=settings.VERSION,  # e.g., "1.1.0"
        )
```

### Add SENTRY_DSN to config

In `backend/app/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Error Tracking
    SENTRY_DSN: str = ""
    ENVIRONMENT: str = "production"
    VERSION: str = "1.1.0"
```

### Initialize in main.py

In `backend/app/main.py` (at the top, before app creation):

```python
from app.core.sentry import init_sentry

# Initialize Sentry FIRST
init_sentry()

app = FastAPI(...)
```

### Test Backend Error Capture

Add test endpoint:

```python
@app.get("/debug/sentry-test")
async def sentry_test():
    """Test endpoint to verify Sentry is working"""
    raise Exception("This is a test error for Sentry!")
```

---

## Step 3: Frontend Integration (30-45 minutes)

### Install Sentry SDK

```powershell
cd frontend
npm install @sentry/nextjs
```

### Run Sentry Wizard

```powershell
npx @sentry/wizard@latest -i nextjs
```

This creates:
- `sentry.client.config.ts`
- `sentry.server.config.ts`
- `sentry.edge.config.ts`

### Configure Sentry Files

**File: `frontend/sentry.client.config.ts`**

```typescript
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 0.1,
  debug: false,
  environment: process.env.NODE_ENV,
  replaysOnErrorSampleRate: 1.0,
  replaysSessionSampleRate: 0.1,
});
```

**File: `frontend/sentry.server.config.ts`**

```typescript
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 0.1,
  debug: false,
  environment: process.env.NODE_ENV,
});
```

### Add Error Boundary

**File: `frontend/components/error-boundary.tsx`** (update existing):

```typescript
'use client'

import * as Sentry from "@sentry/nextjs";
import React, { Component, ReactNode } from 'react'
import { Button } from './ui/button'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
    // Send to Sentry
    Sentry.captureException(error, {
      contexts: {
        react: {
          componentStack: errorInfo.componentStack,
        },
      },
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
          <div className="max-w-md w-full bg-card border rounded-lg p-6 space-y-4">
            <h2 className="text-2xl font-bold text-destructive">
              Something went wrong
            </h2>
            <p className="text-muted-foreground">
              An error occurred. Our team has been notified.
            </p>
            {this.state.error && (
              <pre className="text-xs bg-muted p-2 rounded overflow-auto">
                {this.state.error.message}
              </pre>
            )}
            <Button
              onClick={() => {
                this.setState({ hasError: false, error: null })
                window.location.href = '/'
              }}
            >
              Go to Home
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
```

### Test Frontend Error

Add test button somewhere (e.g., in Settings page):

```typescript
<Button onClick={() => {
  throw new Error("This is a test error for Sentry!");
}}>
  Test Sentry (Dev Only)
</Button>
```

---

## Step 4: Environment Variables (10 minutes)

### Local Development

**Backend `.env`:**
```bash
SENTRY_DSN=https://xxxxx@yyyy.ingest.sentry.io/zzzzzz-backend
ENVIRONMENT=development
VERSION=1.1.0
```

**Frontend `.env.local`:**
```bash
NEXT_PUBLIC_SENTRY_DSN=https://xxxxx@yyyy.ingest.sentry.io/zzzzzz-frontend
```

### Railway Production

**Backend Service Variables:**
```
SENTRY_DSN=https://xxxxx@yyyy.ingest.sentry.io/zzzzzz-backend
ENVIRONMENT=production
VERSION=1.1.0
```

**Frontend Service Variables:**
```
NEXT_PUBLIC_SENTRY_DSN=https://xxxxx@yyyy.ingest.sentry.io/zzzzzz-frontend
```

---

## Step 5: Testing (20 minutes)

### Local Testing

**Backend Test:**
```powershell
# Start backend
cd backend
uvicorn app.main:app --reload

# In browser: http://localhost:8000/debug/sentry-test
# Should see error in Sentry dashboard
```

**Frontend Test:**
```powershell
# Start frontend
cd frontend
npm run dev

# Click test button in UI
# Should see error in Sentry dashboard
```

### Production Testing

After Railway deployment:
1. Visit https://media-feed-production.up.railway.app/debug/sentry-test
2. Click test error button in frontend
3. Check Sentry dashboard for both errors

---

## Step 6: Verify in Sentry Dashboard (10 minutes)

### Check Error Capture

In Sentry dashboard, verify:
- [x] Backend errors appear in me-feed-backend project
- [x] Frontend errors appear in me-feed-frontend project
- [x] Error shows stack trace
- [x] Error shows user context (browser, OS)
- [x] Error shows breadcrumbs (user actions before error)

### Setup Alerts (Optional)

Configure email/Slack alerts:
1. Sentry Dashboard → Alerts → New Alert Rule
2. Trigger: "When an event is seen"
3. Action: Send email
4. Save

---

## Step 7: Remove Test Endpoints (5 minutes)

After verification:

**Backend:** Remove `/debug/sentry-test` endpoint

**Frontend:** Remove test error button

Commit changes:
```bash
git add .
git commit -m "feat: Add Sentry error monitoring for production

- Integrated Sentry SDK in backend (FastAPI)
- Integrated Sentry SDK in frontend (Next.js)
- Added error boundaries with automatic reporting
- Configured separate projects for backend/frontend
- Performance monitoring enabled (10% sample rate)

Co-authored-by: factory-droid[bot] <138933559+factory-droid[bot]@users.noreply.github.com>"
```

---

## Expected Results

### What You Get

**Automatic Error Capture:**
- Backend exceptions (500 errors, database errors, etc.)
- Frontend React errors
- Unhandled promise rejections
- API call failures

**Error Details:**
- Full stack trace
- User context (email, ID if logged in)
- Browser/OS information
- Breadcrumbs (user actions leading to error)
- Request data (URL, headers, body)

**Performance Monitoring:**
- Slow API endpoints
- Database query performance
- Frontend rendering issues

**Alerts:**
- Email notifications for new errors
- Slack/Discord integration (optional)
- Daily/weekly digest emails

---

## Troubleshooting

### Errors Not Appearing in Sentry?

**Check:**
1. SENTRY_DSN is set correctly (no typos)
2. Backend: `init_sentry()` is called BEFORE FastAPI app creation
3. Frontend: Sentry config files exist
4. Test endpoint actually throws error
5. Internet connection works from Railway

**Debug:**
```python
# In backend/app/core/sentry.py
import logging
logger = logging.getLogger(__name__)

def init_sentry():
    if settings.SENTRY_DSN:
        logger.info(f"Initializing Sentry with DSN: {settings.SENTRY_DSN[:20]}...")
        sentry_sdk.init(...)
        logger.info("Sentry initialized successfully")
    else:
        logger.warning("SENTRY_DSN not configured - error tracking disabled")
```

---

## Cost

**Sentry Free Tier:**
- 5,000 errors per month
- 10,000 performance events per month
- 30-day retention
- Unlimited projects

**Sufficient for:**
- MVP/Small apps
- ~165 errors per day
- Upgrade to paid if needed ($26/month for more)

---

## Next Steps After Implementation

1. Monitor Sentry dashboard daily (first week)
2. Fix errors as they appear
3. Set up alerts for critical errors
4. Review weekly error trends
5. Optimize performance based on traces

---

## Documentation

- Sentry Docs: https://docs.sentry.io/platforms/python/guides/fastapi/
- Next.js Integration: https://docs.sentry.io/platforms/javascript/guides/nextjs/

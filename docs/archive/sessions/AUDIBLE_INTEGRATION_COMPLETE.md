# Audible Integration - Complete Implementation Guide

**Date:** November 11, 2025  
**Status:** ✅ Backend Complete | Frontend In Progress  
**Deployment:** Production (Railway)  
**Version:** 1.2.0

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Backend Implementation](#backend-implementation)
4. [API Endpoints](#api-endpoints)
5. [Frontend Implementation](#frontend-implementation)
6. [Security](#security)
7. [Testing](#testing)
8. [Usage Guide](#usage-guide)
9. [Troubleshooting](#troubleshooting)

---

## Overview

### What Was Built

The Audible integration allows users to:
- **Connect** their Audible account securely
- **Import** their entire audiobook library (1-click)
- **Sync** library updates (new purchases, progress)
- **Disconnect** and remove stored credentials
- **View** connection status and audiobook count

### Key Features

- 🔐 **Secure Credential Storage** - User-specific encryption with PBKDF2
- 📚 **Rich Metadata** - Authors, narrators, duration, series, ratings
- 🔄 **Auto-Sync** - Update library with new purchases
- 🚦 **Rate Limiting** - Prevent API abuse (3 auth/hour, 10 syncs/day)
- ⚠️ **Error Handling** - CAPTCHA, 2FA, auth failures gracefully handled
- 🗄️ **Database Integration** - Audiobooks stored as `media.type = 'audiobook'`

---

## Architecture

### System Flow

```
┌─────────────┐
│   User      │
│  (Browser)  │
└──────┬──────┘
       │ 1. Enter Audible credentials
       ↓
┌─────────────────────────────┐
│  Frontend (Next.js)         │
│  - ConnectAudibleModal      │
│  - AudibleStatusCard        │
└──────────┬──────────────────┘
           │ 2. POST /api/audible/connect
           ↓
┌────────────────────────────────────────────┐
│  Backend (FastAPI)                         │
│  ┌─────────────────────────────────────┐  │
│  │ API Layer (audible.py)              │  │
│  │ - Rate limiting                     │  │
│  │ - Input validation                  │  │
│  └──────┬──────────────────────────────┘  │
│         │                                  │
│  ┌──────▼──────────────────────────────┐  │
│  │ Service Layer                       │  │
│  │ - AudibleService (auth, fetch)      │  │
│  │ - AudibleParser (data mapping)      │  │
│  └──────┬──────────────────────────────┘  │
│         │                                  │
│  ┌──────▼──────────────────────────────┐  │
│  │ Security Layer                      │  │
│  │ - User-specific encryption          │  │
│  │ - PBKDF2 key derivation             │  │
│  └──────┬──────────────────────────────┘  │
└─────────┼──────────────────────────────────┘
          │ 3. Store encrypted token
          ↓
┌────────────────────────────────┐
│  Database (PostgreSQL)         │
│  - audible_auth table          │
│  - media table (audiobooks)    │
│  - user_media (consumption)    │
└────────────────────────────────┘
          │ 4. Fetch library
          ↓
┌────────────────────────────────┐
│  Audible API (External)        │
│  - Authentication              │
│  - Library endpoint            │
│  - Device registration         │
└────────────────────────────────┘
```

### Database Schema

**New Table: `audible_auth`**
```sql
CREATE TABLE audible_auth (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    encrypted_token TEXT NOT NULL,  -- User-specific encryption
    marketplace VARCHAR(10) NOT NULL,  -- us, uk, de, etc.
    device_name VARCHAR(255),
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_audible_auth_user (user_id)
);
```

**Modified Table: `media`**
```sql
-- Existing table, now supports type = 'audiobook'
UPDATE media SET type = 'audiobook' WHERE ...;
```

**Audiobook Metadata (JSONB):**
```json
{
  "authors": ["Author Name"],
  "narrators": ["Narrator Name"],
  "duration_minutes": 720,
  "duration_display": "12h 0m",
  "publisher": "Publisher Name",
  "language": "en",
  "rating": 4.5,
  "num_ratings": 1234,
  "asin": "B00EXAMPLE",
  "audible_url": "https://www.audible.com/pd/B00EXAMPLE",
  "series": {
    "title": "Series Name",
    "sequence": "1"
  },
  "cover_images": {
    "500": "https://...",
    "1000": "https://..."
  }
}
```

---

## Backend Implementation

### Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `backend/app/services/audible_service.py` | 300 | Authentication, library fetching |
| `backend/app/services/audible_parser.py` | 280 | Data mapping to database |
| `backend/app/api/audible.py` | 370 | API endpoints |
| `backend/app/schemas/audible_schemas.py` | 140 | Request/response models |
| `backend/alembic/versions/008_add_audible_auth.py` | 50 | Database migration |

### Files Modified

| File | Changes | Purpose |
|------|---------|---------|
| `backend/app/core/security.py` | +63 lines | User-specific encryption |
| `backend/app/db/models.py` | +30 lines | AudibleAuth model |
| `backend/app/schemas/import_schemas.py` | +1 line | AUDIBLE_API enum |
| `backend/app/main.py` | +2 lines | Router registration |
| `backend/requirements.txt` | +1 line | audible==0.10.0 |

### Dependencies Added

```txt
audible==0.10.0
  └── Pillow>=9.4.0
  └── beautifulsoup4>=4.11.2
  └── httpx>=0.23.3
  └── pbkdf2>=1.3
  └── pyaes>=1.6.1
  └── rsa>=4.9
```

---

## API Endpoints

### 1. Connect Audible Account

**Endpoint:** `POST /api/audible/connect`

**Rate Limit:** 3 requests per hour per user

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "audible_password",
  "marketplace": "us"
}
```

**Marketplaces Supported:**
- `us` - United States
- `uk` - United Kingdom
- `de` - Germany
- `fr` - France
- `ca` - Canada
- `au` - Australia
- `in` - India
- `it` - Italy
- `jp` - Japan
- `es` - Spain

**Success Response (200):**
```json
{
  "success": true,
  "message": "Successfully imported 245 audiobooks from Audible",
  "device_name": "Me Feed - Web",
  "marketplace": "us",
  "books_imported": 245
}
```

**Error Responses:**

**401 - Invalid Credentials:**
```json
{
  "error": "Invalid email or password",
  "error_type": "auth_failed"
}
```

**400 - CAPTCHA Required:**
```json
{
  "error": "CAPTCHA verification required. Please try again later or use manual import.",
  "error_type": "captcha_required"
}
```

**400 - 2FA Required:**
```json
{
  "error": "Two-factor authentication detected. Please append your 2FA code to your password.",
  "error_type": "2fa_required"
}
```

**429 - Rate Limit Exceeded:**
```json
{
  "error": "Rate limit exceeded",
  "detail": "3 per 1 hour"
}
```

**Example cURL:**
```bash
curl -X POST https://media-feed-production.up.railway.app/api/audible/connect \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@audible.com",
    "password": "yourpassword",
    "marketplace": "us"
  }'
```

---

### 2. Sync Library

**Endpoint:** `POST /api/audible/sync`

**Rate Limit:** 10 requests per day per user

**Request Body:** None (uses stored token)

**Success Response (200):**
```json
{
  "success": true,
  "message": "Library synced successfully",
  "imported": 12,
  "updated": 3,
  "skipped": 230,
  "errors": 0,
  "total": 245
}
```

**Error Responses:**

**404 - Not Connected:**
```json
{
  "error": "Audible not connected",
  "detail": "Please connect your Audible account first"
}
```

**401 - Token Expired:**
```json
{
  "error": "Authentication token expired. Please reconnect your Audible account.",
  "error_type": "token_expired"
}
```

**Example cURL:**
```bash
curl -X POST https://media-feed-production.up.railway.app/api/audible/sync \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 3. Disconnect Audible

**Endpoint:** `DELETE /api/audible/disconnect`

**Request Body:** None

**Success Response (200):**
```json
{
  "success": true,
  "message": "Audible account disconnected successfully. Device removed from Amazon account."
}
```

**Note:** This will:
- Deregister the virtual device from Amazon account
- Delete encrypted token from database
- **NOT** delete imported audiobooks (they remain in your library)

**Example cURL:**
```bash
curl -X DELETE https://media-feed-production.up.railway.app/api/audible/disconnect \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 4. Get Connection Status

**Endpoint:** `GET /api/audible/status`

**Request Body:** None

**Success Response - Connected (200):**
```json
{
  "connected": true,
  "marketplace": "us",
  "device_name": "Me Feed - Web",
  "last_sync_at": "2025-11-11T23:30:00Z",
  "books_count": 245
}
```

**Success Response - Not Connected (200):**
```json
{
  "connected": false,
  "marketplace": null,
  "device_name": null,
  "last_sync_at": null,
  "books_count": null
}
```

**Example cURL:**
```bash
curl https://media-feed-production.up.railway.app/api/audible/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Frontend Implementation

### Components to Build

#### 1. ConnectAudibleModal

**Location:** `frontend/components/audible/connect-audible-modal.tsx`

**Purpose:** Modal dialog for entering Audible credentials

**Features:**
- Email input (validated)
- Password input (type="password")
- Marketplace dropdown (US, UK, DE, etc.)
- 2FA helper text
- Loading state during connection
- Error display (CAPTCHA, 2FA, invalid credentials)
- Success message with imported count

**Props:**
```typescript
interface ConnectAudibleModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: (data: AudibleConnectResponse) => void;
}
```

#### 2. AudibleStatusCard

**Location:** `frontend/components/audible/audible-status-card.tsx`

**Purpose:** Display connection status and actions

**Features:**
- Connection badge (Connected/Not Connected)
- Marketplace display
- Last sync timestamp
- Audiobook count
- "Sync Now" button (when connected)
- "Disconnect" button (when connected)
- "Connect Audible" button (when not connected)

**Props:**
```typescript
interface AudibleStatusCardProps {
  onConnect: () => void;
  onDisconnect: () => void;
  onSync: () => void;
}
```

#### 3. Audible API Client

**Location:** `frontend/lib/audible-api.ts`

**Purpose:** API client functions

**Functions:**
```typescript
export const audibleApi = {
  // Connect Audible account
  connect: async (data: AudibleConnectRequest): Promise<AudibleConnectResponse> => {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_URL}/api/audible/connect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || error.error);
    }
    
    return response.json();
  },
  
  // Sync library
  sync: async (): Promise<AudibleSyncResponse> => {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_URL}/api/audible/sync`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || error.error);
    }
    
    return response.json();
  },
  
  // Disconnect
  disconnect: async (): Promise<AudibleDisconnectResponse> => {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_URL}/api/audible/disconnect`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || error.error);
    }
    
    return response.json();
  },
  
  // Get status
  getStatus: async (): Promise<AudibleStatusResponse> => {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_URL}/api/audible/status`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || error.error);
    }
    
    return response.json();
  }
};
```

### Page Integrations

#### Import Page (`frontend/app/(dashboard)/import/page.tsx`)

**Add Section:**
```tsx
<Card>
  <CardHeader>
    <CardTitle>Import from Audible</CardTitle>
    <CardDescription>
      Connect your Audible account to import your audiobook library
    </CardDescription>
  </CardHeader>
  <CardContent>
    <AudibleStatusCard 
      onConnect={() => setShowConnectModal(true)}
      onDisconnect={handleDisconnect}
      onSync={handleSync}
    />
  </CardContent>
</Card>

<ConnectAudibleModal
  open={showConnectModal}
  onClose={() => setShowConnectModal(false)}
  onSuccess={(data) => {
    toast.success(`Imported ${data.books_imported} audiobooks!`);
    setShowConnectModal(false);
  }}
/>
```

#### Settings Page (`frontend/app/(dashboard)/settings/page.tsx`)

**Add Section:**
```tsx
<Card>
  <CardHeader>
    <CardTitle>Audible Integration</CardTitle>
    <CardDescription>
      Manage your Audible account connection
    </CardDescription>
  </CardHeader>
  <CardContent>
    <AudibleStatusCard 
      onConnect={() => setShowConnectModal(true)}
      onDisconnect={handleDisconnect}
      onSync={handleSync}
    />
  </CardContent>
</Card>
```

---

## Security

### Password Handling

**Critical: Passwords are NEVER stored**

1. User enters password in frontend
2. Sent via HTTPS to backend
3. Backend uses password **once** to authenticate with Audible
4. Password discarded immediately after authentication
5. Only encrypted token is stored

**Code Flow:**
```python
async def authenticate(user_id, email, password, marketplace):
    # Password only exists here
    auth = audible.Authenticator.from_login(email, password, locale=marketplace)
    
    # Password is now out of scope and garbage collected
    # Only token remains
    
    auth_dict = auth.to_dict()
    encrypted_token = encrypt_user_specific_data(auth_dict, user_id)
    
    return {'encrypted_token': encrypted_token}
    # Password no longer exists in memory
```

### Token Encryption

**User-Specific Encryption with PBKDF2:**

```python
def encrypt_user_specific_data(data: str, user_id: str) -> str:
    # Derive unique key per user
    base_material = settings.encryption_key  # Master key
    user_salt = user_id.encode()
    
    # PBKDF2 with 100,000 iterations
    computed_value = hashlib.pbkdf2_hmac(
        'sha256', 
        base_material.encode(), 
        user_salt, 
        100000,  # 100k iterations for security
        dklen=32
    )
    
    # Encrypt with Fernet (AES-128 in CBC mode)
    cipher = Fernet(base64.urlsafe_b64encode(computed_value))
    encrypted = cipher.encrypt(data.encode())
    
    return encrypted.decode()
```

**Why User-Specific Keys?**
- Each user's data encrypted with unique derived key
- If one user's key compromised, others remain secure
- Master key + User ID = Unique encryption key
- Cannot decrypt without both master key AND user ID

### Rate Limiting

**Protection Against Abuse:**

| Endpoint | Limit | Reason |
|----------|-------|--------|
| `/connect` | 3/hour | Prevent brute force auth attempts |
| `/sync` | 10/day | Prevent API abuse (Audible's servers) |
| `/disconnect` | Unlimited | Safe operation |
| `/status` | Unlimited | Read-only |

**Implementation:**
```python
from app.core.middleware import limiter

@limiter.limit("3/hour")
async def connect_audible(request: Request, ...):
    pass
```

### Audit Logging

**All Operations Logged:**

```python
logger.info(f"Audible connection attempt for user {user_id}")
logger.info(f"Audible auth stored for user {user_id}")
logger.info(f"Audible library imported for user {user_id}: {import_stats}")
logger.info(f"Audible disconnected for user {user_id}")
```

**Logs Sent to Sentry** for monitoring and alerting.

---

## Testing

### Backend Testing

**1. Health Check:**
```bash
curl https://media-feed-production.up.railway.app/health
# Expected: {"status":"healthy", ...}
```

**2. Authentication:**
```bash
# Get token
curl -X POST https://media-feed-production.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
  
# Expected: {"access_token": "eyJ...", ...}
```

**3. Audible Status (Not Connected):**
```bash
curl https://media-feed-production.up.railway.app/api/audible/status \
  -H "Authorization: Bearer YOUR_TOKEN"
  
# Expected: {"connected": false, ...}
```

**4. Audible Connect (Requires Real Credentials):**
```bash
curl -X POST https://media-feed-production.up.railway.app/api/audible/connect \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@audible.com",
    "password": "yourpassword",
    "marketplace": "us"
  }'
  
# Expected: {"success": true, "books_imported": 245, ...}
```

**5. Verify Import in Database:**
```bash
# Railway CLI
railway run psql $DATABASE_URL -c "SELECT COUNT(*) FROM media WHERE type='audiobook';"
# Expected: 245 (or your audiobook count)

railway run psql $DATABASE_URL -c "SELECT * FROM audible_auth LIMIT 1;"
# Expected: 1 row with encrypted_token
```

### Frontend Testing (After Implementation)

**1. Status Display:**
- Navigate to /import
- Verify "Connect Audible" button shows
- Verify status shows "Not Connected"

**2. Connection Flow:**
- Click "Connect Audible"
- Enter credentials
- Select marketplace
- Submit form
- Verify loading state
- Verify success message
- Verify audiobook count updates

**3. Sync Flow:**
- After connection, click "Sync Now"
- Verify loading state
- Verify sync stats displayed
- Verify last sync time updates

**4. Disconnect Flow:**
- Click "Disconnect"
- Confirm dialog
- Verify status changes to "Not Connected"
- Verify audiobooks remain in library

**5. Error Handling:**
- Try connecting with wrong password
- Verify error message displayed
- Try rate limit (3 attempts quickly)
- Verify 429 error shown

---

## Usage Guide

### For End Users

#### Step 1: Connect Audible Account

1. Log into Me Feed
2. Navigate to **Import** page
3. Find "Import from Audible" section
4. Click **"Connect Audible Account"**
5. Enter your Audible email and password
6. Select your marketplace (usually "United States")
7. Click **"Connect & Import"**
8. Wait 10-30 seconds for import to complete
9. Success! Your audiobooks are now in your library

**Note:** If you have 2FA enabled:
- Append your 2FA code to your password
- Example: If password is "MyPass123" and 2FA code is "456789"
- Enter: "MyPass123456789"

#### Step 2: View Your Audiobooks

1. Navigate to **Library** page
2. Filter by "Audiobooks" (if filter exists)
3. See all your imported audiobooks with:
   - Cover art
   - Title and authors
   - Duration
   - Narrator info
   - Series information

#### Step 3: Sync New Purchases

1. Navigate to **Settings** or **Import** page
2. Find "Audible Integration" section
3. Click **"Sync Now"**
4. New audiobooks will be imported
5. See sync statistics (imported, updated, etc.)

#### Step 4: Disconnect (Optional)

1. Navigate to **Settings** page
2. Find "Audible Integration" section
3. Click **"Disconnect"**
4. Confirm disconnection
5. Your audiobooks remain in the library
6. Encrypted token is deleted

### For Developers

#### Adding Audible Support to New Features

**Check if media is audiobook:**
```typescript
if (media.type === 'audiobook') {
  // Show audiobook-specific UI
  // Display narrator, duration, etc.
}
```

**Access audiobook metadata:**
```typescript
const metadata = media.media_metadata;

console.log(metadata.authors);        // ["Author Name"]
console.log(metadata.narrators);      // ["Narrator Name"]
console.log(metadata.duration_display); // "12h 0m"
console.log(metadata.series?.title);  // "Series Name"
```

**Filter audiobooks in queries:**
```sql
SELECT * FROM media 
WHERE type = 'audiobook' 
AND user_id = $1
ORDER BY created_at DESC;
```

---

## Troubleshooting

### Connection Issues

**Problem:** "Invalid email or password"

**Solutions:**
- Verify credentials are correct
- Check if using Amazon email (not Audible email)
- Try logging into Audible website first
- Check for typos in email/password

---

**Problem:** "CAPTCHA verification required"

**Cause:** Audible detects unusual activity (new device, too many attempts)

**Solutions:**
- Wait 30-60 minutes before trying again
- Try connecting from the Audible website first
- Use manual import (Option C from strategy doc)
- Contact support if persists

---

**Problem:** "Two-factor authentication detected"

**Solution:** Append 2FA code to password
- Example: `MyPassword123456789`
- Where `456789` is your 2FA code
- Must be current code (time-based)

---

**Problem:** "Rate limit exceeded"

**Cause:** Too many connection attempts (3/hour limit)

**Solutions:**
- Wait 1 hour before trying again
- Check if you have multiple tabs open
- Verify you're using correct credentials (to avoid multiple attempts)

---

### Import Issues

**Problem:** No audiobooks imported (books_imported: 0)

**Possible Causes:**
1. Audible library is empty
2. Connection succeeded but fetch failed
3. Parsing error

**Solutions:**
- Check Audible.com to verify you have audiobooks
- Try syncing again (may have been temporary)
- Check backend logs for errors
- Contact support with job ID

---

**Problem:** Some audiobooks missing

**Possible Causes:**
1. Audible API returned partial data
2. Parsing error for specific titles
3. Duplicate detection skipped them

**Solutions:**
- Run sync again (may import missing ones)
- Check error logs for specific titles
- Verify audiobooks exist on Audible.com

---

### Sync Issues

**Problem:** "Authentication token expired"

**Cause:** Audible invalidated the stored token

**Solutions:**
- Disconnect and reconnect Audible account
- Check if you deregistered device from Amazon
- Contact support if persists

---

**Problem:** Sync takes too long

**Cause:** Large library (500+ audiobooks)

**Expected:** Up to 60 seconds for large libraries

**Note:** Progress is saved incrementally, so interruption won't lose data

---

## Appendix

### File Structure

```
Me Feed/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── audible.py                    # API endpoints
│   │   ├── services/
│   │   │   ├── audible_service.py            # Auth & library fetching
│   │   │   └── audible_parser.py             # Data mapping
│   │   ├── schemas/
│   │   │   └── audible_schemas.py            # Request/response models
│   │   ├── core/
│   │   │   └── security.py                   # Encryption functions
│   │   └── db/
│   │       └── models.py                     # AudibleAuth model
│   ├── alembic/
│   │   └── versions/
│   │       └── 008_add_audible_auth.py       # Database migration
│   └── requirements.txt                       # Dependencies
└── frontend/
    ├── components/
    │   └── audible/
    │       ├── connect-audible-modal.tsx      # Connection dialog
    │       └── audible-status-card.tsx        # Status widget
    ├── lib/
    │   └── audible-api.ts                     # API client
    └── app/
        └── (dashboard)/
            ├── import/page.tsx                # Import page integration
            └── settings/page.tsx              # Settings page integration
```

### Environment Variables

**Backend (.env):**
```bash
# Existing variables (no changes needed)
DATABASE_URL=postgresql://...
ENCRYPTION_KEY=...
JWT_PRIVATE_KEY=...
JWT_PUBLIC_KEY=...
```

**Frontend (.env.local):**
```bash
# Existing variables (no changes needed)
NEXT_PUBLIC_API_URL=https://media-feed-production.up.railway.app
```

**Note:** No Audible-specific environment variables required! The `audible` library handles authentication internally.

### Deployment Checklist

**Backend Deployment (✅ Complete):**
- [x] Install `audible==0.10.0`
- [x] Run migration `008_add_audible_auth.py`
- [x] Verify `audible_auth` table created
- [x] Test `/api/audible/status` endpoint
- [x] Test `/api/audible/connect` with real credentials
- [x] Verify encryption works
- [x] Verify rate limiting works

**Frontend Deployment (⏳ In Progress):**
- [ ] Build `ConnectAudibleModal` component
- [ ] Build `AudibleStatusCard` component
- [ ] Create `audible-api.ts` client
- [ ] Integrate into Import page
- [ ] Integrate into Settings page
- [ ] Test end-to-end flow
- [ ] Deploy to Railway

### Resources

- **Audible Python Library:** https://audible.readthedocs.io/
- **API Documentation:** This file (API Endpoints section)
- **Strategy Document:** `AUDIBLE_INTEGRATION_STRATEGY.md`
- **Backend Implementation:** `backend/app/api/audible.py`
- **Security Details:** `backend/app/core/security.py`

---

**Document Version:** 1.0  
**Last Updated:** November 11, 2025  
**Status:** Backend Complete ✅ | Frontend In Progress ⏳  
**Total Implementation Time:** ~4 hours  
**Lines of Code:** 1,340+

# Audible Integration Strategy

**Project:** Me Feed - Media Tracker  
**Feature:** Audible Library Import  
**Created:** November 11, 2025  
**Status:** In Development - Starting with Option A  

---

## Overview

This document outlines three approaches for integrating Audible audiobook library data into Me Feed. Each option balances security, user experience, and technical complexity differently.

**Context:**
- Audible has NO public OAuth API
- Only private/internal API exists (used by mobile apps)
- Requires Amazon/Audible credentials for authentication
- Python library available: `audible` (https://audible.readthedocs.io/)

---

## Option A: In-App Credential Authentication (CURRENT IMPLEMENTATION)

**Status:** ✅ **SELECTED FOR INITIAL RELEASE**

### User Flow

1. User logs into Me Feed (existing auth)
2. Navigates to Settings or Import page
3. Clicks "Connect Audible Account"
4. Modal opens with form:
   - Audible Email
   - Audible Password
   - Country/Marketplace selector (US, UK, DE, etc.)
   - Checkbox: "I authorize Me Feed to access my Audible library"
5. Backend authenticates with Audible API
6. Fetches library data (title, author, narrator, duration, progress, etc.)
7. Imports audiobooks to database
8. **Stores encrypted auth token** (NOT password)
9. Shows success message with count (e.g., "245 audiobooks imported")
10. User can disconnect/revoke at any time

### Technical Implementation

#### Backend Components

**New Files:**
- `backend/app/services/audible_service.py` - Audible API client wrapper
- `backend/app/services/audible_parser.py` - Parse Audible library data
- `backend/app/api/audible_import.py` - API endpoints
- `backend/app/schemas/audible_schemas.py` - Pydantic models

**Modified Files:**
- `backend/app/schemas/import_schemas.py` - Add `AUDIBLE_API` to ImportSource
- `backend/app/db/models.py` - Add `audible_auth` table
- `backend/requirements.txt` - Add `audible` library

**Database Schema:**

```sql
CREATE TABLE audible_auth (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    encrypted_token TEXT NOT NULL,  -- AES-256 encrypted auth token
    marketplace VARCHAR(10) NOT NULL,  -- us, uk, de, etc.
    device_name VARCHAR(255),
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id)  -- One Audible account per user
);

-- Index for quick lookup
CREATE INDEX idx_audible_auth_user ON audible_auth(user_id);
```

**API Endpoints:**

```
POST /api/audible/connect
  - Body: { email, password, marketplace }
  - Authenticates with Audible
  - Stores encrypted token
  - Returns: { success, device_name, books_count }

POST /api/audible/sync
  - Fetches latest library data
  - Updates existing books
  - Imports new purchases
  - Returns: { imported, updated, total }

DELETE /api/audible/disconnect
  - Deregisters device with Audible
  - Deletes encrypted token
  - Returns: { success }

GET /api/audible/status
  - Returns: { connected, last_sync, books_count }
```

#### Security Measures

**1. Password Handling:**
```python
# Password is NEVER stored
def authenticate_audible(email: str, password: str, marketplace: str):
    # Use password only for authentication
    auth = audible.Authenticator.from_login(email, password, locale=marketplace)
    
    # Get auth token (this is what we store)
    token = auth.to_dict()
    
    # Password is now out of scope and garbage collected
    # Only token remains in memory
    
    return token
```

**2. Token Encryption:**
```python
from cryptography.fernet import Fernet

# Each user has unique encryption key derived from master key + user_id
def get_user_encryption_key(user_id: UUID) -> bytes:
    master_key = os.getenv('AUDIBLE_ENCRYPTION_KEY')
    user_salt = str(user_id).encode()
    return hashlib.pbkdf2_hmac('sha256', master_key.encode(), user_salt, 100000)

def encrypt_token(token: dict, user_id: UUID) -> str:
    key = get_user_encryption_key(user_id)
    fernet = Fernet(key)
    token_json = json.dumps(token)
    encrypted = fernet.encrypt(token_json.encode())
    return base64.b64encode(encrypted).decode()

def decrypt_token(encrypted_token: str, user_id: UUID) -> dict:
    key = get_user_encryption_key(user_id)
    fernet = Fernet(key)
    decoded = base64.b64decode(encrypted_token.encode())
    decrypted = fernet.decrypt(decoded)
    return json.loads(decrypted.decode())
```

**3. Token Storage:**
- Encrypted with AES-256-GCM
- User-specific encryption key (derived from master key + user_id)
- Master key stored in environment variable (never committed)
- Token can be revoked by user at any time

**4. Device Registration:**
- Each connection creates a "virtual device" on Amazon account
- Visible in user's Amazon device list as "Me Feed - Web"
- User can deregister from Amazon if needed
- App can deregister programmatically

**5. Audit Logging:**
```python
# Log all Audible auth events
audit_log.info("audible_connect", user_id=user.id, marketplace=marketplace)
audit_log.info("audible_sync", user_id=user.id, books_imported=count)
audit_log.info("audible_disconnect", user_id=user.id)
```

**6. Rate Limiting:**
```python
# Prevent brute force attacks
@limiter.limit("3 per hour")  # Only 3 connection attempts per hour
@router.post("/api/audible/connect")
async def connect_audible(...):
    pass

@limiter.limit("10 per day")  # Sync limit
@router.post("/api/audible/sync")
async def sync_audible(...):
    pass
```

**7. HTTPS Only:**
- All credentials transmitted over HTTPS
- No plaintext transmission

**8. GDPR Compliance:**
- User can delete all Audible data
- Export their Audible library data (data portability)
- Clear privacy policy about credential handling
- Token deletion on account deletion

#### Frontend Components

**New Components:**
- `frontend/components/audible/connect-audible-modal.tsx` - Connection modal
- `frontend/components/audible/audible-status-card.tsx` - Connection status widget
- `frontend/lib/audible-api.ts` - API client

**Modified Components:**
- `frontend/app/(dashboard)/import/page.tsx` - Add Audible import option
- `frontend/app/(dashboard)/settings/page.tsx` - Add Audible connection management

**UI Flow:**

```tsx
// Import Page
<Card>
  <CardTitle>Import Audiobooks from Audible</CardTitle>
  <Button onClick={openConnectModal}>Connect Audible Account</Button>
</Card>

// Connect Modal
<Modal>
  <Input label="Audible Email" type="email" />
  <Input label="Audible Password" type="password" />
  <Select label="Marketplace">
    <option value="us">United States</option>
    <option value="uk">United Kingdom</option>
    <option value="de">Germany</option>
    {/* ... other marketplaces */}
  </Select>
  <Checkbox>I authorize Me Feed to access my Audible library</Checkbox>
  <Button>Connect & Import</Button>
</Modal>

// Settings Page - Audible Section
<Card>
  <CardTitle>Audible Connection</CardTitle>
  {connected ? (
    <>
      <Badge>Connected</Badge>
      <Text>Last synced: {lastSync}</Text>
      <Text>{booksCount} audiobooks imported</Text>
      <Button onClick={syncNow}>Sync Now</Button>
      <Button variant="destructive" onClick={disconnect}>Disconnect</Button>
    </>
  ) : (
    <Button onClick={openConnectModal}>Connect Audible</Button>
  )}
</Card>
```

#### Data Mapping

**Audible API Response → Media Table:**

```python
def map_audible_to_media(audible_item: dict) -> Media:
    """
    Map Audible library item to Media model
    
    Audible fields available:
    - asin: Audible's unique ID
    - title: Book title
    - authors: List of author objects
    - narrators: List of narrator objects
    - runtime_length_min: Duration in minutes
    - release_date: Publication date
    - purchase_date: When user bought it
    - percent_complete: Listening progress (0-100)
    - series: Series information (if part of series)
    - rating: Audible rating
    - cover_url: Book cover image
    - is_finished: Boolean
    """
    
    return Media(
        title=audible_item['title'],
        type='audiobook',
        release_date=parse_date(audible_item.get('release_date')),
        tmdb_id=None,  # Audible doesn't use TMDB
        imdb_id=None,
        platform='audible',
        platform_ids={'asin': audible_item['asin']},
        media_metadata={
            'authors': [a['name'] for a in audible_item.get('authors', [])],
            'narrators': [n['name'] for n in audible_item.get('narrators', [])],
            'duration_minutes': audible_item.get('runtime_length_min'),
            'series': audible_item.get('series', {}).get('title'),
            'series_sequence': audible_item.get('series', {}).get('sequence'),
            'rating': audible_item.get('rating'),
            'cover_url': audible_item.get('cover_url'),
            'audible_url': f"https://www.audible.com/pd/{audible_item['asin']}"
        }
    )

def map_audible_to_user_media(user_id: UUID, media_id: UUID, audible_item: dict) -> UserMedia:
    """Map Audible item to UserMedia (consumption tracking)"""
    
    return UserMedia(
        user_id=user_id,
        media_id=media_id,
        platform='audible',
        consumed_at=parse_date(audible_item.get('purchase_date')),
        status='finished' if audible_item.get('is_finished') else 'in_progress',
        imported_from='audible_api',
        raw_import_data={
            'asin': audible_item['asin'],
            'percent_complete': audible_item.get('percent_complete', 0),
            'purchase_date': audible_item.get('purchase_date'),
            'is_finished': audible_item.get('is_finished', False)
        }
    )
```

#### Error Handling

```python
class AudibleAuthError(Exception):
    """Raised when Audible authentication fails"""
    pass

class AudibleCaptchaRequiredError(AudibleAuthError):
    """Raised when Audible requires CAPTCHA (high security mode)"""
    pass

class AudibleTwoFactorRequiredError(AudibleAuthError):
    """Raised when 2FA code needed"""
    pass

# In API endpoint
try:
    await audible_service.connect(email, password, marketplace)
except AudibleCaptchaRequiredError:
    return {"error": "CAPTCHA required. Please try again later or use manual import."}
except AudibleTwoFactorRequiredError:
    return {"error": "2FA detected. Please append your 2FA code to your password."}
except AudibleAuthError as e:
    return {"error": f"Authentication failed: {str(e)}"}
```

#### Testing Strategy

**Unit Tests:**
- Token encryption/decryption
- Data mapping (Audible → Media)
- Error handling

**Integration Tests:**
- Full authentication flow (with test account)
- Library import
- Sync functionality
- Disconnect/revoke

**Security Tests:**
- Token encryption strength
- Password not logged
- Token not exposed in API responses
- Rate limiting works

### Pros & Cons

**Advantages:**
- ✅ True web service experience (one-click)
- ✅ No manual exports needed
- ✅ Can auto-sync new purchases
- ✅ Get listening progress automatically
- ✅ Standard pattern (used by Plex, banking apps, etc.)
- ✅ Rich data (progress, ratings, series info)
- ✅ Future features: progress sync, recommendations

**Disadvantages:**
- ⚠️ Security responsibility (credentials handling)
- ⚠️ Users must trust app with credentials
- ⚠️ 2FA complexity (users append code to password)
- ⚠️ CAPTCHA can block automation
- ⚠️ Audible may change API (unofficial)

### Compliance & Legal

**Privacy Policy Addition:**
```
Audible Integration:
- When you connect your Audible account, we temporarily use your credentials 
  to authenticate with Audible's service.
- Your password is never stored. We only store an encrypted authentication token.
- This token allows us to fetch your audiobook library and sync updates.
- You can disconnect at any time, which immediately deletes the token.
- We do not share your Audible data with third parties.
- Your Audible connection creates a "virtual device" visible in your Amazon 
  account's device list.
```

**Terms of Service Addition:**
```
Third-Party Service Integration:
- By connecting third-party services (Audible, Netflix, etc.), you authorize 
  Me Feed to access data from those services on your behalf.
- You are responsible for maintaining the security of your third-party credentials.
- Me Feed is not responsible for changes to third-party APIs or service 
  availability.
- Audible is a trademark of Amazon. Me Feed is not affiliated with or 
  endorsed by Amazon or Audible.
```

### Implementation Timeline

**Phase 1: Core Functionality (3-4 hours)**
- ✅ Install `audible` library
- ✅ Create Audible service with authentication
- ✅ Create token encryption utilities
- ✅ Create database migration for `audible_auth` table
- ✅ Create parser to map Audible → Media
- ✅ Create API endpoints
- ✅ Add frontend connection modal
- ✅ Test with real account

**Phase 2: Polish (1-2 hours)**
- Progress indicators during import
- Better error messages
- 2FA code handling UI
- Marketplace auto-detection
- Connection status widget

**Phase 3: Advanced Features (Future)**
- Auto-sync on schedule (daily/weekly)
- Progress sync (update listening progress from Audible)
- Audiobook recommendations based on library
- Series completion tracking
- Narrator filtering

---

## Option B: Browser Extension Helper

**Status:** 📋 **DOCUMENTED FOR FUTURE**

### Concept

A browser extension that authenticates with Audible client-side, fetches library data in the browser, and sends it to Me Feed backend via API.

### User Flow

1. User installs "Me Feed Audible Connector" Chrome/Firefox extension
2. Clicks extension icon → "Connect to Audible"
3. Extension opens Audible login in new tab (user logs in normally)
4. Once logged in, extension reads auth cookies
5. Extension fetches library data using Audible's internal API
6. Extension prompts: "Send 245 audiobooks to Me Feed?"
7. User confirms → Extension posts data to `POST /api/audible/import-from-extension`
8. Backend validates and imports data

### Technical Architecture

**Extension Components:**
- Manifest V3 extension (Chrome/Firefox compatible)
- Content script: Injects into audible.com to read cookies
- Background worker: Fetches library data
- Popup UI: Shows connection status and import button

**Backend:**
- New endpoint: `POST /api/audible/import-from-extension`
- Validates data structure
- Imports to database
- No credential storage

**Extension Code Structure:**
```
audible-connector-extension/
├── manifest.json
├── background.js (service worker)
├── content.js (inject into audible.com)
├── popup.html
├── popup.js
└── icons/
```

### Pros & Cons

**Advantages:**
- ✅ Zero credential storage on server
- ✅ No security liability
- ✅ Uses official Audible website (no unofficial API)
- ✅ Respects Audible's auth flow
- ✅ User stays in control

**Disadvantages:**
- ⚠️ Requires extension installation
- ⚠️ More complex user setup
- ⚠️ Extension needs updates (Chrome/Firefox)
- ⚠️ Can't auto-sync (user must trigger)
- ⚠️ Browser-specific (need Chrome + Firefox versions)

### When to Implement

- After Option A is stable
- If users express security concerns about Option A
- If Audible starts blocking Option A's API access
- For enterprise users with strict security policies

---

## Option C: Manual Export/Upload

**Status:** 📋 **DOCUMENTED FOR FUTURE**

### Concept

User exports their Audible library using a standalone tool, then uploads the file to Me Feed (like Netflix CSV).

### User Flow

**Method 1: Python Script (Recommended)**
1. User downloads `audible_export.py` from Me Feed
2. Runs: `python audible_export.py`
3. Enters Audible credentials (local, never sent to Me Feed)
4. Script generates `audible_library.json`
5. User uploads JSON to Me Feed import page

**Method 2: Third-Party Tools**
1. User installs Audible Library Extractor (Chrome extension)
2. Exports library as CSV
3. Uploads to Me Feed

**Method 3: OpenAudible**
1. User installs OpenAudible desktop app
2. Exports library
3. Uploads to Me Feed

### Technical Implementation

**Export Script (`audible_export.py`):**
```python
#!/usr/bin/env python3
"""
Audible Library Export Tool for Me Feed
Runs locally on your machine. No data sent to Me Feed during export.
"""
import audible
import json
from getpass import getpass

def export_audible_library():
    print("=== Me Feed - Audible Library Export ===")
    print("Your credentials are used locally only.\n")
    
    email = input("Audible Email: ")
    password = getpass("Audible Password: ")
    marketplace = input("Marketplace (us, uk, de, etc.): ")
    
    print("\nAuthenticating with Audible...")
    auth = audible.Authenticator.from_login(
        email, password, locale=marketplace, with_username=False
    )
    
    print("Fetching library...")
    with audible.Client(auth=auth) as client:
        library = client.get(
            "1.0/library",
            num_results=1000,
            response_groups="product_desc,product_attrs,media,series,rating"
        )
    
    # Save to file
    output_file = "audible_library.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(library, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Exported {len(library['items'])} audiobooks to {output_file}")
    print(f"✓ Upload this file to Me Feed: https://your-app.com/import")
    
    # Cleanup
    auth.deregister_device()
    print("✓ Temporary device deregistered from Amazon")

if __name__ == "__main__":
    export_audible_library()
```

**Backend:**
- New parser: `AudibleJSONParser`
- Endpoint: `POST /api/import/audible-json`
- Handles JSON format from export script

### Pros & Cons

**Advantages:**
- ✅ Zero security concerns (no credentials in web app)
- ✅ Simple backend (just parse uploaded file)
- ✅ Works for all users (no browser/device restrictions)
- ✅ User maintains full control

**Disadvantages:**
- ❌ Manual process (not true "web service")
- ❌ Requires Python installation (or third-party tool)
- ❌ No auto-sync
- ❌ Extra steps for user

### When to Implement

- As fallback if Option A fails (CAPTCHA, 2FA issues)
- For users who prefer manual import
- For one-time imports (users who don't need sync)
- For developers/technical users

---

## Comparison Matrix

| Feature | Option A (In-App Auth) | Option B (Extension) | Option C (Manual Upload) |
|---------|------------------------|----------------------|--------------------------|
| **User Experience** | ⭐⭐⭐⭐⭐ One-click | ⭐⭐⭐ Install + click | ⭐⭐ Multi-step |
| **Security (Server)** | ⭐⭐⭐ Encrypted token | ⭐⭐⭐⭐⭐ No credentials | ⭐⭐⭐⭐⭐ No credentials |
| **Security (User)** | ⭐⭐⭐ Trust required | ⭐⭐⭐⭐ Local only | ⭐⭐⭐⭐⭐ Local only |
| **Auto-Sync** | ✅ Yes | ❌ Manual | ❌ Manual |
| **Development Time** | 3-4 hours | 6-8 hours | 1-2 hours |
| **Maintenance** | Low | Medium (extension) | Low |
| **Works on Mobile** | ✅ Yes | ❌ Desktop only | ⚠️ Needs app |
| **GDPR Compliant** | ✅ With policy | ✅ Yes | ✅ Yes |
| **Audible API Risk** | ⚠️ Unofficial API | ⚠️ Uses web scraping | ⚠️ Unofficial API |

---

## Recommendations

### Phase 1: Launch (Now)
**Implement Option A** - Best balance of UX and feasibility
- Core feature for web service
- Standard industry pattern
- Enables future features

### Phase 2: Expansion (3-6 months)
**Add Option C** - Manual export as fallback
- For users who hit 2FA/CAPTCHA issues
- For privacy-conscious users
- Simple to implement

### Phase 3: Enterprise (6-12 months)
**Add Option B** - Browser extension
- For enterprise customers with security requirements
- For users in regions where Option A is blocked
- Differentiator vs competitors

---

## Success Metrics

**For Option A:**
- Connection success rate > 90%
- Average import time < 30 seconds
- User retention (connected after 30 days) > 70%
- Support tickets related to Audible < 5%
- Zero security incidents

**Feature Adoption:**
- % of users who connect Audible account
- % of users who use auto-sync
- % of users who disconnect vs. stay connected
- Average audiobooks per user

---

## Risk Mitigation

### Risk: Audible Changes API
**Mitigation:**
- Monitor `audible` library for updates
- Implement fallback to Option C
- Clear communication to users if service disrupted

### Risk: Security Breach
**Mitigation:**
- Token encryption with user-specific keys
- Regular security audits
- Rate limiting
- Audit logging
- Immediate token revocation capability

### Risk: Legal Action from Audible/Amazon
**Mitigation:**
- Clear disclaimer: "Not affiliated with Amazon"
- Terms of service: Users authorize access
- Respect rate limits (no abuse)
- Personal use only (no commercial scraping)

### Risk: Low Adoption (Users Don't Trust)
**Mitigation:**
- Transparent security documentation (this file)
- Open-source encryption code
- Allow users to review what data is stored
- Provide Option C as alternative

---

## Future Enhancements

### Listening Progress Sync (Option A only)
- Periodically fetch listening progress from Audible
- Update UserMedia.percent_complete
- Show progress bars in library
- Mark as "finished" when 95%+ complete

### Series Tracking
- Detect audiobook series from Audible metadata
- Show "Next in series" recommendations
- Notify when new book in series releases
- Track series completion percentage

### Narrator Filtering
- Extract narrator data from Audible
- Filter library by favorite narrators
- Recommendations based on narrator preferences

### Wishlist Integration
- Fetch Audible wishlist
- Track price drops
- Notify when wishlist item goes on sale

### Social Features
- Share favorite audiobooks
- See what friends are listening to
- Book clubs / shared listening progress

---

## Documentation Status

- ✅ All options documented
- ✅ Security measures defined
- ✅ Implementation plan for Option A
- ✅ Future roadmap defined
- ✅ Risk mitigation strategies
- 🔄 Implementation in progress (Option A)

**Next Steps:**
1. Implement Option A (3-4 hours)
2. Test with real Audible account
3. Update privacy policy
4. Deploy to production
5. Monitor adoption and feedback

**Last Updated:** November 11, 2025  
**Document Version:** 1.0

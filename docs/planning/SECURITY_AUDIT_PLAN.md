# Security Audit Plan - Post-Audible Integration

**Created:** November 15, 2025  
**Target Execution:** After Audible Extension reaches production-ready state  
**Estimated Duration:** 6-8 hours  
**Previous Audit:** November 11, 2025 (see SECURITY_AUDIT_NOV_11_2025.md)

---

## Audit Trigger Conditions

Execute security audit when **ALL** of the following are met:

✅ **1. Audible Extension Stable**
- Pagination working (scrapes all books, not just 20)
- Series grouping implemented
- Category filter functional
- No critical bugs in extension

✅ **2. Core Features Complete**
- Basic import/export working
- User authentication solid
- Token management stable

✅ **3. Production Usage Ready**
- Extension tested with 100+ book libraries
- No data loss incidents
- Performance acceptable

**Current Status:** ❌ Not ready - Audible MVP has critical limitations

---

## Scope: New Attack Surface from Audible Integration

### 1. Browser Extension Security

#### 1.1 Manifest & Permissions Review
**Risk Level:** HIGH

**Check:**
- [ ] Review all `host_permissions` - are they minimal?
- [ ] Verify `content_scripts` only run on necessary domains
- [ ] Check for overly broad permissions (tabs, cookies, etc.)
- [ ] Validate Content Security Policy in manifest

**Current Concerns:**
```json
"host_permissions": [
  "https://*.audible.com/*",      // Broad - necessary?
  "https://*.audible.de/*",       // 10 marketplaces
  "https://*.railway.app/*",      // Production only?
  "http://localhost:3000/*"       // Dev only - remove for prod?
]
```

**Questions:**
- Can we restrict to specific Railway subdomain?
- Should localhost be removed in production build?
- Do we need ALL Audible marketplaces or just user's active ones?

#### 1.2 Data Exfiltration Risk
**Risk Level:** CRITICAL

**Attack Vectors:**
1. Malicious update could steal Audible cookies
2. Extension could scrape beyond library (wishlist, payment info, etc.)
3. Token could be exfiltrated to third-party servers

**Mitigations to Verify:**
- [ ] Extension only accesses `/library*` pages (check manifest matches)
- [ ] No network requests to non-Me Feed domains
- [ ] Token only sent to verified backend URL
- [ ] No analytics/tracking code in extension
- [ ] Content script isolated from page JavaScript

**Code Review Checklist:**
- [ ] Search for `fetch()` calls - verify all go to BACKEND_URL
- [ ] Check for `XMLHttpRequest` usage
- [ ] Look for `eval()` or `new Function()` (XSS risk)
- [ ] Verify no inline scripts in manifest
- [ ] Check for external script loading

#### 1.3 Token Handling in Extension
**Risk Level:** HIGH

**Current Implementation:**
```javascript
// mefeed-token-grabber.js
const token = localStorage.getItem('access_token');
chrome.runtime.sendMessage({ action: 'autoSaveToken', token });

// background.js
await chrome.storage.local.set({ authToken: token });
```

**Security Questions:**
- [ ] Is chrome.storage.local encrypted? (NO - needs encryption)
- [ ] Can other extensions read this storage? (YES if they request permission)
- [ ] Token validation before storage? (NO - accepts any string)
- [ ] Token expiration checked? (NO - stored until cleared)

**Recommended Fixes:**
1. Validate token format (JWT regex check)
2. Store token expiration timestamp
3. Clear token on expiry
4. Add warning if token leaked to clipboard

#### 1.4 Content Script Injection Safety
**Risk Level:** MEDIUM

**Check:**
- [ ] Content scripts don't modify Audible page DOM (read-only)
- [ ] No execution of page scripts (isolated world)
- [ ] Sanitize all scraped data before sending to backend
- [ ] Handle malicious book titles (XSS in metadata)

**Test Cases:**
- Book title with `<script>alert(1)</script>`
- Author name with SQL injection attempt
- ASIN with path traversal `../../etc/passwd`
- Cover URL pointing to malicious site

---

### 2. Backend API Security

#### 2.1 Extension Endpoints Authentication
**Risk Level:** HIGH

**Endpoints to Audit:**
- `POST /api/audible/import-from-extension`
- `GET /api/audible/extension/status`

**Current Security:**
```python
@router.post("/import-from-extension")
@limiter.limit("20/hour")
async def import_from_extension(
    current_user: User = Depends(get_current_user),
    ...
)
```

**Checks:**
- [✅] JWT authentication required (get_current_user)
- [✅] Rate limiting (20/hour) - adequate?
- [❌] Input validation on book data? (NEEDS REVIEW)
- [❌] File size limits on request? (NEEDS LIMIT)
- [❌] Sanitization of metadata? (NEEDS REVIEW)

**Questions:**
- Is 20/hour rate limit sufficient? (User may have 500+ books)
- What if malicious extension sends 1000 fake books?
- Validate ASIN format before database insert?

#### 2.2 Origin Validation Bypass
**Risk Level:** MEDIUM

**Current Code:**
```python
# middleware.py
extension_paths = [
    '/api/audible/import-from-extension',
    '/api/audible/extension/status'
]
if any(request.url.path.startswith(path) for path in extension_paths):
    return await call_next(request)  # SKIP ORIGIN CHECK
```

**Security Implications:**
- Extension endpoints bypass CSRF protection
- Relies ONLY on JWT auth
- Any origin can call if they have valid token

**Questions:**
- Is this acceptable given JWT requirement?
- Should we whitelist chrome-extension:// origins?
- Document this exception in security policy?

#### 2.3 Input Validation
**Risk Level:** HIGH

**Review:**
```python
class AudibleBookFromExtension(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    authors: List[str] = Field(default_factory=list)
    asin: str = Field(..., min_length=10, max_length=20)
    ...
```

**Checks:**
- [✅] Length limits on title (500 chars)
- [✅] ASIN length validated (10-20 chars)
- [❌] ASIN format validation (should be alphanumeric)
- [❌] URL validation on cover_url (could be file://, javascript:, etc.)
- [❌] Array size limits on authors/narrators (DOS risk)

**Recommended Additions:**
```python
from pydantic import validator, HttpUrl

@validator('asin')
def validate_asin_format(cls, v):
    if not re.match(r'^[A-Z0-9]{10,20}$', v):
        raise ValueError('Invalid ASIN format')
    return v

@validator('authors', 'narrators')
def limit_array_size(cls, v):
    if len(v) > 20:
        raise ValueError('Too many items')
    return v[:20]

cover_url: Optional[HttpUrl] = None  # Pydantic validates HTTP/HTTPS only
```

---

### 3. Database Security

#### 3.1 SQL Injection via Parser
**Risk Level:** MEDIUM

**Review:**
```python
# audible_parser.py
media = await self._find_or_create_media(item)
```

**Checks:**
- [✅] Using SQLAlchemy ORM (parameterized queries)
- [✅] No raw SQL in parser
- [❌] Metadata stored as JSON - injection in JSON keys?

#### 3.2 Data Integrity
**Risk Level:** LOW

**Questions:**
- Can extension overwrite existing books from CSV import?
- Can malicious data corrupt other users' libraries?
- Is user_id properly isolated in all queries?

**Test:**
```python
# Verify user isolation
# User A shouldn't be able to modify User B's audiobooks
# even with valid token
```

---

### 4. Token Management

#### 4.1 JWT Expiration
**Risk Level:** MEDIUM

**Recent Change:**
```python
ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days (was 15 minutes)
```

**Security Review:**
- [❓] Is 7 days too long for access token?
- [❓] Should extension use refresh tokens instead?
- [❓] Token revocation mechanism exists?
- [❓] Old tokens cleaned up from storage?

**Recommendation:**
- Access token: 1 hour
- Refresh token: 7 days
- Extension auto-refreshes token hourly

#### 4.2 Token Storage Security
**Risk Level:** HIGH

**Current:**
- Frontend: localStorage (unencrypted)
- Extension: chrome.storage.local (unencrypted)
- Backend: Not stored (stateless JWT)

**Concerns:**
- XSS can steal localStorage tokens
- Chrome extension can read chrome.storage
- No encryption at rest

**Recommended:**
1. Consider httpOnly cookies for web app
2. Encrypt tokens in extension storage
3. Add token binding (IP/User-Agent validation)

---

### 5. Privacy & Compliance

#### 5.1 Data Collection
**What Extension Collects:**
- Book titles, authors, narrators
- Reading history (ASINs)
- Audible marketplace (infers user location)
- Me Feed auth token

**Questions:**
- [ ] Is this documented in privacy policy?
- [ ] User consent obtained?
- [ ] GDPR compliance if EU users?
- [ ] Data retention policy defined?

#### 5.2 Third-Party Data Sharing
**Check:**
- [ ] Does extension send data to any non-Me Feed servers?
- [ ] Are book covers loaded from Amazon CDN?
- [ ] Any analytics or tracking?
- [ ] Sentry error reporting - what data is included?

---

## Audit Methodology

### Phase 1: Automated Scans (2 hours)

**Tools:**
1. **npm audit** - Check extension dependencies
2. **Snyk** - Scan for known vulnerabilities
3. **ESLint** - Security rules for JavaScript
4. **Bandit** - Python security linter
5. **Safety** - Python dependency check

**Commands:**
```bash
# Extension
cd extension
npm audit --production
npx snyk test

# Backend
cd backend
bandit -r app/
safety check
```

### Phase 2: Manual Code Review (3 hours)

**Focus Areas:**
1. Extension manifest permissions
2. Token handling in 3 locations (frontend, extension, backend)
3. Input validation in extension endpoint
4. CORS/origin handling for extension
5. Parser SQL injection risks

**Review Checklist:**
- [ ] All `TODO:` and `FIXME:` comments
- [ ] All `eval()`, `exec()`, `new Function()` usage
- [ ] All `fetch()` and API calls
- [ ] All user input handling
- [ ] All authentication checks
- [ ] All database queries

### Phase 3: Penetration Testing (2 hours)

**Attack Scenarios:**
1. **Token Theft**
   - Extract token from chrome.storage
   - Use stolen token from different IP
   - Replay old token after user logs out

2. **Data Injection**
   - Send malicious book titles with XSS
   - Overflow arrays (1000 authors)
   - Invalid ASINs
   - Malicious cover URLs

3. **Rate Limit Bypass**
   - Multiple extension instances
   - Rapid requests from different tabs
   - DOS with large payloads

4. **Origin Spoofing**
   - Call extension endpoints from web page
   - CSRF attack with valid token
   - Cross-origin token theft

### Phase 4: Documentation (1 hour)

**Deliverables:**
1. Updated SECURITY_FINDINGS.md
2. Threat model diagram
3. Mitigation action items
4. Security best practices doc for extension users

---

## Success Criteria

✅ **No Critical Vulnerabilities** - All critical issues fixed before production  
✅ **Medium Issues Documented** - Mitigation plan for medium-risk items  
✅ **Low Issues Tracked** - Backlog items for future sprints  
✅ **Security Documentation Complete** - Users informed of risks  
✅ **Audit Report Published** - Findings documented  

---

## Post-Audit Actions

### Immediate (Critical Fixes)
1. Fix any authentication bypasses
2. Patch SQL injection vulnerabilities
3. Fix XSS in book metadata
4. Secure token storage

### Short-Term (2 weeks)
1. Implement input validation improvements
2. Add token encryption in extension
3. Improve rate limiting
4. Add security headers

### Long-Term (Ongoing)
1. Dependency updates
2. Regular security scans
3. Bug bounty program?
4. Third-party audit

---

## Dependencies

**Before Audit Can Start:**
- [❌] Audible pagination implemented (critical feature)
- [❌] Series grouping working (core feature)
- [❌] Extension tested with large libraries (stability)
- [❌] No critical bugs in issue tracker (MVP → stable)

**Estimated Timeline:**
- Audible features complete: 8-12 hours (1-2 sessions)
- **Then** security audit: 6-8 hours (1 session)

**Total:** ~16-20 hours from current state to security-audited Audible integration

---

## Notes

- Previous audit (Nov 11) covered session management bug
- This audit focuses on NEW attack surface from browser extension
- Extension security is different from web app security
- Chrome Web Store requires security review anyway
- Consider hiring professional pen-tester for production release

---

## References

- SECURITY_AUDIT_NOV_11_2025.md (previous audit)
- SECURITY_FINDINGS.md (current known issues)
- AUDIBLE_INTEGRATION_PIVOT.md (architecture decision)
- Chrome Extension Security Best Practices: https://developer.chrome.com/docs/extensions/mv3/security/

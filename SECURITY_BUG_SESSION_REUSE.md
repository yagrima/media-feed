# CRITICAL SECURITY BUG: Session Token Reuse

**Discovered:** November 9, 2025  
**Fixed:** November 11, 2025  
**Severity:** 🔴 CRITICAL  
**Status:** ✅ FIXED - Verified in production  
**Fix Commit:** a1dc986

---

## 🚨 Issue Summary

Users who logout and then register a new account are logged into their PREVIOUS account instead of the newly created account. This is a critical authentication vulnerability.

---

## 🔍 Detailed Description

### What Happens:
1. User A logs in → Gets JWT tokens
2. User A logs out → Tokens should be invalidated
3. User registers NEW account (User B) → Should get new tokens
4. **BUG:** User is logged in as User A (not User B)

### Security Implications:
- ❌ Session tokens persist after logout
- ❌ Cross-account access possible
- ❌ Data privacy violation
- ❌ Authentication boundary broken

---

## ✅ RESOLUTION

### Root Cause Identified
Login and register pages were bypassing the AuthContext and calling API endpoints directly:
- `register/page.tsx` used `authApi.register()` + `tokenManager.setTokens()` directly
- `login/page.tsx` used `authApi.login()` + `tokenManager.setTokens()` directly
- **AuthProvider was missing** from the Providers component tree
- AuthContext had correct `clearTokens()` logic in both `login()` and `register()` methods, but these were never called

### Fix Implemented (Commit a1dc986)
1. **Modified register page** to use `useAuth().register()` hook
2. **Modified login page** to use `useAuth().login()` hook
3. **Added AuthProvider** to `components/providers.tsx`
4. Now AuthContext's `clearTokens()` is called BEFORE every login/register operation

### Files Changed
- `frontend/app/(auth)/login/page.tsx` - Use AuthContext instead of direct API
- `frontend/app/(auth)/register/page.tsx` - Use AuthContext instead of direct API
- `frontend/components/providers.tsx` - Added AuthProvider wrapper

### Verification Test (Production)
**Test Scenario:** Logout → Register New User → Verify Identity

**Test Results (November 11, 2025):**
```
Step 1: Register User A (security-test-userA-190022@example.com)
        User ID: d66dab8c-5948-415c-af86-4c954394d3dd
        ✓ Registered successfully

Step 2: Verify User A via /api/auth/me
        ✓ Confirmed: security-test-userA-190022@example.com

Step 3: Logout User A
        ✓ Logged out successfully

Step 4: Register User B (security-test-userB-190024@example.com)
        User ID: 57ad5145-49bb-48f3-a96b-0ece991410b1
        ✓ Registered successfully

Step 5: CRITICAL TEST - Verify /api/auth/me
        ✓ SUCCESS: Returns security-test-userB-190024@example.com
        ✓ User B ID matches (57ad5145...)
        ✅ BUG-005 IS FIXED!
```

**Conclusion:** Cross-account access prevented. Users are correctly authenticated as new accounts after logout and registration.

---

## 🔬 Original Investigation Checklist

### Frontend Investigation:
- [ ] Check if `localStorage` is cleared on logout
- [ ] Check if `sessionStorage` is cleared on logout
- [ ] Verify auth context clears tokens on logout
- [ ] Check if registration endpoint response includes new tokens
- [ ] Verify tokens are replaced (not appended) on new login

**Files to Check:**
- `frontend/lib/auth/auth-context.tsx` - Logout logic
- `frontend/lib/api/auth.ts` - Registration endpoint
- `frontend/app/auth/register/page.tsx` - Registration flow

### Backend Investigation:
- [ ] Verify logout endpoint invalidates refresh tokens in database
- [ ] Check if registration endpoint returns proper auth tokens
- [ ] Verify user session table is updated correctly
- [ ] Check if refresh tokens are unique per user

**Files to Check:**
- `backend/app/api/auth.py` - Logout and registration endpoints
- `backend/app/db/models.py` - UserSession model
- `backend/app/core/security.py` - Token generation

### Database Investigation:
- [ ] Check `user_sessions` table after logout
- [ ] Verify old tokens are deleted/invalidated
- [ ] Check if new registration creates new session row

---

## 🛠️ Proposed Fix Strategy

### Phase 1: Frontend Token Clearing
```typescript
// In logout function:
localStorage.removeItem('access_token')
localStorage.removeItem('refresh_token')
sessionStorage.clear()
// Clear auth context state
setUser(null)
setTokens(null)
```

### Phase 2: Backend Token Invalidation
```python
# In logout endpoint:
- Delete refresh token from database
- Add token to blacklist (if implemented)
- Clear all user sessions

# In registration endpoint:
- Ensure new tokens are generated
- Create new session in database
- Return tokens in response
```

### Phase 3: Frontend Registration Flow
```typescript
// After registration success:
1. Clear any existing tokens (defensive)
2. Set NEW tokens from registration response
3. Fetch new user profile
4. Redirect to dashboard
```

---

## 🧪 Testing Plan

### Manual Test Cases:
1. **Happy Path:**
   - Login as user1@test.com
   - Logout
   - Register user2@test.com
   - ✅ Should be logged in as user2@test.com

2. **Token Verification:**
   - Login as user1
   - Decode JWT token → Note user_id
   - Logout
   - Register user2
   - Decode JWT token → Should have different user_id

3. **Database Verification:**
   - Login as user1
   - Note refresh_token_hash in user_sessions table
   - Logout
   - Verify session deleted/invalidated
   - Register user2
   - Verify new session created with different hash

### Automated Test:
```python
# In backend/tests/test_auth.py
async def test_logout_clears_session():
    # Login user1
    # Logout
    # Verify session invalidated
    # Register user2
    # Verify new session created
    # Verify different user_id in JWT
```

---

## 📋 Related Improvements

### FR-003: Show Logged-In User in UI
**Priority:** HIGH (related to this bug)  
**Status:** ✅ **ALREADY IMPLEMENTED**

**Implementation Details:**
- Navbar shows user email from AuthContext (`user.email`)
- User icon (Lucide User icon) displayed next to email
- Styled with muted background container
- Located in top-right corner of navbar
- Logout button next to user display

**Current Implementation:**
```typescript
// In frontend/components/layout/navbar.tsx (lines 82-87)
{user && (
  <div className="flex items-center space-x-2 px-3 py-2 rounded-md bg-muted/50">
    <User className="h-4 w-4 text-muted-foreground" />
    <span className="text-sm text-muted-foreground">{user.email}</span>
  </div>
)}
```

**Benefits Achieved:**
- ✅ Users can immediately see which account they're logged in as
- ✅ Helps identify cross-account access issues
- ✅ Clear visual confirmation of authentication state

---

## ⚠️ Risk Assessment

**If Left Unfixed:**
- 🔴 Users can accidentally access other accounts
- 🔴 Data privacy violations
- 🔴 Regulatory compliance issues (GDPR, etc.)
- 🔴 Loss of user trust
- 🔴 Cannot launch to multiple users safely

**Fix Difficulty:** MEDIUM (2-3 hours)  
**Testing Required:** HIGH (must be thorough)  
**Deploy Priority:** CRITICAL (block all other features)

---

## 📝 Action Items

**Immediate:**
- [x] Document bug in KNOWN_BUGS.md
- [x] Create this detailed investigation document
- [ ] Add FR-003 to feature roadmap (show logged-in user)

**Next Session:**
- [ ] Investigate frontend token storage
- [ ] Investigate backend logout endpoint
- [ ] Implement fix
- [ ] Write tests
- [ ] Verify fix in Railway production
- [ ] Add user indicator to UI

---

## 🔗 References

- Session management best practices: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
- JWT invalidation strategies: https://stackoverflow.com/questions/21978658/invalidating-json-web-tokens
- Auth0 logout guide: https://auth0.com/docs/authenticate/login/logout

---

**Document Created:** November 9, 2025  
**Last Updated:** November 9, 2025  
**Assignee:** TBD (Next session)  
**Estimated Fix Time:** 2-3 hours

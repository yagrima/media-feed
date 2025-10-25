# Me Feed - Integration Test Checklist

**Date Created**: October 20, 2025
**Purpose**: Comprehensive integration testing checklist for frontend-backend integration
**Status**: Ready for Testing

---

## Pre-Test Setup

### Backend Prerequisites
- [ ] Backend running on `http://localhost:8000`
- [ ] PostgreSQL database running and migrated
- [ ] Redis cache running
- [ ] Environment variables configured (.env file)
- [ ] JWT keys generated in `secrets/` directory
- [ ] TMDB API key configured (optional for basic testing)

### Frontend Prerequisites
- [ ] Frontend dependencies installed (`npm install`)
- [ ] `@radix-ui/react-switch` dependency installed
- [ ] Frontend running on `http://localhost:3000`
- [ ] `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.local`

### Quick Start Commands
```bash
# Backend
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

---

## Test Categories

## 1. Authentication & Authorization ✅

### 1.1 User Registration
- [ ] Navigate to `/register`
- [ ] Test validation errors:
  - [ ] Empty email shows error
  - [ ] Invalid email format shows error
  - [ ] Password less than 12 characters shows error
  - [ ] Password without uppercase shows error
  - [ ] Password without lowercase shows error
  - [ ] Password without digit shows error
  - [ ] Password without special character shows error
  - [ ] Passwords don't match shows error
- [ ] Register with valid credentials
  - [ ] Success toast appears
  - [ ] Redirected to login page or dashboard
  - [ ] User can see success confirmation
- [ ] Test duplicate registration:
  - [ ] Error toast appears for existing email
  - [ ] Appropriate error message displayed

**Expected Backend Behavior**:
- POST `/api/auth/register`
- Returns: `201 Created` with user object
- Error: `400 Bad Request` for validation errors

### 1.2 User Login
- [ ] Navigate to `/login`
- [ ] Test validation errors:
  - [ ] Empty email shows error
  - [ ] Empty password shows error
  - [ ] Invalid email format shows error
- [ ] Login with valid credentials
  - [ ] Success toast appears
  - [ ] Redirected to `/dashboard`
  - [ ] User email appears in settings
  - [ ] Navbar appears with navigation links
- [ ] Login with invalid credentials:
  - [ ] Error toast appears
  - [ ] Error message displayed in form
  - [ ] User remains on login page

**Expected Backend Behavior**:
- POST `/api/auth/login`
- Returns: `{ access_token, refresh_token, token_type, expires_in }`
- Error: `401 Unauthorized` for invalid credentials

### 1.3 Token Refresh
- [ ] Stay logged in for 15 minutes (or modify token expiry)
- [ ] Make an API request after token expires
  - [ ] Token automatically refreshes in background
  - [ ] Original request succeeds
  - [ ] No interruption to user
- [ ] Test expired refresh token:
  - [ ] Toast notification: "Session expired. Please login again."
  - [ ] Redirected to `/login`

**Expected Backend Behavior**:
- First request returns `401 Unauthorized`
- POST `/api/auth/refresh` with refresh token
- Returns: new `access_token` and `refresh_token`
- Original request retried automatically

### 1.4 Protected Routes
- [ ] Logout (if logged in)
- [ ] Try to access `/dashboard` directly
  - [ ] Redirected to `/login`
- [ ] Try to access `/dashboard/import`
  - [ ] Redirected to `/login`
- [ ] Try to access `/dashboard/notifications`
  - [ ] Redirected to `/login`
- [ ] Login and verify access to all protected routes

### 1.5 Logout
- [ ] Click "Logout" button in navbar
  - [ ] Success toast appears
  - [ ] Redirected to `/login`
  - [ ] Tokens cleared from localStorage
  - [ ] Cannot access protected routes
  - [ ] Backend session invalidated (if applicable)

---

## 2. CSV Import & Media Library 📊

### 2.1 CSV Upload
- [ ] Navigate to `/dashboard/import`
- [ ] Test file validation:
  - [ ] Drag non-CSV file - should show error
  - [ ] Drag file > 10MB - should show error
  - [ ] Drag CSV file - should show green border/highlight
- [ ] Upload valid Netflix CSV:
  - [ ] Progress indicator appears
  - [ ] Success toast appears
  - [ ] Job ID displayed
  - [ ] Status shows "Processing" or "Completed"
  - [ ] Row counts update (successful/failed/total)

**Test CSV Format** (create `test.csv`):
```csv
Title,Date
Breaking Bad: Season 1,2024-01-15
The Matrix,2024-02-20
Stranger Things: Season 3,2024-03-10
```

**Expected Backend Behavior**:
- POST `/api/import/csv` (multipart/form-data)
- Returns: `{ job_id, status, message }`
- Rate limit: 5 uploads per hour

### 2.2 Import Status Tracking
- [ ] After upload, status polling starts automatically
  - [ ] Progress bar updates every 2 seconds
  - [ ] Row counts update in real-time
  - [ ] Status changes from "processing" to "completed"
- [ ] Check error log if any rows failed:
  - [ ] Failed rows displayed with reasons
  - [ ] Error messages are clear

### 2.3 Import History
- [ ] Scroll down to Import History section
  - [ ] Previous imports listed
  - [ ] Each shows: filename, date, status, row counts
  - [ ] Status badges color-coded (green/red/yellow)
- [ ] Upload another CSV:
  - [ ] History updates automatically
  - [ ] Most recent import at top

### 2.4 Media Library Display
- [ ] Navigate to `/dashboard` or `/dashboard/library`
- [ ] Verify media grid displays:
  - [ ] All imported media items shown
  - [ ] Movie icon for movies
  - [ ] TV icon for TV series
  - [ ] Season number displayed for TV shows
  - [ ] Platform badge displayed
  - [ ] Consumed date displayed
  - [ ] Cards are clickable (hover effect)

**Expected Backend Behavior**:
- GET `/api/import/status/{job_id}`
- GET `/api/import/history?page=1&page_size=20`
- Returns: paginated import job list

### 2.5 Media Library Pagination
- [ ] If library has > 20 items:
  - [ ] Pagination controls appear at bottom
  - [ ] Page numbers displayed correctly
  - [ ] "Next" button enabled
  - [ ] "Previous" button disabled on first page
- [ ] Click "Next" page:
  - [ ] New items load
  - [ ] Smooth scroll to top
  - [ ] Loading state shown briefly
  - [ ] Page number updates
- [ ] Click page number directly:
  - [ ] Jumps to that page
  - [ ] Items update correctly
- [ ] Click "Last" page:
  - [ ] Goes to final page
  - [ ] "Next" button disabled

**Expected Backend Behavior**:
- GET `/api/media?page=1&limit=20`
- Returns: `{ items: [], total, page, limit }`

### 2.6 Media Library Filtering
- [ ] Click "All" filter - shows all media
- [ ] Click "Movies" filter:
  - [ ] Only movies displayed
  - [ ] TV series hidden
  - [ ] Count updates
- [ ] Click "TV Series" filter:
  - [ ] Only TV shows displayed
  - [ ] Movies hidden
  - [ ] Count updates
- [ ] Pagination works with filters:
  - [ ] Filtered results paginate correctly
  - [ ] Total count reflects filtered items

**Expected Backend Behavior**:
- GET `/api/media?type=movie&page=1&limit=20`
- Returns: filtered paginated results

---

## 3. Notifications 🔔

### 3.1 Notification Display
- [ ] Navigate to `/dashboard/notifications`
- [ ] Verify notification center displays:
  - [ ] Notification list (or empty state if none)
  - [ ] Icons based on type (sequel/import/system)
  - [ ] Unread count badge at top
  - [ ] "Mark all as read" button if unread exist
  - [ ] Manual refresh button

### 3.2 Notification Types
Create test notifications via backend or wait for import completion:

**Import Complete Notification**:
- [ ] Complete a CSV import
- [ ] Notification appears automatically
- [ ] Green upload icon
- [ ] Title: "Import Complete"
- [ ] Message includes filename and row count
- [ ] "New" badge if unread

**Import Failed Notification**:
- [ ] Upload invalid CSV
- [ ] Notification appears
- [ ] Red alert icon
- [ ] Title: "Import Failed"
- [ ] Error details in message

**Sequel Detected Notification** (requires backend processing):
- [ ] If sequel detection runs
- [ ] Film icon displayed
- [ ] Shows original and sequel titles
- [ ] Link or metadata displayed

### 3.3 Mark as Read
- [ ] Click "Mark read" on single notification:
  - [ ] "New" badge disappears
  - [ ] Background changes to muted color
  - [ ] Unread count decreases
  - [ ] Navbar badge updates
- [ ] Click "Mark all read" button:
  - [ ] All notifications marked read
  - [ ] Success toast appears
  - [ ] Unread count becomes 0
  - [ ] Navbar badge disappears

**Expected Backend Behavior**:
- PUT `/api/notifications/{id}/read`
- PUT `/api/notifications/mark-all-read`
- Returns: `200 OK`

### 3.4 Delete Notification
- [ ] Click trash icon on notification:
  - [ ] Notification removed from list
  - [ ] Success toast appears
  - [ ] Total count updates
  - [ ] If unread, navbar badge updates

**Expected Backend Behavior**:
- DELETE `/api/notifications/{id}`
- Returns: `204 No Content`

### 3.5 Auto-Refresh
- [ ] Create new notification via backend (or trigger import)
- [ ] Wait 30 seconds without refreshing page
  - [ ] New notification appears automatically
  - [ ] Navbar badge updates
  - [ ] Unread count increases
- [ ] Switch to another tab, then back:
  - [ ] Notifications refresh immediately
  - [ ] Latest data displayed

### 3.6 Pagination
- [ ] If > 20 notifications exist:
  - [ ] Pagination controls appear
  - [ ] Works same as media library pagination
  - [ ] Auto-refresh works on all pages

---

## 4. Notification Preferences ⚙️

### 4.1 Load Preferences
- [ ] Navigate to `/dashboard/notifications/preferences`
- [ ] Verify page loads:
  - [ ] All switches display current state
  - [ ] Loading state shown briefly
  - [ ] No errors

**Expected Backend Behavior**:
- GET `/api/notifications/preferences`
- Returns: `{ email_enabled, sequel_notifications, import_notifications, system_notifications }`

### 4.2 Toggle Switches
- [ ] Toggle "Email Notifications" switch:
  - [ ] Switch animates smoothly
  - [ ] On/off state clear
  - [ ] "Save Preferences" button enables
- [ ] Toggle each notification type:
  - [ ] Sequel Detected
  - [ ] Import Status
  - [ ] System Updates
- [ ] Each switch works independently

### 4.3 Save Preferences
- [ ] Make changes to preferences
- [ ] Click "Save Preferences":
  - [ ] Loading indicator appears
  - [ ] Success toast: "Preferences updated successfully"
  - [ ] Button disabled (no changes)
  - [ ] Switches remain in new state
- [ ] Refresh page:
  - [ ] Changes persisted
  - [ ] Switches show saved state

**Expected Backend Behavior**:
- PUT `/api/notifications/preferences`
- Body: `{ email_enabled: true, ... }`
- Returns: `200 OK` with updated preferences

### 4.4 Accessibility Testing
- [ ] Tab through all switches:
  - [ ] Focus ring visible
  - [ ] Keyboard accessible (Space/Enter to toggle)
- [ ] Use screen reader (if available):
  - [ ] Switch labels announced
  - [ ] State (on/off) announced
  - [ ] Descriptions read correctly

---

## 5. Settings Page 👤

### 5.1 Profile Information
- [ ] Navigate to `/dashboard/settings`
- [ ] Verify profile section displays:
  - [ ] User email correct
  - [ ] Member since date correct
  - [ ] Account status badge ("Active")

**Expected Backend Behavior**:
- GET `/api/auth/me`
- Returns: `{ id, email, created_at, ... }`

### 5.2 Navigation Links
- [ ] Click "Manage Notification Settings":
  - [ ] Navigates to `/dashboard/notifications/preferences`
  - [ ] Settings page functional

### 5.3 Placeholder Features
- [ ] Verify placeholders exist:
  - [ ] "Change Password" button (disabled, "Coming Soon")
  - [ ] "Enable 2FA" button (disabled, "Coming Soon")
  - [ ] "Export Data" button (disabled, "Coming Soon")
  - [ ] "Delete Account" button (disabled, "Coming Soon")

---

## 6. Error Handling 🚨

### 6.1 Network Errors
- [ ] Stop backend server
- [ ] Try to login:
  - [ ] Toast: "Network error - Unable to reach the server"
  - [ ] Error message displayed
- [ ] Try to load dashboard:
  - [ ] Toast notification appears
  - [ ] Appropriate error handling
- [ ] Restart backend:
  - [ ] App reconnects automatically
  - [ ] Operations resume normally

### 6.2 API Errors
- [ ] Test 404 error (invalid endpoint):
  - [ ] Toast: "Not found" with description
- [ ] Test 429 rate limit (upload 6 CSVs in 1 hour):
  - [ ] Toast: "Too many requests"
  - [ ] Clear error message
- [ ] Test 500 server error (if possible):
  - [ ] Toast: "Server error"
  - [ ] User-friendly message

### 6.3 Component Errors
- [ ] Manually trigger React error (modify code temporarily):
  - [ ] Error boundary catches error
  - [ ] Error UI displayed
  - [ ] "Try Again" button works
  - [ ] "Go to Dashboard" button works
  - [ ] No white screen of death

### 6.4 404 Page
- [ ] Navigate to `/nonexistent-route`
  - [ ] 404 page displays
  - [ ] "Page Not Found" message
  - [ ] "Go to Dashboard" button works
  - [ ] "Go to Login" button works

---

## 7. Navigation & UX 🧭

### 7.1 Navbar
- [ ] Verify all navigation links work:
  - [ ] Library → `/dashboard`
  - [ ] Import → `/dashboard/import`
  - [ ] Notifications → `/dashboard/notifications`
  - [ ] Settings → `/dashboard/settings`
- [ ] Active page highlighted correctly
- [ ] Unread notification badge:
  - [ ] Shows correct count
  - [ ] Displays "99+" for > 99 unread
  - [ ] Disappears when all read
  - [ ] Updates in real-time

### 7.2 Responsive Design
- [ ] Test on mobile viewport (Chrome DevTools):
  - [ ] Navbar stacks/collapses appropriately
  - [ ] Cards resize correctly
  - [ ] Buttons accessible
  - [ ] Text readable
- [ ] Test on tablet viewport:
  - [ ] 2-column grid for media cards
  - [ ] Layout adjusts smoothly
- [ ] Test on desktop:
  - [ ] 4-column grid for media cards
  - [ ] Optimal spacing

### 7.3 Loading States
- [ ] Observe loading indicators:
  - [ ] Skeleton screens or spinners
  - [ ] Smooth transitions
  - [ ] No flickering
  - [ ] Clear visual feedback

### 7.4 Empty States
- [ ] Test empty library:
  - [ ] Friendly message displayed
  - [ ] "Upload CSV" CTA button
  - [ ] Icon displayed
- [ ] Test empty notifications:
  - [ ] "No notifications" message
  - [ ] Bell icon displayed
  - [ ] Appropriate copy

---

## 8. Performance 🚀

### 8.1 Initial Load
- [ ] Measure First Contentful Paint (Chrome DevTools):
  - [ ] Target: < 2 seconds
- [ ] Check bundle size:
  - [ ] Run `npm run build`
  - [ ] Review Next.js build output
  - [ ] No unexpectedly large chunks

### 8.2 API Response Times
- [ ] Monitor Network tab:
  - [ ] Login: < 500ms
  - [ ] Fetch media: < 500ms
  - [ ] CSV upload: depends on file size
  - [ ] Notifications: < 300ms

### 8.3 Memory Leaks
- [ ] Navigate between pages 20+ times
- [ ] Monitor Memory tab in DevTools:
  - [ ] Memory usage stable
  - [ ] No continuous growth
  - [ ] No detached DOM nodes

---

## 9. Security 🔐

### 9.1 Token Storage
- [ ] Open DevTools → Application → Local Storage
- [ ] Verify tokens stored:
  - [ ] `access_token` present
  - [ ] `refresh_token` present
  - [ ] `token_expiry` present
- [ ] Logout:
  - [ ] Tokens cleared from localStorage
  - [ ] No sensitive data remaining

### 9.2 CORS
- [ ] Verify CORS headers allow frontend origin
- [ ] Check backend allows `http://localhost:3000`
- [ ] No CORS errors in console

### 9.3 Input Validation
- [ ] Test XSS attempts (if applicable):
  - [ ] Input: `<script>alert('XSS')</script>`
  - [ ] Verify: Rendered as text, not executed
- [ ] SQL injection attempts (backend responsibility):
  - [ ] Input special characters in login
  - [ ] No database errors exposed

### 9.4 Rate Limiting
- [ ] Upload 6 CSVs within 1 hour:
  - [ ] 6th upload blocked
  - [ ] Clear error message
  - [ ] User informed of limit
- [ ] Wait 1 hour (or adjust backend limit):
  - [ ] Can upload again

---

## 10. Browser Compatibility 🌐

### 10.1 Chrome
- [ ] All features work
- [ ] No console errors
- [ ] UI renders correctly

### 10.2 Firefox
- [ ] All features work
- [ ] No console errors
- [ ] UI renders correctly

### 10.3 Safari (if available)
- [ ] All features work
- [ ] No console errors
- [ ] UI renders correctly

### 10.4 Edge
- [ ] All features work
- [ ] No console errors
- [ ] UI renders correctly

---

## Known Issues & Workarounds

Document any issues found during testing:

### Issue Template
```
**Issue**: [Brief description]
**Severity**: [Critical / High / Medium / Low]
**Steps to Reproduce**:
1.
2.
3.
**Expected**: [What should happen]
**Actual**: [What actually happens]
**Workaround**: [Temporary fix if any]
**Status**: [Open / In Progress / Fixed]
```

---

## Sign-Off Checklist

### Developer
- [ ] All critical paths tested
- [ ] No console errors
- [ ] Performance acceptable
- [ ] Documentation updated
- [ ] Ready for technical lead review

**Tested by**: _____________
**Date**: _____________
**Signature**: _____________

### Technical Lead
- [ ] Integration test results reviewed
- [ ] Known issues acceptable for MVP
- [ ] Security checks passed
- [ ] Performance metrics acceptable
- [ ] Approved for staging deployment

**Reviewed by**: _____________
**Date**: _____________
**Signature**: _____________

---

## Test Results Summary

**Total Tests**: [  ]
**Passed**: [  ]
**Failed**: [  ]
**Blocked**: [  ]
**Pass Rate**: [  ]%

**Critical Issues**: [  ]
**High Priority Issues**: [  ]
**Medium Priority Issues**: [  ]
**Low Priority Issues**: [  ]

**Overall Status**: ⬜ PASS | ⬜ FAIL | ⬜ CONDITIONAL PASS

**Notes**:
_____________________________________________________________________________
_____________________________________________________________________________
_____________________________________________________________________________

---

**Document Version**: 1.0
**Last Updated**: October 20, 2025
**Next Review**: After integration testing completion

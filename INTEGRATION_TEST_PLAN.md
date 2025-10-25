# Integration Testing Plan - Notification Center

**Date**: October 20, 2025
**Developer**: Implementation Complete
**Status**: Ready for Manual Testing

---

## Overview

Notification center implementation complete. Frontend code ready but requires:
1. Backend services running
2. npm dependencies installed (cache corruption resolved)
3. Manual end-to-end testing

---

## Pre-Test Checklist

### Backend Services
- [ ] Docker services running: `docker-compose up -d`
- [ ] Database migrations applied: `docker exec mefeed_backend alembic upgrade head`
- [ ] Backend health check: `curl http://localhost:8000/health`
- [ ] Redis connection verified
- [ ] Test user account created

### Frontend Setup
- [ ] npm dependencies installed: `cd frontend && npm install`
- [ ] TypeScript compilation successful: `npm run type-check`
- [ ] Development server started: `npm run dev`
- [ ] Environment variable set: `NEXT_PUBLIC_API_URL=http://localhost:8000`

---

## Test Scenarios

### Test 1: Authentication Flow
**Purpose**: Verify notification system works with authenticated users

1. Navigate to `http://localhost:3000/login`
2. Login with test credentials
3. Verify JWT token stored in localStorage
4. Check navbar displays notification bell icon
5. Verify no errors in browser console

**Expected Result**:
- Successful login
- Navbar shows "Notifications" link
- No unread badge (fresh account)

---

### Test 2: Notification Badge Display
**Purpose**: Verify unread notification count displays correctly

**Setup**: Create test notifications via backend API or SQL:
```sql
INSERT INTO notifications (user_id, type, title, message, data, read)
VALUES
  ('<user_id>', 'sequel_detected', 'New Sequel Available', 'Stranger Things Season 5 is now available', '{"media_title": "Stranger Things S4", "sequel_title": "Stranger Things S5"}', false),
  ('<user_id>', 'import_complete', 'Import Complete', 'Your CSV import finished successfully', '{"total_rows": 100}', false);
```

1. Refresh page or wait 30 seconds (auto-refresh interval)
2. Check navbar notification icon

**Expected Result**:
- Red badge showing "2" appears on Notifications button
- Badge displays "99+" for counts over 99

---

### Test 3: Notification Center Display
**Purpose**: Verify notification list renders correctly

1. Click "Notifications" in navbar
2. Navigate to `/dashboard/notifications`
3. Verify notification list displays

**Expected Result**:
- Page loads without errors
- Header shows "2 unread" badge
- "Mark all read" button visible
- Two notification cards displayed
- Unread notifications have "New" badge
- Correct icons displayed:
  - Film icon for sequel_detected
  - Upload icon (green) for import_complete
- Timestamps formatted correctly
- Data fields rendered (media titles)

---

### Test 4: Mark Single as Read
**Purpose**: Test individual notification marking

1. Click "Mark read" on first notification
2. Verify API call: `PUT /api/notifications/{id}/read`

**Expected Result**:
- Notification card background changes to muted
- "New" badge disappears
- "Mark read" button disappears
- Navbar badge updates to "1"
- No page reload

---

### Test 5: Mark All as Read
**Purpose**: Test bulk marking functionality

1. Create multiple unread notifications
2. Click "Mark all read" button
3. Verify API call: `PUT /api/notifications/mark-all-read`

**Expected Result**:
- All notifications visually marked as read
- Navbar badge disappears
- Toast notification: "All notifications marked as read"
- Query cache invalidated

---

### Test 6: Delete Notification
**Purpose**: Test notification deletion

1. Click trash icon on a notification
2. Verify API call: `DELETE /api/notifications/{id}`

**Expected Result**:
- Notification removed from list
- Toast notification: "Notification deleted"
- Total count decreases
- Unread count updates if deleted notification was unread

---

### Test 7: Notification Types & Icons
**Purpose**: Verify all notification types render correctly

Create one of each type:
- `sequel_detected` → Film icon (blue)
- `import_complete` → Upload icon (green)
- `import_failed` → AlertCircle icon (red)
- `system` → Bell icon (muted)

**Expected Result**:
- Each type displays correct icon
- Colors match type (success green, error red, etc.)
- Icon positioned correctly in card

---

### Test 8: Pagination
**Purpose**: Test notification pagination

**Setup**: Create 25+ notifications

1. Load notifications page
2. Verify only 20 displayed
3. Check pagination controls visible
4. Click "Next" button

**Expected Result**:
- Shows "Page 1 of 2"
- "Previous" disabled on page 1
- "Next" enabled
- Clicking "Next" loads page 2
- API called with `?page=2&limit=20`

---

### Test 9: Empty State
**Purpose**: Verify empty state displays

1. Delete all notifications
2. Navigate to `/dashboard/notifications`

**Expected Result**:
- Empty state card displayed
- Bell icon (large, muted)
- Message: "You're all caught up! New notifications will appear here."
- No errors

---

### Test 10: Notification Preferences
**Purpose**: Test preferences page and form

1. Navigate to `/dashboard/notifications`
2. Click "Preferences" button
3. Navigate to `/dashboard/notifications/preferences`

**Expected Result**:
- Preferences form loads
- Current settings fetched: `GET /api/notifications/preferences`
- Four toggle checkboxes:
  - Email Notifications
  - Sequel Detected
  - Import Status
  - System Updates
- Default values loaded from API

---

### Test 11: Update Preferences
**Purpose**: Test saving notification preferences

1. On preferences page, toggle checkboxes
2. Click "Save Preferences" button
3. Verify API call: `PUT /api/notifications/preferences`

**Expected Result**:
- Loading state: "Saving..." button text
- API called with updated values
- Toast notification: "Preferences updated successfully"
- Form disabled state during save
- "Save" button disabled until changes made

---

### Test 12: Real-time Updates
**Purpose**: Verify auto-refresh of unread count

1. Open app in browser tab
2. Create new notification via backend/SQL
3. Wait 30 seconds (refetch interval)

**Expected Result**:
- Badge updates automatically
- No page reload
- React Query refetches data

---

### Test 13: CORS & API Connectivity
**Purpose**: Verify frontend-backend communication

1. Open browser DevTools Network tab
2. Navigate to notifications page
3. Check API requests

**Expected Result**:
- No CORS errors
- Authorization headers present
- Requests to `http://localhost:8000/api/notifications/*`
- 200 OK responses
- JSON data received

---

### Test 14: Token Refresh During Long Session
**Purpose**: Test JWT refresh during notification polling

1. Login
2. Wait for access token to near expiry (~15 min)
3. Let auto-refresh trigger

**Expected Result**:
- Notification queries continue working
- Token refresh transparent
- No logout
- No 401 errors

---

### Test 15: Error Handling
**Purpose**: Test error states

**Scenarios**:
- Backend down: Stop docker services
- Network error: Block localhost:8000
- 500 error: Modify backend to return error

**Expected Result**:
- Error state displayed in notification center
- AlertCircle icon with error message
- No app crash
- Toast notifications for failed mutations

---

## API Endpoints Used

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/notifications` | List notifications (paginated) |
| GET | `/api/notifications/unread` | Get unread count |
| PUT | `/api/notifications/{id}/read` | Mark single as read |
| PUT | `/api/notifications/mark-all-read` | Mark all as read |
| DELETE | `/api/notifications/{id}` | Delete notification |
| GET | `/api/notifications/preferences` | Get user preferences |
| PUT | `/api/notifications/preferences` | Update preferences |

---

## Browser Console Checks

### Required Checks
- [ ] No TypeScript errors
- [ ] No React Query errors
- [ ] No 401/403/500 errors
- [ ] Query cache updates visible
- [ ] Token refresh logs (if applicable)

### React Query DevTools (Optional)
- [ ] Install: `npm i @tanstack/react-query-devtools`
- [ ] Check query states: loading, success, error
- [ ] Verify cache invalidation on mutations
- [ ] Confirm refetch intervals

---

## Files Implemented

**New Files** (7):
1. `frontend/lib/api/notifications.ts` - API client
2. `frontend/components/notifications/notification-center.tsx` - Main component
3. `frontend/components/notifications/notification-preferences.tsx` - Preferences form
4. `frontend/app/(dashboard)/dashboard/notifications/page.tsx` - List page
5. `frontend/app/(dashboard)/dashboard/notifications/preferences/page.tsx` - Preferences page

**Modified Files** (1):
6. `frontend/components/layout/navbar.tsx` - Added notification link + badge

---

## Known Limitations

1. **No E2E Tests**: Manual testing only (Playwright/Cypress not configured)
2. **npm Cache Corruption**: May require `npm cache clean --force` before install
3. **No Backend Unit Tests**: Notification endpoints lack test coverage
4. **No Real-time WebSocket**: Uses polling (30s interval) instead of push notifications
5. **No Notification Sound**: Visual only, no audio alerts

---

## Post-Test Actions

After successful testing:
- [ ] Document any bugs found
- [ ] Update PROJECT_STATUS.md
- [ ] Mark notification center as complete
- [ ] Move to error boundary implementation
- [ ] Plan Week 6 priorities (Celery, CI/CD)

---

## Manual Testing Command Reference

```bash
# Start backend services
docker-compose up -d

# Check backend health
curl http://localhost:8000/health

# View backend logs
docker logs mefeed_backend -f

# Start frontend dev server
cd frontend
npm install
npm run dev

# Type checking
npm run type-check

# Create test notification (SQL)
docker exec -it mefeed_db psql -U <user> -d mefeed
INSERT INTO notifications (...);

# Check React Query cache
# Open browser: http://localhost:3000
# Press Ctrl+Shift+C → Console
# Type: window.__REACT_QUERY_DEVTOOLS__
```

---

**Next Steps**:
1. Resolve npm install issues
2. Start backend services
3. Run manual tests 1-15
4. Document results
5. Fix any bugs found
6. Mark feature complete

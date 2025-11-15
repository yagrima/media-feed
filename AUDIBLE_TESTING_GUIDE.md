# Audible Integration - Testing Guide

**Date:** November 11, 2025  
**Status:** Ready for Testing  
**URLs:**
- Frontend: https://proud-courtesy-production-992b.up.railway.app
- Backend: https://media-feed-production.up.railway.app

---

## ✅ Pre-Testing Checklist

### 1. Verify Frontend is Live
```powershell
# Run this command:
Invoke-WebRequest -Uri "https://proud-courtesy-production-992b.up.railway.app" -UseBasicParsing | Select-Object StatusCode

# Expected: StatusCode should be 200
```

### 2. Verify Backend Health
```powershell
# Run this command:
curl https://media-feed-production.up.railway.app/health

# Expected: {"status":"healthy","service":"Me Feed","version":"1.1.0"}
```

---

## 🧪 Test Scenario 1: View Connection Status (Not Connected)

### Steps:
1. Open browser: https://proud-courtesy-production-992b.up.railway.app
2. Log in with your existing account
3. Navigate to **Import** page (from sidebar)
4. Scroll down to **"Audible Audiobooks importieren"** section

### Expected Results:
- ✅ You see a card titled "Audible Connection"
- ✅ Badge shows "Not Connected" (gray)
- ✅ You see a book icon
- ✅ Description says "Connect your Audible account to import audiobooks"
- ✅ Shows benefits list:
  - One-click import of your entire library
  - Secure credential storage (encrypted)
  - Sync new purchases automatically
  - Rich metadata (authors, narrators, duration)
- ✅ Blue button: "Connect Audible Account"

### Screenshot Locations:
- Top right: "Not Connected" badge
- Center: Book icon with empty state message
- Bottom: Benefits list

---

## 🧪 Test Scenario 2: Open Connection Modal

### Steps:
1. Click **"Connect Audible Account"** button

### Expected Results:
- ✅ Modal dialog opens
- ✅ Title: "Connect Audible Account" with book icon
- ✅ Description: "Enter your Audible credentials to import your audiobook library. Your password is never stored—only an encrypted token."
- ✅ Form fields visible:
  - Email input (type: email)
  - Password input (type: password, masked)
  - Marketplace dropdown (default: "United States")
- ✅ Helper text under password: "If you have 2FA enabled, append your 2FA code to your password"
- ✅ Authorization notice (gray box)
- ✅ Two buttons: "Cancel" (gray), "Connect & Import" (blue)

---

## 🧪 Test Scenario 3: Form Validation

### Test 3a: Empty Fields
**Steps:** Click "Connect & Import" without entering anything

**Expected:**
- ✅ Browser shows "Please fill out this field" for email
- ❌ Should NOT submit

### Test 3b: Invalid Email
**Steps:** 
1. Enter "notanemail" in email field
2. Enter any password
3. Click "Connect & Import"

**Expected:**
- ✅ Browser shows "Please include '@' in the email address"
- ❌ Should NOT submit

### Test 3c: Valid Format
**Steps:**
1. Enter "test@example.com"
2. Enter "password123"
3. Select marketplace
4. Click "Connect & Import"

**Expected:**
- ✅ Form submits (will fail auth, but validates format)
- ✅ Loading spinner appears
- ✅ Button text changes to "Connecting..."
- ✅ After ~2 seconds, error appears: "Invalid email or password"

---

## 🧪 Test Scenario 4: Connect with Wrong Credentials

### Steps:
1. Enter your real Audible email
2. Enter WRONG password
3. Select correct marketplace
4. Click "Connect & Import"

### Expected Results:
- ✅ Button shows loading spinner: "Connecting..."
- ✅ Form fields become disabled
- ✅ After 2-5 seconds, red error alert appears:
  - **Error:** "Invalid email or password"
  - **Tip:** "Double-check your email and password. Make sure you're using your Amazon/Audible credentials."
- ✅ Form re-enables
- ✅ Button returns to "Connect & Import"

---

## 🧪 Test Scenario 5: Connect with REAL Credentials ⭐

### Prerequisites:
- Have your Audible account credentials ready
- Know your Audible marketplace (US, UK, DE, etc.)
- If you have 2FA: Have your 2FA code ready

### Steps:
1. Enter your **real Audible email**
2. Enter your **real Audible password**
   - **If 2FA enabled:** Append code to password
   - Example: "MyPassword123456789" (password + 6-digit code)
3. Select your **correct marketplace**
4. Click **"Connect & Import"**

### Expected Results (Success):
1. **Loading State (5-30 seconds):**
   - ✅ Button shows "Connecting..." with spinner
   - ✅ All form fields disabled
   - ✅ No errors appear

2. **Success State:**
   - ✅ Green success alert appears:
     - **Success!** Imported X audiobooks from Audible. Redirecting...
   - ✅ Toast notification (top right): "Erfolgreich verbunden! X Hörbücher von Audible importiert."
   - ✅ After 2 seconds, modal closes automatically
   - ✅ Status card updates to show "Connected"

3. **Updated Status Card:**
   - ✅ Badge changes to "Connected" (green with checkmark)
   - ✅ Shows connection details:
     - Marketplace: US (or your marketplace)
     - Device: Me Feed - Web
     - Last Synced: just now
     - Audiobooks: X (your count)
   - ✅ Two new buttons appear:
     - "Sync Now" (blue)
     - "Disconnect" (gray outline)

### Possible Errors:

#### Error 1: CAPTCHA Required
**Message:** "CAPTCHA verification required. Please try again later or use manual import."

**What to do:**
- This means Audible detected unusual activity
- Wait 30-60 minutes
- Try again from the Audible website first
- Or use manual import (future feature)

#### Error 2: 2FA Required
**Message:** "Two-factor authentication detected. Please append your 2FA code to your password."

**What to do:**
1. Get your current 2FA code from authenticator app
2. Append it to your password
3. Example: If password is "MyPass123" and 2FA code is "456789"
4. Enter: "MyPass123456789" (no spaces)
5. Try again

#### Error 3: Rate Limit
**Message:** "Rate limit exceeded"

**What to do:**
- You tried connecting 3 times in 1 hour
- Wait until the hour passes
- Try again

---

## 🧪 Test Scenario 6: Verify Database Import

### After successful connection, verify audiobooks are in database:

#### Option A: Via Railway Dashboard
1. Go to Railway dashboard
2. Open PostgreSQL service
3. Run query:
```sql
SELECT COUNT(*) FROM media WHERE type = 'audiobook';
```
Expected: Should match your audiobook count

#### Option B: Via API
```powershell
# Get your auth token first
$loginResponse = Invoke-WebRequest -Uri "https://media-feed-production.up.railway.app/api/auth/login" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"email":"your@email.com","password":"yourpassword"}'

$token = ($loginResponse.Content | ConvertFrom-Json).access_token

# Check status
Invoke-WebRequest -Uri "https://media-feed-production.up.railway.app/api/audible/status" `
  -Headers @{"Authorization"="Bearer $token"} | 
  Select-Object -ExpandProperty Content
```

Expected:
```json
{
  "connected": true,
  "marketplace": "us",
  "device_name": "Me Feed - Web",
  "last_sync_at": "2025-11-11T...",
  "books_count": 245
}
```

---

## 🧪 Test Scenario 7: Settings Page

### Steps:
1. Navigate to **Settings** page
2. Scroll down to **"Audible Integration"** section

### Expected Results:
- ✅ Same status card as Import page
- ✅ Shows "Connected" status
- ✅ Shows all connection details
- ✅ "Sync Now" and "Disconnect" buttons visible

---

## 🧪 Test Scenario 8: Sync Library

### Steps:
1. On Import or Settings page
2. Click **"Sync Now"** button

### Expected Results:
1. **Loading State:**
   - ✅ Button shows "Syncing..." with spinner
   - ✅ Button becomes disabled

2. **Success State (5-15 seconds):**
   - ✅ Green success alert appears:
     - "Synced successfully! Imported: X, Updated: Y, Total: Z"
   - ✅ "Last Synced" timestamp updates to "just now"
   - ✅ Button returns to "Sync Now"

3. **If No New Books:**
   - Imported: 0
   - Updated: 0
   - Skipped: 245 (all existing)
   - Total: 245

---

## 🧪 Test Scenario 9: Disconnect

### Steps:
1. Click **"Disconnect"** button

### Expected Results:
1. **Confirmation Dialog Appears:**
   - ✅ Title: "Disconnect Audible Account?"
   - ✅ Description lists what will happen:
     - Remove the virtual device from your Amazon account
     - Delete stored authentication credentials
     - **Keep** all imported audiobooks in your library
   - ✅ Note: "You can reconnect at any time to sync updates."
   - ✅ Two buttons: "Cancel", "Disconnect" (red)

2. **After Clicking "Disconnect":**
   - ✅ Button shows "Disconnecting..." with spinner
   - ✅ After 2-3 seconds, dialog closes
   - ✅ Status card updates to "Not Connected"
   - ✅ Shows empty state with "Connect Audible Account" button

3. **Verify in Amazon:**
   - Go to amazon.com → Account → Content & Devices → Devices
   - "Me Feed - Web" device should be removed (or gone soon)

---

## 🧪 Test Scenario 10: Verify Audiobooks in Library

### Steps:
1. Navigate to **Library** page
2. Look for your audiobooks

### Expected Results (Current):
- ✅ Audiobooks appear in media list
- ⚠️ May show as generic media items (no special audiobook display yet)
- ⚠️ Cover art may not display (depends on Audible API response)

### What to Check:
- Do titles match your Audible library?
- Do you see the correct count?
- Can you click on them to view details?

---

## 📊 Success Criteria

### Must Pass (Critical):
- [ ] Frontend loads without errors
- [ ] Connection modal opens
- [ ] Form validation works
- [ ] Connection with real credentials succeeds
- [ ] Success message shows book count
- [ ] Status updates to "Connected"
- [ ] Audiobooks appear in database
- [ ] Sync button works
- [ ] Disconnect button works

### Should Pass (Important):
- [ ] Error messages are helpful
- [ ] Loading states show properly
- [ ] Toast notifications appear
- [ ] Settings page shows same status
- [ ] Timestamps display correctly
- [ ] German text displays correctly

### Nice to Have (Polish):
- [ ] Animations are smooth
- [ ] No console errors
- [ ] Fast response times (<5s for sync)
- [ ] Mobile responsive
- [ ] Keyboard navigation works

---

## 🐛 Known Limitations

### Current Version:
1. **Audiobook Display:** No special audiobook UI in Library yet (shows as generic media)
2. **Cover Art:** May not display (depends on Audible API)
3. **Progress Sync:** Doesn't sync listening progress from Audible (future feature)
4. **Series Grouping:** Audiobook series not grouped (future feature)

### Future Enhancements:
- Audiobook-specific library view
- Narrator filtering
- Series tracking
- Progress sync from Audible
- Wishlist integration

---

## 🆘 Troubleshooting

### Problem: Frontend won't load

**Check:**
```powershell
Invoke-WebRequest -Uri "https://proud-courtesy-production-992b.up.railway.app" -UseBasicParsing | Select-Object StatusCode
```

**Solutions:**
- If status 200: Clear browser cache and retry
- If other status: Wait 5 more minutes for deployment
- Check Railway logs for errors

---

### Problem: Modal doesn't open

**Check:**
- Browser console for JavaScript errors (F12 → Console)
- Are you logged in? (Must be authenticated)

**Solutions:**
- Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Try different browser
- Check if import page loaded correctly

---

### Problem: Connection hangs forever

**Check:**
- Browser Network tab (F12 → Network)
- Look for `/api/audible/connect` request
- Check response status and body

**Solutions:**
- Backend might be down (check health endpoint)
- Network issue (check internet connection)
- CORS issue (check browser console)

---

### Problem: "Not authenticated" error

**Solution:**
- You're logged out
- Go back to login page
- Log in again
- Return to Import page

---

### Problem: Rate limit error after 1 attempt

**Possible Cause:**
- Multiple tabs open
- Previous attempts in past hour
- Browser made duplicate requests

**Solution:**
- Close other tabs
- Wait 1 hour
- Try again

---

## 📝 Testing Checklist

**Print this checklist and mark as you test:**

```
Pre-Flight:
[ ] Frontend loads (Status 200)
[ ] Backend health check passes
[ ] Logged into application

UI Tests:
[ ] Import page shows Audible section
[ ] Status card displays "Not Connected"
[ ] "Connect" button visible and clickable
[ ] Modal opens when clicked
[ ] All form fields present
[ ] Form validation works
[ ] Cancel button closes modal

Connection Tests:
[ ] Wrong credentials show error
[ ] Error message is helpful
[ ] Correct credentials succeed
[ ] Success message shows
[ ] Book count is correct
[ ] Status updates to "Connected"
[ ] Connection details display

Functionality Tests:
[ ] Sync button works
[ ] Sync shows statistics
[ ] Last sync time updates
[ ] Disconnect shows confirmation
[ ] Disconnect succeeds
[ ] Status returns to "Not Connected"

Data Verification:
[ ] Audiobooks in database (SQL query)
[ ] Book count matches Audible
[ ] /api/audible/status returns correct data

Settings Page:
[ ] Settings shows Audible section
[ ] Same functionality as Import page
[ ] Sync works from Settings
[ ] Disconnect works from Settings

Edge Cases:
[ ] Multiple syncs in a row (should work)
[ ] Disconnect and reconnect (should work)
[ ] 3 connection attempts (4th should rate limit)
[ ] 2FA handling (if applicable)
[ ] Wrong marketplace selection (should fail)
```

---

## 🎉 Test Complete!

If all tests pass, **congratulations!** You have a fully functional Audible integration:
- ✅ Secure credential handling
- ✅ One-click library import
- ✅ Sync capability
- ✅ Clean disconnect flow
- ✅ German UI
- ✅ Error handling

**Report any issues you find!**

---

**Document Version:** 1.0  
**Last Updated:** November 11, 2025  
**Status:** Ready for Testing

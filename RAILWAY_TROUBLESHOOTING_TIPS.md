# Railway Troubleshooting Tips

**Last Updated:** November 12, 2025  
**Critical Discoveries from Production Debugging**

---

## 🚨 **CRITICAL TIP #1: Railway Dashboard Cache Issue**

### **Problem:**
Railway dashboard shows old/stale deployment data due to aggressive browser caching. You might see:
- Old deployments only
- Missing recent builds
- Incorrect "Active" status
- Wrong commit hashes
- "Last deployed X hours ago" when builds happened recently

### **Symptoms:**
- Dashboard shows "no new deployments" but you just pushed code
- Railway CLI shows different state than dashboard
- Variables changed but no deployment triggered
- Builds appear to be "stuck"

### **Solution: Use Incognito/Private Window**

**ALWAYS check Railway dashboard in incognito mode when troubleshooting:**

#### Chrome/Edge:
- Press **Ctrl + Shift + N** (Windows)
- Press **Cmd + Shift + N** (Mac)
- Navigate to railway.app

#### Firefox:
- Press **Ctrl + Shift + P** (Windows)
- Press **Cmd + Shift + P** (Mac)
- Navigate to railway.app

#### Safari:
- File → New Private Window
- Navigate to railway.app

### **Why This Happens:**
- Railway's dashboard heavily caches deployment data
- Service Worker caching
- Aggressive CDN caching
- Hard refresh (Ctrl+Shift+R) often doesn't clear it
- Only fresh session (incognito) shows true state

### **Impact:**
- **CRITICAL** - You might think deployments aren't happening when they're actually failing
- Hidden failed builds mean hidden error messages
- Wastes hours debugging "why won't it deploy" when it IS deploying (and failing)

### **Best Practice:**
1. **ALWAYS** open Railway dashboard in incognito when:
   - Checking deployment status
   - Investigating "stuck" deployments
   - Verifying builds after changes
   - Troubleshooting any deployment issues

2. **Compare** normal vs incognito views:
   - If they differ → cache issue
   - Incognito shows TRUE state
   - Normal browser shows STALE state

---

## 🚨 **CRITICAL TIP #2: Check ALL Deployment History**

### **Problem:**
Failed builds might not be visible on first page of deployment history.

### **Solution:**
- Scroll down in Deployments tab
- Look for pagination controls
- Check if there's a "Show More" or "Load More" button
- Railway might limit initial view to 10-20 deployments

### **In Incognito:**
- You'll see the FULL deployment history
- All failed builds become visible
- Error messages are accessible

---

## 🚨 **CRITICAL TIP #3: Railway CLI vs Dashboard Mismatch**

### **Problem:**
Railway CLI might deploy successfully but dashboard doesn't reflect it.

### **Symptoms:**
- `railway up` completes without error
- CLI shows "Uploaded" and "Build started"
- Dashboard shows no new deployment
- OR Dashboard shows failed build CLI didn't report

### **Solution:**
1. **Don't trust CLI output alone** - it might succeed in upload but fail in build
2. **Always verify in Railway dashboard (incognito)**
3. **Check build logs in dashboard** even if CLI says success
4. **Use direct deployment link** from CLI output

### **Why:**
- CLI only reports upload success
- Actual build happens server-side
- Build/runtime errors only visible in dashboard
- CLI doesn't stream all errors

---

## 🔍 **Troubleshooting Workflow (NEW - CRITICAL)**

### **When Deployments Seem Stuck or Missing:**

```
Step 1: Open Railway in INCOGNITO window
        ↓
Step 2: Navigate to project → service → Deployments
        ↓
Step 3: Check FULL deployment history
        ↓
Step 4: Look for failed builds (might be dozens!)
        ↓
Step 5: Click on most recent failed build
        ↓
Step 6: Read Build Logs for actual error
        ↓
Step 7: Fix error and redeploy
```

### **Don't Waste Time On:**
- ❌ Adding/removing variables repeatedly (if incognito shows builds are happening)
- ❌ Disconnecting/reconnecting GitHub (if incognito shows builds are happening)
- ❌ Using Railway CLI to force deploy (if builds are failing, not stuck)
- ❌ Changing root directory back and forth (if builds are failing, not missing)

### **Do This Instead:**
- ✅ Open incognito FIRST
- ✅ Check actual build status
- ✅ Read error messages
- ✅ Fix root cause
- ✅ Deploy once with fix

---

## 📋 **Quick Reference: When to Use Incognito**

| Situation | Use Incognito? | Why |
|-----------|----------------|-----|
| Checking if deployment completed | ✅ YES | Dashboard might show stale "Active" status |
| Reading build logs | ✅ YES | Might not show recent failed builds |
| Verifying variable changes | ✅ YES | Dashboard might show old values |
| Investigating "no new deployments" | ✅ YES | Might be deploying and failing silently |
| After `railway up` | ✅ YES | Verify build actually succeeded |
| After git push | ✅ YES | Check if auto-deploy triggered |
| Checking current commit hash | ✅ YES | Might show old commit |
| Any troubleshooting | ✅ YES | Always see true state |

---

## 🎯 **Real-World Example**

### **What Happened:**
1. User pushed Audible integration code
2. Dashboard showed: "Last deployment 4 hours ago"
3. Tried multiple fixes:
   - Added variables (no new deployment)
   - Changed root directory (no new deployment)
   - Used Railway CLI (appeared to work, but dashboard unchanged)
4. Assumed: "Railway isn't detecting pushes"
5. **Opened incognito:** Revealed dozens of failed builds!
6. Real problem: Builds were happening but FAILING

### **Time Wasted:** ~1 hour debugging "why won't it deploy"

### **Time Saved with Incognito:** 2 minutes to see actual errors

### **Lesson:**
- ✅ Always check incognito FIRST
- ✅ Cache can hide the real problem
- ✅ Failed builds = different troubleshooting path than missing builds

---

## 🚀 **Other Railway Tips**

### **Tip #4: Direct Deployment Links**
When using `railway up`, the CLI outputs a direct link:
```
Build Logs: https://railway.com/project/[id]/service/[id]?id=[deployment-id]
```
**Bookmark this link** - it goes directly to that specific deployment, bypassing cache.

### **Tip #5: Check Multiple Tabs**
In Railway dashboard:
- **Build Logs** - Shows compilation errors
- **Deploy Logs** - Shows runtime/startup errors
- **HTTP Logs** - Shows request errors
- All three might have different errors!

### **Tip #6: Railway Status Command**
```powershell
railway status
```
Shows which project/environment/service you're linked to. Run this BEFORE deploying to verify you're deploying to the right place.

### **Tip #7: Watch Paths**
If your service has "Watch Paths" configured:
- Railway only deploys when files in those paths change
- Check Settings → Build → Watch Paths
- Empty = watches all files
- Configured = only watches specific paths

### **Tip #8: Root Directory**
- Root Directory should NOT have trailing slash: `frontend` not `frontend/`
- Railway auto-suggests with leading slash: `/frontend` (this is correct)
- Changes to Root Directory should trigger immediate redeploy (check incognito to verify)

---

## 🎁 **Bonus: Force Clear Railway Cache**

### **If Incognito Shows Different State:**

**Option 1: Clear Browser Cache**
1. Normal browser window
2. F12 (Developer Tools)
3. Network tab
4. Right-click → "Clear browser cache"
5. Hard refresh: Ctrl+Shift+R

**Option 2: Clear Railway Service Worker**
1. F12 (Developer Tools)
2. Application tab
3. Service Workers
4. Find railway.app
5. Click "Unregister"
6. Hard refresh

**Option 3: Use Incognito** (Easiest)
- Just use incognito for all Railway troubleshooting
- No cache to clear

---

## 📞 **Summary for Future Sessions**

### **Always Remember:**
1. 🚨 **Check Railway in incognito FIRST** when troubleshooting
2. 🚨 **Dashboard cache can hide dozens of failed builds**
3. 🚨 **Normal browser shows STALE data, incognito shows TRUTH**
4. 🚨 **Failed builds ≠ Missing builds** (different solutions)
5. 🚨 **Railway CLI success ≠ Deployment success** (check dashboard)

### **Add to Every Troubleshooting Checklist:**
```
□ Opened Railway dashboard in incognito window
□ Checked full deployment history
□ Read build logs of most recent deployment
□ Verified actual error messages
□ Confirmed problem before attempting fixes
```

---

**Document Version:** 1.0  
**Created:** November 12, 2025  
**Discovered By:** User during Audible integration debugging  
**Lives Saved:** Could have saved 1-2 lives if known earlier  

**CRITICAL LESSON: When Railway seems stuck, it's probably not stuck - it's just cached. Check incognito!**

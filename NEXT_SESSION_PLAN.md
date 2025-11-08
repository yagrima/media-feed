# Next Session Plan - November 9, 2025

**Starting Lives:** 10 ✨  
**Session Focus:** Feature Development (FR-001)  
**Estimated Duration:** 4-6 hours

---

## 🎯 Primary Objective: FR-001 - TMDB Episode Count Lookup

**Goal:** Implement automatic episode count fetching from TMDB API during CSV import

**Priority:** 🟡 MEDIUM  
**Estimated Effort:** 4-6 hours  
**User Value:** HIGH (solves episode count display issue completely)

---

## 📋 Detailed Implementation Plan

### Phase 1: Database Schema (30 minutes)

**Task:** Add columns to store TMDB data

**Files to Modify:**
- `backend/alembic/versions/007_add_tmdb_episode_data.py` (new migration)

**Schema Changes:**
```python
# Add to media table
- total_seasons (Integer, nullable=True)
- total_episodes (Integer, nullable=True)
- tmdb_id (Integer, nullable=True, unique=True)
- last_tmdb_update (TIMESTAMP, nullable=True)
```

**Steps:**
1. Create new Alembic migration: `alembic revision -m "add tmdb episode data"`
2. Add columns with proper SQL
3. Test migration locally: `alembic upgrade head`
4. Verify in local PostgreSQL
5. Document rollback procedure

**Success Criteria:**
- ✅ Migration runs without errors
- ✅ Columns exist in database
- ✅ Can rollback successfully

---

### Phase 2: TMDB Service Method (2 hours)

**Task:** Create service to fetch episode counts from TMDB API

**Files to Modify:**
- `backend/app/services/tmdb_service.py` (extend existing)

**New Methods:**
```python
async def search_tv_series(query: str) -> Optional[int]:
    """Search for TV series and return TMDB ID"""
    
async def get_series_details(tmdb_id: int) -> Dict[str, Any]:
    """Get full series details including seasons/episodes"""
    
async def get_episode_count(series_name: str) -> Optional[Tuple[int, int]]:
    """
    Get total seasons and episodes for a series
    Returns: (total_seasons, total_episodes) or None
    """
```

**Implementation Details:**
1. Use existing TMDB API key from config
2. Add caching to avoid rate limits (Redis)
3. Handle API errors gracefully (return None)
4. Parse series name to improve search accuracy
5. Log all TMDB API calls for debugging

**Error Handling:**
- TMDB API down → Return None, log error
- Series not found → Return None, log warning
- Rate limit hit → Use cached data if available
- Network error → Return None, log error

**Caching Strategy:**
- Cache key: `tmdb:series:{series_name}`
- TTL: 7 days (episode counts don't change often)
- Store: `{tmdb_id, total_seasons, total_episodes, updated_at}`

**Success Criteria:**
- ✅ Can search for TV series by name
- ✅ Can fetch episode counts
- ✅ Handles errors gracefully
- ✅ Caching works correctly
- ✅ Rate limiting respected

---

### Phase 3: Import Integration (1 hour)

**Task:** Call TMDB during CSV import to populate episode counts

**Files to Modify:**
- `backend/app/services/import_service.py`

**Integration Points:**
1. **After media creation:** Call TMDB for TV series only
2. **Store results:** Update media record with TMDB data
3. **Log results:** Track success/failure rates
4. **Continue on failure:** Don't block import if TMDB fails

**Code Changes:**
```python
# In import_service.py, after creating media record

if media.type == "tv_series" and media.base_title:
    try:
        tmdb_data = await tmdb_service.get_episode_count(media.base_title)
        if tmdb_data:
            total_seasons, total_episodes = tmdb_data
            media.total_seasons = total_seasons
            media.total_episodes = total_episodes
            media.last_tmdb_update = datetime.utcnow()
            logger.info(f"TMDB: Found {total_episodes} episodes for {media.base_title}")
    except Exception as e:
        logger.warning(f"TMDB: Failed for {media.base_title}: {e}")
        # Continue import regardless
```

**Success Criteria:**
- ✅ TMDB called for TV series during import
- ✅ Episode counts stored in database
- ✅ Import continues even if TMDB fails
- ✅ Logging provides visibility

---

### Phase 4: API Response Update (30 minutes)

**Task:** Return total episode counts in media API responses

**Files to Modify:**
- `backend/app/api/media_api.py`
- `backend/app/schemas/media_schemas.py`

**Schema Changes:**
```python
# Add to MediaResponse
total_seasons: Optional[int] = None
total_episodes: Optional[int] = None
```

**API Changes:**
- Ensure `total_seasons` and `total_episodes` are returned in media list
- No special logic needed, Pydantic will serialize automatically

**Success Criteria:**
- ✅ API returns total episode data when available
- ✅ Frontend receives the data

---

### Phase 5: Frontend Display (1 hour)

**Task:** Update UI to show "X/Y episodes" format

**Files to Modify:**
- `frontend/components/library/media-grid.tsx`
- `frontend/components/library/media-detail-modal.tsx` (if needed)

**Display Logic:**
```typescript
// In media-grid.tsx
const episodeDisplay = media.type === 'tv_series'
  ? media.total_episodes 
    ? `${media.watched_episodes_count}/${media.total_episodes} episodes`
    : `${media.watched_episodes_count} episodes`
  : null
```

**Display Formats:**
- **With TMDB data:** "45/276 episodes" (shows progress)
- **Without TMDB data:** "45 episodes" (shows count only)
- **Movies:** No episode display

**Success Criteria:**
- ✅ Shows "X/Y episodes" when total is known
- ✅ Shows "X episodes" when total unknown
- ✅ No display for movies
- ✅ Looks good visually

---

### Phase 6: Testing (30 minutes)

**Task:** Test the complete feature end-to-end

**Test Scenarios:**

1. **Happy Path:**
   - Import CSV with known series (e.g., "Breaking Bad")
   - Verify TMDB called and data stored
   - Verify display shows "X/Y episodes"

2. **Unknown Series:**
   - Import CSV with obscure series name
   - Verify import completes
   - Verify display shows "X episodes" (fallback)

3. **TMDB Failure:**
   - Temporarily break TMDB API key
   - Verify import still completes
   - Verify error logged
   - Verify display uses fallback

4. **Rate Limiting:**
   - Import large CSV (100+ series)
   - Verify caching reduces API calls
   - Verify no rate limit errors

5. **Mixed Content:**
   - Import CSV with movies and TV series
   - Verify TMDB only called for TV series
   - Verify movies unaffected

**Success Criteria:**
- ✅ All test scenarios pass
- ✅ No errors in logs (except expected ones)
- ✅ Display works correctly
- ✅ Import performance acceptable

---

### Phase 7: Railway Deployment (15 minutes)

**Task:** Deploy to Railway and test in production

**Steps:**
1. Run migration locally first: `alembic upgrade head`
2. Commit all changes
3. Push to GitHub (triggers Railway deploy)
4. Watch Railway logs for migration success
5. Run test import in production
6. Verify episode counts appear correctly

**Success Criteria:**
- ✅ Migration runs successfully on Railway
- ✅ TMDB API calls work in production
- ✅ Episode counts display correctly
- ✅ No errors in production logs

---

## 🚧 Potential Blockers & Solutions

### Blocker 1: TMDB API Rate Limits
**Problem:** Too many API calls during large imports  
**Solution:** 
- Implement aggressive caching (7 days)
- Add request throttling (max 40 requests/10 seconds)
- Queue TMDB calls for background processing (future: Celery)

### Blocker 2: Series Name Matching
**Problem:** CSV titles don't match TMDB names exactly  
**Solution:**
- Clean series names before search (remove year, country codes)
- Try multiple search strategies (exact, fuzzy)
- Log mismatches for manual review
- Consider manual mapping table (future)

### Blocker 3: TMDB API Key Missing
**Problem:** TMDB_API_KEY not configured on Railway  
**Solution:**
- Check Railway environment variables
- Add key if missing (get from tmdb.org)
- Verify key works with test request

### Blocker 4: Migration Fails on Railway
**Problem:** Database migration errors in production  
**Solution:**
- Test migration extensively locally first
- Have rollback plan ready
- Monitor Railway logs during deployment
- Can manually run migration if auto-migration fails

---

## 📊 Success Metrics

### Feature Complete When:
- ✅ Database has TMDB columns
- ✅ TMDB service fetches episode counts
- ✅ Import integrates TMDB lookups
- ✅ API returns episode counts
- ✅ Frontend displays "X/Y episodes"
- ✅ All tests pass
- ✅ Deployed to Railway
- ✅ User verifies it works

### Quality Gates:
- ✅ No breaking changes to existing features
- ✅ Import still works if TMDB fails
- ✅ Performance acceptable (<5s per series lookup with caching)
- ✅ Error handling comprehensive
- ✅ Logging provides good visibility

---

## 🎯 Alternative Tasks (If Blocked)

### Option A: Sentry Error Monitoring (2-3 hours)
If TMDB API unavailable or blocked:
1. Sign up for Sentry account (sentry.io)
2. Install Sentry SDK in backend: `pip install sentry-sdk[fastapi]`
3. Install Sentry SDK in frontend: `npm install @sentry/nextjs`
4. Configure both with DSN from Sentry
5. Test error reporting
6. Deploy to Railway

**Priority:** HIGH (good for production stability)

### Option B: Performance Monitoring (2 hours)
If waiting for Railway deployment:
1. Set up Railway metrics dashboard
2. Configure slow query logging in PostgreSQL
3. Add performance timing to critical endpoints
4. Review and optimize slow queries
5. Document findings

**Priority:** MEDIUM (good for optimization)

### Option C: Frontend Tests (4+ hours)
If feature work blocked:
1. Set up Jest and React Testing Library
2. Write tests for critical components
3. Add test scripts to package.json
4. Document testing approach
5. Run tests in CI (future)

**Priority:** LOW (good but time-consuming)

---

## 📋 Pre-Session Checklist

Before starting the session, verify:

- ✅ Railway production is stable (no ongoing issues)
- ✅ Git repository is clean (no uncommitted changes)
- ✅ Documentation is up to date
- ✅ TMDB API key is available
- ✅ Local development environment works
- ✅ PostgreSQL and Redis running locally
- ✅ You have Railway access

---

## 🎓 Learning Objectives

### Technical Skills:
- Working with external APIs (TMDB)
- Database migrations in production
- Caching strategies with Redis
- Error handling for external services
- Progressive enhancement (works with/without TMDB data)

### Best Practices:
- Fail gracefully when external services are down
- Cache expensive operations
- Log for observability
- Test edge cases
- Don't block user flows on external dependencies

---

## 📝 Documentation Plan

### During Implementation:
- Comment complex TMDB search logic
- Document caching strategy
- Add API endpoint examples
- Update schema documentation

### After Completion:
- Update KNOWN_BUGS.md (mark FR-001 as complete)
- Update PROJECT_STATUS.md (Phase 9 progress)
- Create TMDB_INTEGRATION.md with details
- Update README.md with new feature

---

## 💡 Quick Start Guide for Tomorrow

### Step-by-Step:
1. **Pull latest code:** `git pull origin main`
2. **Start local services:** `docker-compose up -d` (PostgreSQL, Redis)
3. **Create migration:** `cd backend && alembic revision -m "add tmdb episode data"`
4. **Implement migration** (see Phase 1 details above)
5. **Test migration locally:** `alembic upgrade head`
6. **Implement TMDB service** (see Phase 2 details above)
7. **Test TMDB service manually** with a few series names
8. **Integrate into import** (see Phase 3 details above)
9. **Update frontend** (see Phase 5 details above)
10. **Test end-to-end locally**
11. **Deploy to Railway**
12. **Test in production**
13. **Document and celebrate!** 🎉

### Estimated Timeline:
- 09:00 - 09:30: Setup and migration (30 min)
- 09:30 - 11:30: TMDB service implementation (2 hours)
- 11:30 - 12:30: Import integration (1 hour)
- 12:30 - 13:00: Break
- 13:00 - 13:30: API updates (30 min)
- 13:30 - 14:30: Frontend changes (1 hour)
- 14:30 - 15:00: Testing (30 min)
- 15:00 - 15:15: Deploy and verify (15 min)
- 15:15 - 15:30: Documentation (15 min)

**Total: ~5 hours** (within 4-6 hour estimate)

---

## 🚀 Let's Build Tomorrow!

**Feature:** TMDB Episode Count Lookup  
**User Impact:** See accurate progress like "45/276 episodes watched"  
**Technical Challenge:** External API integration with proper error handling  
**Learning Value:** High - great patterns for future integrations

**Ready to start?** See you tomorrow with 10 lives! ✨

---

**Document Created:** November 8, 2025  
**Next Session:** November 9, 2025  
**Status:** 🟢 READY

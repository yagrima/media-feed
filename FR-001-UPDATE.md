### FR #1: TMDB API Episode Count Lookup (Gesamtzahl der Episoden ermitteln)
**ID:** FR-001  
**Status:** ✅ **IMPLEMENTED** - November 8, 2025  
**Commit:** 4862119  
**Migration:** 007_add_tmdb_episode_counts.py  
**Category:** Enhancement  

**Description:**
Automatic online lookup for total episode counts using TMDB API - **ALREADY WORKING IN PRODUCTION**

**What Was Implemented:**
✅ Query TMDB API during show import for total seasons/episodes  
✅ Store metadata in database (`total_seasons`, `total_episodes`, `last_tmdb_update` columns)  
✅ Cache results to avoid API rate limits  
✅ Fall back to CSV data if API unavailable  

**Files Implemented:**
- `backend/alembic/versions/007_add_tmdb_episode_counts.py` - Database migration
- `backend/app/services/tmdb_client.py` - `get_series_episode_count()` method
- `backend/app/services/netflix_parser.py` - `_enrich_with_tmdb_data()` auto-enrichment
- `backend/app/db/models.py` - Added `total_seasons`, `total_episodes`, `last_tmdb_update` columns

**What's NOT Yet Implemented (See FR-002):**
❌ Periodic background updates (weekly/monthly refresh for ongoing shows)  
❌ Automatic detection of new seasons  
❌ Celery background jobs

**Note to maintainers:** This feature is COMPLETE and working. Update KNOWN_BUGS.md to reflect this.

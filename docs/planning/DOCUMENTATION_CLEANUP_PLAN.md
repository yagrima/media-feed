# Documentation Cleanup & Consolidation Plan

**Created:** November 15, 2025  
**Status:** Planning Phase  
**Estimated Effort:** 4-6 hours

---

## Current State Analysis

### Documentation Files (93 total)
```
Total markdown files: 93
Core docs: 15
Archive/legacy: 20+
Session summaries: 10+
Feature planning: 8
Deployment guides: 6
Testing docs: 5
Duplicate/outdated: Unknown
```

### Key Issues

1. **Duplication:** Multiple files covering same topics (deployment, testing, status)
2. **Outdated:** Many docs reference old bugs/features that are fixed
3. **No Clear Structure:** No central index or navigation
4. **Scattered FRs:** Feature requests in multiple files (KNOWN_BUGS.md, USER_STORIES.md, etc.)
5. **Session Dumps:** Raw session summaries not integrated into main docs
6. **No Versioning:** Hard to tell what's current vs historical

---

## Proposed Structure

### `/docs/` - Main Documentation
```
README.md                    # Project overview + quick start
ARCHITECTURE.md              # System design & tech stack
API.md                       # API endpoints & schemas
DATABASE.md                  # Schema & models
DEPLOYMENT.md                # Production deployment guide
SECURITY.md                  # Security policies & audit results
CHANGELOG.md                 # Version history
```

### `/docs/development/` - Developer Guides
```
SETUP.md                     # Local development setup
CONTRIBUTING.md              # Contribution guidelines
TESTING.md                   # Test strategy & running tests
DEBUGGING.md                 # Common issues & solutions
```

### `/docs/features/` - Feature Documentation
```
CSV_IMPORT.md                # CSV import feature
NOTIFICATIONS.md             # Notification system
AUDIBLE_EXTENSION.md         # Browser extension
TMDB_INTEGRATION.md          # TMDB API integration
```

### `/docs/planning/` - Planning Documents
```
USER_STORIES.md              # User stories (keep current)
ROADMAP.md                   # Future features & timeline
KNOWN_BUGS.md                # Active bugs (keep current)
BACKLOG.md                   # Low-priority FRs
```

### `/docs/archive/` - Historical Records
```
sessions/                    # Session summaries (dated)
decisions/                   # Architecture decision records
migrations/                  # Migration notes
audits/                      # Security audit reports
```

---

## Cleanup Tasks

### Phase 1: Consolidation (2 hours)

**1.1 Merge Deployment Docs** (30 min)
- Consolidate: RAILWAY_DEPLOYMENT_GUIDE.md, RAILWAY_TROUBLESHOOTING_TIPS.md, RAILWAY_VERIFICATION_CHECKLIST.md
- Into: `/docs/DEPLOYMENT.md`
- Archive originals

**1.2 Merge Status Docs** (30 min)
- Consolidate: CURRENT_STATUS.md, PROJECT_STATUS.md, current-project-status.json
- Into: Single `STATUS.md` with JSON export
- Archive originals

**1.3 Consolidate Testing Docs** (30 min)
- Merge: E2E_TEST_PLAN.md, INTEGRATION_TEST_PLAN.md, TEST_SUITE_COMPLETE.md, MANUAL_TESTING_ANLEITUNG.md
- Into: `/docs/development/TESTING.md`

**1.4 Archive Session Summaries** (30 min)
- Move all `SESSION_SUMMARY_*.md` to `/docs/archive/sessions/`
- Keep only key decisions in main docs
- Create index: `/docs/archive/sessions/INDEX.md`

### Phase 2: Restructure (2 hours)

**2.1 Create Master README** (30 min)
- Overview of project
- Quick start guide
- Link to all major docs
- Status badges (build, tests, security)

**2.2 Feature Documentation** (1 hour)
- Extract feature docs from various files
- Create dedicated feature pages
- Update with current implementation status
- Link from main README

**2.3 Planning Docs Cleanup** (30 min)
- Review USER_STORIES.md for outdated items
- Move completed stories to archive
- Update KNOWN_BUGS.md with current status
- Create ROADMAP.md from scattered FRs

### Phase 3: Cleanup & Polish (2 hours)

**3.1 Remove Duplicates** (1 hour)
- Identify truly duplicate files
- Merge content or delete
- Update all references

**3.2 Update Links** (30 min)
- Find all internal doc links
- Update to new structure
- Fix broken links

**3.3 Add Navigation** (30 min)
- Create docs/INDEX.md with full tree
- Add "Related Docs" sections to each file
- Create quick reference card

---

## Files to Archive (Candidates)

### Session Dumps (move to archive)
- SESSION_SUMMARY_NOV_11_2025.md
- SESSION_SUMMARY_NOV_11_2025_FINAL.md
- SESSION_SUMMARY_NOV_8_2025.md
- DEV_SESSION_SUMMARY_OCT_20.md
- AUDIBLE_SESSION_FINAL_SUMMARY.md
- AUDIBLE_SESSION_STATUS_NOV_12.md

### Completed Implementation (archive)
- FRONTEND_DEVELOPMENT_COMPLETE.md
- AUDIBLE_BACKEND_COMPLETE.md
- AUDIBLE_INTEGRATION_COMPLETE.md
- INTEGRATION_VERIFICATION_REPORT.md
- EPISODE_TRACKING_IMPLEMENTATION.md
- TEST_SUITE_COMPLETE.md

### Redundant Deployment (merge)
- RAILWAY_DEPLOYMENT_TODO.md (outdated)
- RAILWAY_VERIFICATION_CHECKLIST.md (merge)
- RAILWAY_TROUBLESHOOTING_TIPS.md (merge)

### Status Snapshots (merge/archive)
- PRODUCTION_READY_SUMMARY.md
- PUSH_SUCCESS_SUMMARY.md
- FINAL_INTEGRATION_SUMMARY.md

### Old Planning (archive if not actively used)
- MVP_ROADMAP.md (if outdated)
- NEXT_SESSION_PLAN.md (merge into ROADMAP)

---

## Files to Keep (Core Documentation)

### Critical - Do Not Archive
- README.md
- USER_STORIES.md (active planning)
- KNOWN_BUGS.md (active tracking)
- CURRENT_STATUS.md (keep latest only)
- ARCHITECTURE_GUIDELINES.md
- TECHNICAL_SPEC v1.1.md
- SECURITY_AUDIT_NOV_11_2025.md
- SECURITY_FINDINGS.md
- DATABASE_SETUP.md
- QUICKSTART.md

### Feature Docs - Keep & Organize
- AUDIBLE_INTEGRATION_PIVOT.md (important decision record)
- AUDIBLE_INTEGRATION_STRATEGY.md (current approach)
- AUDIBLE_TESTING_GUIDE.md (active use)

---

## Success Criteria

✅ All docs organized into clear folder structure  
✅ No duplicate content across files  
✅ Clear navigation from main README  
✅ Session summaries archived but accessible  
✅ Planning docs current and actionable  
✅ Feature docs match implementation status  
✅ All internal links working  
✅ Total file count reduced by 30%  

---

## Execution Plan

**Who:** AI Assistant + User Review  
**When:** Next available session  
**Duration:** 4-6 hours  
**Dependencies:** None (can start anytime)  
**Risk:** Low (git-tracked, can revert)  

**Process:**
1. Create `/docs/` structure
2. Move files one category at a time
3. Update content while moving
4. User reviews each category
5. Update all references
6. Commit changes

---

## Notes

- Keep git history intact (use `git mv` for renames)
- Archive = move to `/docs/archive/`, don't delete
- Every moved file gets redirect comment at old location
- Create `/docs/INDEX.md` as single source of truth for navigation
- Update PR templates to reference new structure

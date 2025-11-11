# E2E Test Plan with Playwright

**Goal:** Prevent critical bugs like today's Login regression and Token storage issues

**Duration:** ~4-5 hours  
**Priority:** HIGH  
**Status:** In Progress

---

## Why E2E Tests Now?

### Problems We Could Have Caught Today:

**1. Login Regression (BUG-005):**
- Token storage inconsistency
- Login success but no redirect
- Would have been caught by Auth Flow test

**2. Requirements.txt Corruption:**
- Deployment crash
- Would have been caught by basic smoke test

**3. TMDB Integration Issues:**
- Episode counts not showing
- Would have been caught by Import test

---

## Test Priority

### Critical Tests (Must Have):

**Test 1: Authentication Flow** ✅ Top Priority
- Register new user
- Logout
- Login with same user
- Verify dashboard redirect
- Verify token persistence
- **Prevents:** BUG-005 type issues

**Test 2: CSV Import & Library Display**
- Upload Netflix CSV
- Wait for import completion
- Verify media appears in library
- Verify episode counts (X/Y format)
- **Prevents:** TMDB integration breaks

**Test 3: Smoke Test**
- Backend health endpoint responds
- Frontend loads
- Critical routes accessible
- **Prevents:** Deployment crashes

### Secondary Tests (Nice to Have):

**Test 4: Media Filtering**
- Filter by Movies/TV Series
- Search functionality
- Pagination

**Test 5: Notifications**
- Notification badge shows count
- Notifications page loads

---

## Implementation Plan

### Phase 1: Setup (30 minutes)
- Install Playwright
- Configure for Next.js
- Setup test database/environment
- Create base test utilities

### Phase 2: Critical Tests (2-3 hours)
- Test 1: Auth Flow (1 hour)
- Test 2: CSV Import (1 hour)
- Test 3: Smoke Test (30 min)
- Debug and fix issues (30 min)

### Phase 3: CI Integration (1 hour - Optional)
- GitHub Actions workflow
- Run tests on PR
- Test artifacts/screenshots

### Phase 4: Documentation (30 min)
- README for running tests
- Contribution guidelines
- Test writing guide

---

## Technical Setup

### Tools:
- **Playwright** - E2E testing framework
- **@playwright/test** - Test runner
- **playwright-chromium** - Browser automation

### Test Structure:
```
frontend/
  tests/
    e2e/
      auth.spec.ts          # Authentication tests
      import.spec.ts        # CSV import tests
      smoke.spec.ts         # Basic health checks
      fixtures/
        test-import.csv     # Test CSV file
      helpers/
        auth-helpers.ts     # Reusable auth functions
        api-helpers.ts      # API interaction helpers
  playwright.config.ts      # Playwright configuration
```

### Environment:
- Test against: http://localhost:3000 (dev) or Railway (staging)
- Backend: http://localhost:8000 or Railway backend
- Test database: Separate from production
- Test user: test-e2e@example.com

---

## Expected Outcomes

### After Implementation:

**✅ Confidence in Deployments:**
- Tests run before every deploy
- Critical paths verified automatically
- Regressions caught early

**✅ Better Code Quality:**
- Forces thinking about user flows
- Documents expected behavior
- Easier refactoring with test safety net

**✅ Time Savings:**
- No more manual testing before deploy
- Faster debugging with test failures
- Reduced production bugs

### Success Metrics:

- ✅ All 3 critical tests passing
- ✅ Test run time < 2 minutes
- ✅ 0 flaky tests (consistent results)
- ✅ Easy to run locally (`npm test:e2e`)

---

## Risks & Mitigation

**Risk 1: Flaky Tests**
- Mitigation: Proper waits, stable selectors
- Use `data-testid` attributes

**Risk 2: Slow Tests**
- Mitigation: Parallel execution
- Mock external APIs where possible

**Risk 3: Maintenance Burden**
- Mitigation: Keep tests focused
- Only test critical paths initially

---

## Next Steps

1. **Install Playwright** in frontend
2. **Create first test:** Auth Flow
3. **Run and verify** it catches yesterday's bug
4. **Iterate:** Add more tests based on failures

---

## Commands

```bash
# Install
npm install -D @playwright/test

# Run tests
npm run test:e2e

# Run tests in UI mode (debugging)
npm run test:e2e:ui

# Run specific test
npm run test:e2e -- auth.spec.ts

# Generate test code (Playwright Codegen)
npx playwright codegen http://localhost:3000
```

---

**Status:** Ready to implement
**Next:** Install Playwright and create first test

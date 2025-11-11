# E2E Tests with Playwright

End-to-end tests for Me Feed application to prevent regressions and ensure critical user flows work correctly.

## Why These Tests?

After experiencing critical bugs in production (BUG-005: Token Storage Issue, Requirements.txt crash), we implemented E2E tests to catch these issues before deployment.

**Tests Prevent:**
- Authentication regressions (login/logout/token issues)
- CSV import failures
- TMDB integration breaks
- Deployment crashes
- Critical page load failures

## Test Files

```
tests/e2e/
  ├── auth.spec.ts       # Authentication flow tests
  ├── import.spec.ts     # CSV import and library tests
  ├── smoke.spec.ts      # Fast health checks
  ├── fixtures/
  │   └── test-import.csv # Test CSV file
  └── helpers/
      └── auth-helpers.ts # Reusable auth utilities
```

## Running Tests

### Prerequisites

1. **Backend must be running** on http://localhost:8000
2. **Frontend dev server** (started automatically by Playwright)

### Start Backend

```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### Run Tests

```powershell
cd frontend

# Run all tests
npm run test:e2e

# Run specific test file
npm run test:e2e -- auth.spec.ts

# Run tests in UI mode (debugging)
npm run test:e2e:ui

# Run tests in debug mode (step-by-step)
npm run test:e2e:debug

# Run only smoke tests (fast)
npm run test:e2e -- smoke.spec.ts
```

### Test Against Railway (Production)

```powershell
cd frontend
$env:PLAYWRIGHT_BASE_URL = "https://proud-courtesy-production-992b.up.railway.app"
npm run test:e2e
```

## Test Categories

### 🔐 Authentication Tests (`auth.spec.ts`)

**What it tests:**
- User registration
- Logout functionality
- Login with same user (BUG-005 scenario)
- Token persistence after page reload
- Invalid credentials handling
- Password validation

**Why it matters:**
- Prevents BUG-005 type issues (token reuse after logout)
- Ensures users can actually log in after registering
- Validates security requirements

**Run time:** ~30 seconds

### 📥 Import Tests (`import.spec.ts`)

**What it tests:**
- CSV file upload
- Import processing
- Media display in library
- TMDB episode counts (FR-001)
- Media type filtering

**Why it matters:**
- Prevents TMDB integration breaks
- Ensures import feature works end-to-end
- Validates episode count display

**Run time:** ~45 seconds

### 💨 Smoke Tests (`smoke.spec.ts`)

**What it tests:**
- Backend health endpoint responds
- Frontend pages load
- Critical routes accessible
- API response time < 1 second

**Why it matters:**
- Catches deployment crashes immediately
- Fast feedback (runs in ~10 seconds)
- Should run first in CI before full suite

**Run time:** ~10 seconds

## Debugging Failed Tests

### Screenshots and Videos

When tests fail, Playwright automatically captures:
- **Screenshots** of failure moment
- **Videos** of entire test run
- **Trace files** for step-by-step debugging

Find them in: `frontend/test-results/`

### View Test Results

```powershell
npx playwright show-report
```

This opens an HTML report with:
- Test pass/fail status
- Screenshots on failure
- Video recordings
- Network logs
- Console logs

### Debug Mode

Run tests in debug mode to step through:

```powershell
npm run test:e2e:debug -- auth.spec.ts
```

This opens Playwright Inspector where you can:
- Step through test line by line
- Inspect page state
- Modify selectors
- Try commands interactively

### Common Issues

**Issue: Tests timeout waiting for element**
- Check if element selector is correct
- Verify element is actually visible (not hidden by CSS)
- Check network requests in test report
- Try increasing timeout: `{ timeout: 15000 }`

**Issue: "ECONNREFUSED" error**
- Backend is not running
- Check backend is on correct port (8000)
- Verify DATABASE_URL is set correctly

**Issue: Flaky tests (sometimes pass, sometimes fail)**
- Add explicit waits: `await page.waitForTimeout(500)`
- Use `waitForLoadState('networkidle')`
- Check for race conditions

## CI Integration (Future)

### GitHub Actions Workflow

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - name: Install dependencies
        run: npm ci
      - name: Install Playwright
        run: npx playwright install --with-deps
      - name: Run tests
        run: npm run test:e2e
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: test-results/
```

## Writing New Tests

### Best Practices

**1. Use data-testid attributes**

Add to components for stable selectors:
```tsx
<button data-testid="login-button">Login</button>
```

Then in test:
```typescript
await page.click('[data-testid="login-button"]');
```

**2. Generate unique test data**

```typescript
const timestamp = Date.now();
const testUser = {
  email: `test-${timestamp}@example.com`,
  password: 'Test123!'
};
```

**3. Use helper functions**

```typescript
import { registerUser, loginUser } from './helpers/auth-helpers';

test('my test', async ({ page }) => {
  const user = generateTestUser();
  await registerUser(page, user);
  // Test logic here
});
```

**4. Clean up after tests**

```typescript
test.afterEach(async ({ page }) => {
  // Logout or clean up
  await logoutUser(page);
});
```

## Test Naming Convention

```typescript
test('should [action] when [condition]', async ({ page }) => {
  // Example: 'should redirect to dashboard when login succeeds'
});
```

## Performance

**Current test suite runtime:**
- Smoke tests: ~10 seconds
- Auth tests: ~30 seconds
- Import tests: ~45 seconds
- **Total: ~1.5 minutes**

**Target:** Keep under 3 minutes for quick feedback

## Maintenance

**When to update tests:**
- UI changes (new selectors, different flow)
- Feature additions (new pages, functionality)
- Bug fixes (add regression test)

**Test priority:**
1. **Critical**: Auth flow, Smoke tests
2. **High**: Import flow, Core features
3. **Medium**: Filters, Search, Secondary features
4. **Low**: Nice-to-have features

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [E2E Testing Guide](https://playwright.dev/docs/writing-tests)

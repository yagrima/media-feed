# Architecture & Development Guidelines - Me(dia) Feed

**Last Updated**: November 11, 2025  
**Version**: 1.2.0

**Major Updates (v1.2.0)**:
- Comprehensive Testing Strategy (Test Pyramid, TDD, Bug-Fix Protocol)
- E2E Testing Guidelines (Playwright)
- Bug Prevention through Regression Tests
- Real-world examples from BUG-005 incident

---

## Development Environment Standards

### Operating System & Tools
- **OS**: Windows 10/11
- **Shell**: PowerShell (primary for all scripts and automation)
- **Browser**: Opera (for development and testing)
- **IDE**: VS Code with extensions:
  - Python
  - TypeScript/JavaScript
  - Docker
  - PostgreSQL

### Why These Standards?

**PowerShell**:
- Native Windows integration
- Consistent scripting environment
- Better handling of paths with spaces
- Docker commands work reliably

**Opera**:
- Good developer tools
- Privacy-focused
- Fast performance
- Standards-compliant

---

## Code Style Guidelines

### General Principles

#### NO EMOJIS OR UNICODE CHARACTERS
**CRITICAL RULE**: Never use emojis or Unicode characters in:
- PowerShell scripts (.ps1 files) - **STRICTLY FORBIDDEN**
- Source code
- Console output
- Log messages
- Comments in code files
- Script output messages

**Forbidden Characters in PowerShell:**
- ❌ Emojis: ✅ ✓ ❌ ✗ 🚀 🔍 ⚠️ ℹ️ etc.
- ❌ Unicode symbols: → ➜ • ● ○ etc.
- ❌ Special quotes: " " ' '
- ❌ Any non-ASCII characters

**Why This is Critical:**
- PowerShell on Windows has severe encoding issues with Unicode
- Causes parse errors: "The string is missing the terminator"
- Script execution failures that waste hours of debugging
- Has caused multiple production issues

**Correct Approach for PowerShell:**
```powershell
# GOOD - ASCII only
Write-Host "[OK] Operation completed" -ForegroundColor Green
Write-Host "[ERROR] Failed to connect" -ForegroundColor Red
Write-Host "[WARNING] Check configuration" -ForegroundColor Yellow
Write-Host "Step 1/3 -> Processing..." -ForegroundColor Cyan

# BAD - Contains Unicode (WILL BREAK)
Write-Host "✅ Operation completed" -ForegroundColor Green
Write-Host "❌ Failed to connect" -ForegroundColor Red  
Write-Host "⚠️ Check configuration" -ForegroundColor Yellow
Write-Host "Step 1/3 ➜ Processing..." -ForegroundColor Cyan
```

**Reason**: Emojis and Unicode cause encoding issues in PowerShell and will break scripts.

**Correct**:
```powershell
Write-Host "Extracting secrets..." -ForegroundColor Cyan
Write-Host "ERROR: File not found" -ForegroundColor Red
```

**Incorrect**:
```powershell
Write-Host "🔐 Extracting secrets..." -ForegroundColor Cyan
Write-Host "❌ ERROR: File not found" -ForegroundColor Red
```

#### Text Formatting Alternatives
Instead of emojis, use:
- **Color coding**: `-ForegroundColor` in PowerShell
- **Text symbols**: `[OK]`, `[ERROR]`, `[WARNING]`, `>>>`, `---`
- **ASCII art**: For section dividers
- **Clear labels**: "SUCCESS:", "ERROR:", "INFO:"

---

## Scripting Standards

### PowerShell Scripts

**File Convention**:
```
scripts/
├── extract-secrets-for-railway.ps1
├── start-backend.ps1
└── deploy-production.ps1
```

**Script Header Template**:
```powershell
# Script Name and Purpose
# Description of what the script does

param(
    [Parameter(Mandatory=$false)]
    [string]$ConfigPath = "default-value"
)

# Main script logic
Write-Host "Starting script..." -ForegroundColor Cyan
```

**Error Handling**:
```powershell
if (-not (Test-Path $path)) {
    Write-Host "ERROR: File not found at: $path" -ForegroundColor Red
    exit 1
}
```

**No Bash/Sh Scripts**: 
- For cross-platform needs, use Python scripts instead
- PowerShell Core (pwsh) works on Linux/Mac if needed

---

## Backend Architecture

### FastAPI Structure
```
backend/app/
├── api/              # Route handlers (thin layer)
├── services/         # Business logic
├── db/               # Models, database layer
├── core/             # Config, security, middleware
├── schemas/          # Pydantic models
└── workers/          # Background tasks (Celery)
```

**Principles**:
- **Async by default**: Use `async def` for all API handlers
- **Dependency injection**: Use FastAPI's `Depends()`
- **Pydantic validation**: All input/output via Pydantic models
- **Service layer**: Keep business logic out of routes

### Database Patterns
```python
# Good: Service handles business logic
class UserService:
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate):
        # Validation
        # Password hashing
        # Database operations
        return user

# Bad: Business logic in route
@router.post("/users")
async def create_user(user: UserCreate):
    hashed_pw = hash_password(user.password)  # Logic in route!
```

---

## Frontend Architecture

### Next.js 14 App Router Structure
```
frontend/app/
├── (auth)/           # Auth group (shared layout)
│   ├── login/
│   └── register/
├── (dashboard)/      # Dashboard group
│   ├── library/
│   ├── import/
│   └── notifications/
├── api/              # API route handlers
└── components/       # Reusable components
```

**Principles**:
- **Server Components default**: Use Client Components only when needed
- **Route groups**: Organize by feature/layout
- **API layer**: Centralize API calls in `lib/api/`
- **Type safety**: TypeScript strict mode

---

## Security Architecture

### Secrets Management

**Development**:
```
../Media Feed Secrets/
├── secrets/
│   ├── jwt_private.pem
│   ├── jwt_public.pem
│   ├── encryption.key
│   └── secret_key.txt
└── config/
    └── secrets.json
```

**Production (Railway/Cloud)**:
- Secrets as environment variables
- Startup script converts ENV to temp files
- Files created in `/tmp/secrets` (ephemeral)

### Authentication Flow
1. User login → JWT access token (15 min) + refresh token (7 days)
2. Access token in memory (frontend)
3. Refresh token in httpOnly cookie
4. Token refresh before expiration
5. RS256 asymmetric signing (not HS256)

---

## Testing Standards

**Philosophy**: Testing is not optional - it prevents production bugs and saves debugging time.

### Test Pyramid

```
        E2E Tests (12+)           ← Critical user flows, slow
            ↑
     Integration Tests (TBD)       ← API + Database, moderate
            ↑
      Unit Tests (71+)             ← Functions, fast
```

**Balance**:
- **Unit Tests (70%)**: Fast, isolated, test individual functions
- **Integration Tests (20%)**: Test components working together
- **E2E Tests (10%)**: Test complete user workflows

---

### When to Write Tests

#### Test-First (TDD) - REQUIRED for:
1. **Security Features**
   - Authentication/Authorization
   - Password validation
   - Token management
   - Session handling
   - **Example**: BUG-005 would have been caught by E2E auth test

2. **Data Integrity**
   - CSV import parsing
   - Database operations
   - User data handling

3. **Critical Business Logic**
   - Episode tracking calculations
   - Notification triggers
   - Sequel detection

#### Test-Alongside - RECOMMENDED for:
- New API endpoints
- New UI components
- Service layer methods
- Utility functions

#### Test-After - ACCEPTABLE for:
- Experimental features
- Prototypes
- Non-critical UI tweaks

---

### Bug-Fix Protocol (MANDATORY)

**Every bug fix MUST include a regression test**:

```python
# Step 1: Write failing test that reproduces the bug
def test_bug_005_token_reuse_after_logout():
    """
    BUG-005: User A logout → User B register → logged in as User A
    This test ensures token cleanup happens before new registration
    """
    # Arrange
    user_a = create_test_user("user_a@test.com")
    login(user_a)
    
    # Act
    logout()
    user_b = register_new_user("user_b@test.com")
    
    # Assert
    current_user = get_current_user()
    assert current_user.email == "user_b@test.com"  # Not user_a!

# Step 2: Fix the bug
# (Implementation changes...)

# Step 3: Verify test passes
# pytest tests/test_auth_regression.py -v
```

**Commit Message Format**:
```
fix: [BUG-XXX] Brief description

- Root cause analysis
- Fix implementation
- Regression test added

Test: test_bug_xxx_description_of_issue

Co-authored-by: factory-droid[bot] <...>
```

**Why This Matters**:
- Prevents the same bug from recurring
- Documents the issue in code
- Builds confidence in codebase stability
- **Real Example**: BUG-005 (token reuse) now has E2E test protection

---

### Unit Tests (Backend)

**Test Naming Convention**:
```python
# Pattern: test_<function>_<scenario>_<expected_result>
def test_create_user_with_valid_data_succeeds():
    # Arrange
    user_data = UserCreate(
        email="test@example.com",
        password="SecurePass123!"
    )
    
    # Act
    result = await UserService.create_user(db, user_data)
    
    # Assert
    assert result.email == "test@example.com"
    assert result.is_active is True

def test_create_user_with_weak_password_fails():
    # Arrange
    user_data = UserCreate(
        email="test@example.com",
        password="weak"
    )
    
    # Act & Assert
    with pytest.raises(ValidationError):
        await UserService.create_user(db, user_data)
```

**Coverage Requirements**:
- Services: 90%+
- API routes: 80%+
- Utility functions: 100%
- Security functions: 100%

**Test Organization**:
```
backend/tests/
├── test_auth_service.py      # Authentication logic
├── test_media_service.py     # Media business logic
├── test_import_service.py    # CSV import
├── test_security_controls.py # Security validations
└── test_regression/          # Bug-specific tests
    ├── test_bug_005.py
    └── test_bug_002.py
```

---

### Unit Tests (Frontend)

**Component Testing with React Testing Library**:
```typescript
// Test user interactions, not implementation details
describe('LoginForm', () => {
  it('submits form with valid credentials', async () => {
    // Arrange
    const mockLogin = jest.fn();
    render(<LoginForm onLogin={mockLogin} />);
    
    // Act
    await userEvent.type(
      screen.getByLabelText(/email/i),
      'test@example.com'
    );
    await userEvent.type(
      screen.getByLabelText(/password/i),
      'SecurePass123!'
    );
    await userEvent.click(screen.getByRole('button', { name: /login/i }));
    
    // Assert
    expect(mockLogin).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'SecurePass123!'
    });
  });

  it('shows error message on invalid credentials', async () => {
    // Test implementation
    const { findByText } = render(<LoginForm />);
    // ... submit with invalid data
    expect(await findByText(/invalid credentials/i)).toBeInTheDocument();
  });
});
```

**What to Test**:
- User interactions (clicks, form submissions)
- Conditional rendering
- Error states
- Loading states
- Accessibility (ARIA labels, keyboard navigation)

**What NOT to Test**:
- Implementation details (state variables, internal functions)
- External library behavior
- Styling/CSS

---

### E2E Tests (Playwright)

**Purpose**: Test critical user workflows that must never break

**Test Categories**:

#### 1. Authentication Flow (CRITICAL)
```typescript
// frontend/tests/e2e/auth.spec.ts
test('complete auth flow: register → logout → login', async ({ page }) => {
  const user = generateTestUser();
  
  // Register new user
  await page.goto('/register');
  await page.fill('input[name="email"]', user.email);
  await page.fill('input[name="password"]', user.password);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/.*dashboard/);
  
  // Logout
  await page.click(`text=${user.email}`);
  await page.click('text=Logout');
  await expect(page).toHaveURL(/.*login/);
  
  // Login (THIS STEP CAUGHT BUG-005!)
  await page.fill('input[name="email"]', user.email);
  await page.fill('input[name="password"]', user.password);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/.*dashboard/);
  
  // Verify correct user logged in
  await expect(page.getByText(user.email)).toBeVisible();
});
```

**Why This Test Matters**: Caught BUG-005 (token reuse after logout)

#### 2. Smoke Tests (FAST)
```typescript
// frontend/tests/e2e/smoke.spec.ts
test('backend health endpoint responds', async ({ request }) => {
  const response = await request.get(`${apiUrl}/health`);
  expect(response.ok()).toBeTruthy();
  expect(await response.json()).toHaveProperty('status', 'healthy');
});
```

#### 3. Import Flow
```typescript
// frontend/tests/e2e/import.spec.ts
test('CSV import shows TMDB episode counts', async ({ page }) => {
  // Upload test CSV
  await page.setInputFiles('input[type="file"]', testCsvPath);
  
  // Wait for import completion
  await expect(page.getByText(/success/i)).toBeVisible({ timeout: 30000 });
  
  // Verify episode counts format (X/Y episodes)
  await page.goto('/library');
  const episodePattern = /\d+\/\d+\s+episodes/i;
  await expect(page.locator('text=' + episodePattern).first()).toBeVisible();
});
```

**E2E Test Guidelines**:
- Keep tests independent (no shared state)
- Use unique test data per run (timestamps in emails)
- Clean up test data if possible
- Run smoke tests first (fast failure)
- **Max duration**: 2-3 minutes for full suite

**When to Run E2E Tests**:
- ✅ Before deploying to production
- ✅ After fixing critical bugs
- ✅ When modifying auth flow
- ✅ In CI/CD pipeline (future)

**Documentation**: See `frontend/tests/e2e/README.md`

---

### Integration Tests

**Purpose**: Test components working together (API + Database + Services)

```python
# Example: Test full CSV import flow
async def test_import_netflix_csv_with_tmdb_enrichment():
    # Arrange
    csv_content = "Title,Date\nBreaking Bad,01/01/2023"
    user = await create_test_user()
    
    # Act
    import_job = await import_service.import_csv(
        db=db,
        user_id=user.id,
        csv_content=csv_content
    )
    
    # Assert
    assert import_job.status == "completed"
    media = await db.execute(
        select(Media).where(Media.title == "Breaking Bad")
    )
    assert media.total_episodes is not None  # TMDB enriched
```

**Integration Test Scope**:
- API endpoint → Service → Database
- Service → External API (TMDB) → Cache (Redis)
- Background job → Database → Notification

---

### Test Data Management

**Test Passwords** (Security Convention):
```
Location: Media Feed Secrets/config/test-config.json
```

**Never hardcode in tests**:
```python
# WRONG
password = "TestPassword123!"

# CORRECT
from tests.helpers import get_test_password
password = get_test_password()
```

**Test User Generation**:
```python
def generate_test_user():
    timestamp = int(time.time() * 1000)
    return {
        'email': f'test-{timestamp}@example.com',
        'password': get_test_password()
    }
```

**Test CSV Fixtures**:
```
frontend/tests/e2e/fixtures/
├── test-import.csv          # Valid CSV
├── invalid.csv              # Malformed CSV
└── large-import.csv         # Performance test
```

---

### Running Tests

**Backend Tests**:
```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth_service.py -v

# Run tests matching pattern
pytest -k "auth" -v

# Run only regression tests
pytest tests/test_regression/ -v
```

**Frontend Unit Tests** (Future):
```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

**E2E Tests**:
```bash
cd frontend

# Run all E2E tests
npm run test:e2e

# Run in UI mode (debugging)
npm run test:e2e:ui

# Run specific test
npm run test:e2e -- auth.spec.ts

# Run only smoke tests (fast)
npm run test:e2e -- smoke.spec.ts
```

---

### Test-Driven Development (TDD) Workflow

**For Critical Features**:

```
1. Write Test (RED)
   └─→ Test fails (expected)

2. Write Minimal Code (GREEN)
   └─→ Test passes

3. Refactor (REFACTOR)
   └─→ Tests still pass

4. Repeat
```

**Example: Adding Email Validation**:

```python
# Step 1: RED - Write failing test
def test_register_with_invalid_email_fails():
    invalid_email = "not-an-email"
    with pytest.raises(ValidationError):
        UserCreate(email=invalid_email, password="SecurePass123!")

# Step 2: GREEN - Add validation
class UserCreate(BaseModel):
    email: EmailStr  # Pydantic validator
    password: str

# Step 3: Test passes - Refactor if needed
```

---

### CI/CD Integration (Future)

**GitHub Actions Workflow** (Planned):
```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Backend Tests
        run: pytest --cov=app

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run E2E Tests
        run: npm run test:e2e
```

**Deployment Gate**:
- ✅ All unit tests pass
- ✅ E2E tests pass
- ✅ Coverage thresholds met
- → Deploy to Railway

---

### Testing Anti-Patterns (AVOID)

**❌ Don't**:
```python
# Testing implementation details
def test_user_service_uses_correct_hash_algorithm():
    # This couples test to implementation
    assert UserService.hash_algo == "argon2"

# Brittle selectors
await page.click('.css-abc123')  # Breaks when CSS changes

# Shared test state
global_test_user = create_user()  # Causes flaky tests

# Testing external libraries
def test_pydantic_validates_email():
    # Pydantic already has tests
```

**✅ Do**:
```python
# Test behavior, not implementation
def test_user_password_is_hashed():
    user = create_user(password="plain")
    assert user.password_hash != "plain"

# Stable selectors
await page.click('[data-testid="login-button"]')

# Independent tests
def test_login():
    user = create_user()  # Fresh user per test

# Test our code
def test_email_validation_rejects_invalid():
    with pytest.raises(ValidationError):
        UserCreate(email="invalid")
```

---

### Test Maintenance

**Keep Tests Green**:
- Fix failing tests immediately (don't accumulate)
- Update tests when requirements change
- Delete obsolete tests
- Refactor tests alongside code

**Test Review Checklist**:
- [ ] Test names clearly describe what's tested
- [ ] Tests are independent (no shared state)
- [ ] Assertions are specific and meaningful
- [ ] Test data doesn't expose real credentials
- [ ] Fast tests (< 1s for unit, < 30s for E2E)

---

### Real-World Examples from This Project

**BUG-005: Token Reuse Security Issue**
- **Problem**: No E2E test for logout → register flow
- **Solution**: Added auth.spec.ts test
- **Result**: Regression prevented forever

**TMDB Integration**
- **Problem**: Episode counts not showing
- **Solution**: Added import.spec.ts E2E test
- **Result**: Verifies "X/Y episodes" format

**Requirements.txt Corruption**
- **Problem**: No test for deployment dependencies
- **Lesson**: Add smoke test for critical dependencies
- **Future**: CI test for requirements.txt validity

---

### Coverage Requirements Summary

| Component | Unit | Integration | E2E | Total Target |
|-----------|------|-------------|-----|--------------|
| Auth | 90%+ | Required | Required | 95%+ |
| Services | 90%+ | Recommended | - | 90%+ |
| API Routes | 80%+ | Required | Smoke | 85%+ |
| UI Components | 70%+ | - | Critical flows | 75%+ |
| Utilities | 100% | - | - | 100% |

**Current Status**:
- Backend Unit: 71 tests (~65% coverage)
- Frontend Unit: 0 tests (TODO)
- E2E: 12 tests (critical flows covered)

**Next Goals**:
- Backend: Increase to 90% coverage
- Frontend: Add unit tests (Jest + RTL)
- E2E: Add import edge cases

---

## Deployment Architecture

### Railway.app Structure
```
Project: Me(dia) Feed
├── Backend Service (Dockerfile)
├── PostgreSQL Plugin (managed)
└── Redis Plugin (managed)
```

**Environment Variables**:
- `DATABASE_URL`: Auto-populated by Railway
- `REDIS_URL`: Auto-populated by Railway
- `JWT_PRIVATE_KEY`: Base64-encoded key content
- `JWT_PUBLIC_KEY`: Base64-encoded key content
- `ENCRYPTION_KEY`: Base64-encoded key
- `SECRET_KEY`: Random 32+ character string

---

## Git Workflow

### Commit Message Format
```
type: brief description

- Detail 1
- Detail 2

Co-authored-by: factory-droid[bot] <138933559+factory-droid[bot]@users.noreply.github.com>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `security`: Security improvement
- `refactor`: Code restructuring
- `test`: Test additions
- `docs`: Documentation
- `chore`: Maintenance

### Branch Strategy
- `main`: Production-ready code
- Feature branches: `feature/description`
- Hotfix branches: `hotfix/issue`

---

## Performance Guidelines

### Backend
- Database queries: Use indexes, limit N+1 queries
- Caching: Redis for frequently accessed data
- Background jobs: Celery for long-running tasks
- Rate limiting: Per-user and per-endpoint

### Frontend
- Code splitting: Dynamic imports for large components
- Image optimization: Next.js Image component
- API calls: React Query for caching and deduplication
- Bundle size: Monitor with webpack-bundle-analyzer

---

## Documentation Standards

### Code Comments
```python
# Good: Explains WHY, not WHAT
# Use JWT refresh to avoid frequent re-authentication
refresh_token = create_refresh_token(user.id)

# Bad: Explains obvious
# Create a refresh token
refresh_token = create_refresh_token(user.id)
```

### API Documentation
- FastAPI auto-generates OpenAPI docs
- Add descriptions to Pydantic models
- Document error responses
- Include examples

---

## Error Handling

### Backend
```python
# Structured error responses
class ErrorResponse(BaseModel):
    detail: str
    error_code: str
    timestamp: datetime

# Raise HTTP exceptions with context
if not user:
    raise HTTPException(
        status_code=404,
        detail="User not found",
        headers={"X-Error-Code": "USER_NOT_FOUND"}
    )
```

### Frontend
```typescript
// Global error boundary
export function ErrorBoundary({ error }: { error: Error }) {
  return (
    <div className="error-container">
      <h2>Something went wrong</h2>
      <p>{error.message}</p>
    </div>
  );
}
```

---

## Logging Standards

### Backend
```python
# Structured logging with context
logger.info("User login successful", extra={
    "user_id": user.id,
    "ip_address": request.client.host,
    "user_agent": request.headers.get("user-agent")
})
```

**Log Levels**:
- `DEBUG`: Development details
- `INFO`: Normal operations
- `WARNING`: Recoverable issues
- `ERROR`: Application errors
- `CRITICAL`: System failures

---

## Monitoring & Observability

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }
```

### Metrics to Track
- API response times
- Database query performance
- Background job queue length
- Error rates by endpoint
- User authentication failures

---

## Compliance & Best Practices

### OWASP Top 10 Coverage
- A01: Broken Access Control → JWT + role-based permissions
- A02: Cryptographic Failures → Encryption at rest + TLS
- A03: Injection → Pydantic validation + prepared statements
- A04: Insecure Design → Security-first architecture
- A05: Security Misconfiguration → Secure defaults
- A06: Vulnerable Components → Dependency scanning
- A07: Authentication Failures → Strong password policy + MFA ready
- A08: Data Integrity Failures → Input validation + HMAC
- A09: Logging Failures → Structured audit logging
- A10: SSRF → URL validation + allow-list

### GDPR Considerations
- User data export functionality
- Account deletion with cascade
- Consent tracking for notifications
- Data retention policies
- Privacy-first design

---

## Review Checklist

Before marking any task complete:
- [ ] Code follows architecture guidelines
- [ ] No emojis in code/scripts
- [ ] PowerShell scripts tested
- [ ] **Tests written and passing** (Unit + E2E for critical features)
- [ ] **Regression test added** (if fixing a bug)
- [ ] Security controls implemented
- [ ] Error handling present
- [ ] Logging added
- [ ] Documentation updated
- [ ] **E2E tests pass** (if auth/import/critical flow changed)

---

## Questions & Clarifications

For architectural decisions:
- Consult Technical Lead
- Document in ADR (Architecture Decision Record)
- Update this guide if pattern changes

For security concerns:
- Consult Security Expert
- Never skip security controls
- Document threat model

---

**Remember**: These guidelines exist to maintain consistency, prevent common issues (like emoji encoding problems), and ensure the project remains maintainable as it scales.

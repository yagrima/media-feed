# Architecture & Development Guidelines - Me(dia) Feed

**Last Updated**: October 27, 2025  
**Version**: 1.1.0

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

### Backend Tests
```python
# Test naming: test_<function>_<scenario>_<expected>
def test_create_user_with_valid_data_succeeds():
    # Arrange
    user_data = UserCreate(email="test@example.com", password="SecurePass123!")
    
    # Act
    result = await UserService.create_user(db, user_data)
    
    # Assert
    assert result.email == "test@example.com"
```

**Coverage Requirements**:
- Services: 90%+
- API routes: 80%+
- Utility functions: 100%

### Frontend Tests
```typescript
// Component tests with React Testing Library
describe('LoginForm', () => {
  it('submits form with valid credentials', async () => {
    // Test implementation
  });
});
```

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
- [ ] Tests written and passing
- [ ] Security controls implemented
- [ ] Error handling present
- [ ] Logging added
- [ ] Documentation updated

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

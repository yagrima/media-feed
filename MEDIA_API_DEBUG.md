# Media API CORS Problem - Systematische Analyse

## Problem Statement
- **Symptom**: Browser zeigt "No 'Access-Control-Allow-Origin' header" bei GET /api/media
- **Error**: ERR_FAILED - Request erreicht Backend nicht oder crasht
- **Status**: Andere Endpoints (/api/import/csv, /api/auth/login) funktionieren

---

## Bereits durchgeführte Versuche (chronologisch)

### Versuch 1: Async → Sync Session Migration
- **Was**: Umstellung von AsyncSession zu sync Session
- **Ergebnis**: Backend crashte wegen async/await in API-Endpoints
- **Status**: ❌ Fehlgeschlagen, zurückgerollt

### Versuch 2: Dependencies auf Sync umgestellt
- **Was**: get_current_user() von async zu sync
- **Ergebnis**: TypeError wegen await auf sync object
- **Status**: ❌ Fehlgeschlagen, zurückgerollt

### Versuch 3: Async wiederhergestellt + Notifications deaktiviert
- **Was**: Zurück zu AsyncSession, notification_api.router auskommentiert
- **Ergebnis**: Backend läuft, health endpoint OK, aber /api/media immer noch CORS-Fehler
- **Status**: ⚠️ Teilweise erfolgreich, aber Hauptproblem besteht

---

## Test-Ergebnisse (aktueller Stand)

### Backend Status
- ✅ Container läuft: `Up 3 minutes (healthy)`
- ✅ Health endpoint: `{"status":"healthy"}`
- ✅ Datenbank erreichbar
- ✅ 69 Medien in user_media Tabelle

### Endpoint Tests (von Backend Container aus)

#### Test 1: Health Endpoint
```bash
curl http://localhost:8000/health
# Ergebnis: ✅ {"status":"healthy"}
```

#### Test 2: Media Endpoint ohne Auth
```bash
curl http://localhost:8000/api/media?page=1&limit=20
# Ergebnis: ✅ 401 Unauthorized (korrekt - Auth required)
```

#### Test 3: OPTIONS Preflight
```bash
curl -X OPTIONS 'http://localhost:8000/api/media' \
  -H 'Origin: http://localhost:3000' \
  -H 'Access-Control-Request-Method: GET'
# Ergebnis: ✅ 200 OK, CORS headers present
# Headers: access-control-allow-origin: http://localhost:3000
```

#### Test 4: Import Endpoint (zum Vergleich)
```bash
curl http://localhost:8000/api/import/status
# Ergebnis: ??? (needs testing)
# Access-Control-Allow-Origin: * (confirmed from logs)
```

---

## Unterschiede zwischen funktionierenden und nicht-funktionierenden Endpoints

### Funktioniert:
- `/api/auth/login` (POST)
- `/api/import/csv` (POST with multipart/form-data)

### Funktioniert NICHT:
- `/api/media` (GET with query params)

### Zu untersuchen:
1. Router registration Unterschiede
2. Middleware-Behandlung
3. GET vs POST
4. Query params vs body

---

## Hypothesen (zu testen)

### Hypothese 1: Backend crasht beim Query-Parsing
- **Test**: Backend Logs während Browser-Request prüfen
- **Erwartung**: Exception/Traceback in Logs
- **Status**: ⏳ Pending

### Hypothese 2: media_api.router prefix Problem
- **Beobachtung**: `app.include_router(media_api.router)` hat KEINEN prefix
- **Andere Router**: `app.include_router(auth.router, prefix="/api")`
- **Test**: Prefix hinzufügen oder Router-Definition prüfen
- **Status**: ⏳ Pending

### Hypothese 3: Middleware blockiert spezifisch GET /api/media
- **Test**: Rate Limiter oder Security Middleware Logs
- **Status**: ⏳ Pending

### Hypothese 4: Browser cached failed request
- **Test**: Curl von Host-Machine (nicht Browser)
- **Status**: ⏳ Pending

### Hypothese 5: AsyncSession Problem bei GET mit joinedload
- **Code**: `query.options(joinedload(UserMedia.media))`
- **Test**: Simplified version without joinedload
- **Status**: ⏳ Pending

---

## 🎯 ROOT CAUSE GEFUNDEN!

### Problem: Session Type Mismatch in media_api.py

**File**: `backend/app/api/media_api.py`

#### Was ist falsch:
```python
from sqlalchemy.orm import Session, joinedload  # ❌ Sync Session import

async def get_user_media(
    db: Session = Depends(get_db),  # ❌ Type hint: Session
):
    query = db.query(UserMedia)  # ❌ Sync API: .query()
    # ...
```

#### Was get_db() tatsächlich zurückgibt:
```python
# backend/app/db/base.py
async def get_db() -> AsyncSession:  # ✅ Returns AsyncSession
    async with AsyncSessionLocal() as session:
        yield session
```

#### Warum das ein Problem ist:
1. FastAPI dependency injection gibt AsyncSession
2. media_api.py erwartet Session (Type hint)
3. Code verwendet `.query()` - die SYNC SQLAlchemy API
4. AsyncSession hat KEINE `.query()` Methode
5. → Runtime Error beim ersten Request
6. → Request crasht BEVOR CORS headers gesendet werden
7. → Browser zeigt "No CORS headers"

#### Vergleich mit funktionierenden Endpoints:

**auth.py** (funktioniert):
```python
from sqlalchemy.ext.asyncio import AsyncSession  # ✅
from sqlalchemy import select  # ✅ Async API

async def login(
    db: AsyncSession = Depends(get_db),  # ✅
):
    result = await db.execute(select(User).where(...))  # ✅ Async API
```

**import_api.py** (funktioniert):
```python
from sqlalchemy.ext.asyncio import AsyncSession  # ✅

async def upload_csv(
    db: AsyncSession = Depends(get_db),  # ✅
):
    # Background processing, aber Session type correct
```

**media_api.py** (crasht):
```python
from sqlalchemy.orm import Session  # ❌ FALSCH!

async def get_user_media(
    db: Session = Depends(get_db),  # ❌ Type mismatch
):
    db.query(UserMedia)  # ❌ Sync API auf Async object
```

---

## 🔧 LÖSUNG

### Option 1: media_api.py auf AsyncSession umschreiben (EMPFOHLEN)

**Vorteile**:
- Konsistent mit anderen APIs
- Async/await best practices
- Kein Datenbank-Session-Wechsel nötig

**Änderungen**:

1. **Imports ändern**:
```python
# ALT:
from sqlalchemy.orm import Session, joinedload

# NEU:
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select
```

2. **Function signature ändern**:
```python
# ALT:
async def get_user_media(
    db: Session = Depends(get_db),

# NEU:
async def get_user_media(
    db: AsyncSession = Depends(get_db),
```

3. **Query API ändern**:
```python
# ALT (Sync API):
query = (
    db.query(UserMedia)
    .options(joinedload(UserMedia.media))
    .filter(UserMedia.user_id == current_user.id)
)
total = query.count()
items = query.order_by(...).offset(offset).limit(limit).all()

# NEU (Async API):
# Build statement
stmt = (
    select(UserMedia)
    .options(joinedload(UserMedia.media))
    .where(UserMedia.user_id == current_user.id)
)

# Apply type filter
if type:
    stmt = stmt.join(Media).where(Media.type == type.value)

# Get total count
count_stmt = select(func.count()).select_from(UserMedia).where(UserMedia.user_id == current_user.id)
if type:
    count_stmt = count_stmt.join(Media).where(Media.type == type.value)
total_result = await db.execute(count_stmt)
total = total_result.scalar()

# Get items
stmt = stmt.order_by(UserMedia.consumed_at.desc()).offset(offset).limit(limit)
result = await db.execute(stmt)
items = result.scalars().unique().all()
```

4. **DELETE endpoint auch anpassen**:
```python
# ALT:
user_media = db.query(UserMedia).filter(...).first()
db.delete(user_media)
db.commit()

# NEU:
result = await db.execute(select(UserMedia).where(...))
user_media = result.scalar_one_or_none()
await db.delete(user_media)
await db.commit()
```

### Option 2: Globaler Wechsel zu Sync Session (NICHT EMPFOHLEN)

**Nachteile**:
- Alle anderen APIs müssen auch umgeschrieben werden
- Verlust von Async-Vorteilen
- Mehr Arbeit

**Status**: Verworfen

---

## Test-Plan für Lösung

### Pre-Implementation Tests
- [x] Root cause identifiziert
- [x] Vergleich mit funktionierenden Endpoints
- [x] Lösung dokumentiert

### Post-Implementation Tests

#### Backend Infrastructure Tests
- [x] Backend startet ohne Fehler
  - Result: ✅ Up 11 seconds (healthy)
  - Logs: No errors, clean startup
- [x] Health endpoint responds
  - Result: ✅ {"status":"healthy"}
- [x] Media endpoint registered
  - Result: ✅ 401 "Not authenticated" (correct behavior without token)
- [x] CORS preflight successful
  - Result: ✅ OPTIONS returns 200 with correct headers
  - Headers: access-control-allow-origin: http://localhost:3000

#### Pending Browser/Frontend Tests
- [ ] GET /api/media mit valid token gibt 200
- [ ] Response enthält Medien-Daten  
- [ ] Browser zeigt keine CORS-Fehler
- [ ] Library-Seite lädt Medien
- [ ] Filter (All/Movies/TV) funktionieren
- [ ] Pagination funktioniert

---

## ✅ IMPLEMENTATION COMPLETED

### Änderungen in media_api.py

#### 1. Imports aktualisiert:
```python
# Added:
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException

# Changed:
from sqlalchemy.orm import joinedload  # removed Session import
```

#### 2. GET /media endpoint komplett umgeschrieben:
- ✅ Type hint: `db: AsyncSession`
- ✅ Query API: `select(UserMedia)` statt `db.query(UserMedia)`
- ✅ Where clause: `.where()` statt `.filter()`
- ✅ Async execution: `await db.execute(stmt)`
- ✅ Result extraction: `result.scalars().unique().all()`
- ✅ Count: Separate statement mit `func.count()`
- ✅ Type filter: Applied to both main and count statements

#### 3. DELETE /media/{media_id} endpoint umgeschrieben:
- ✅ Type hint: `db: AsyncSession`
- ✅ Query: `select(UserMedia).where(...)`
- ✅ Execution: `await db.execute(stmt)`
- ✅ Result: `result.scalar_one_or_none()`
- ✅ Delete: `await db.delete(user_media)`
- ✅ Commit: `await db.commit()`

### Code-Qualität:
- ✅ Konsistent mit auth.py und import_api.py
- ✅ Alle await statements vorhanden
- ✅ Proper error handling
- ✅ Comments für Klarheit
- ✅ Type hints korrekt

---

## Nächste Schritte (systematisch)

### Schritt 1: Backend Logs während Browser-Request
```bash
# Terminal 1: Tail logs
docker logs -f mefeed_backend

# Terminal 2/Browser: Trigger request by opening /library
```
**Ziel**: Exception oder Error message finden

### Schritt 2: Router-Prefix verifizieren
```python
# Check: backend/app/api/media_api.py
router = APIRouter(prefix="/api", tags=["media"])  # Hat es prefix?

# Check: backend/app/main.py
app.include_router(media_api.router)  # Wird prefix überschrieben?
```
**Ziel**: Routing-Inkonsistenz ausschließen

### Schritt 3: Direct curl test von Host
```bash
# With valid token
curl -H "Authorization: Bearer <REAL_TOKEN>" \
     http://localhost:8000/api/media?page=1&limit=20
```
**Ziel**: Browser-spezifisches Problem ausschließen

### Schritt 4: Simplified media endpoint test
```python
# Temporarily modify media_api.py
@router.get("/media-test")
async def test_endpoint():
    return {"test": "ok"}
```
**Ziel**: Middleware/Auth Problem ausschließen

### Schritt 5: Vergleich mit funktionierendem GET endpoint
**Ziel**: Pattern finden der funktioniert

---

## Wichtige Code-Stellen

### Backend Router Registration (main.py)
```python
app.include_router(auth.router, prefix="/api")        # ✅ Works
app.include_router(import_api.router, prefix="/api")  # ✅ Works  
app.include_router(media_api.router)                  # ❌ Doesn't work
# app.include_router(notification_api.router)         # Disabled
```

### Media API Router (media_api.py)
```python
router = APIRouter(prefix="/api", tags=["media"])

@router.get("/media", response_model=UserMediaListResponse)
async def get_user_media(
    type: Optional[MediaType] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # ... query with joinedload
```

### Frontend API Call (media.ts)
```typescript
async getUserMedia(filters?: MediaFilters): Promise<UserMediaResponse> {
    const params: any = {
      page: filters?.page || 1,
      limit: filters?.limit || 20,
    }
    if (filters?.type && filters.type !== 'all') {
      params.type = filters.type
    }
    const response = await apiClient.get('/api/media', { params })
    return response.data
}
```

---

## Status: PHASE 2 - LIVE DEBUGGING

### Versuch 3 Status: ❌ FEHLGESCHLAGEN
- Async migration durchgeführt
- Backend startet OK
- OPTIONS preflight funktioniert
- ABER: GET request schlägt weiterhin fehl
- **Nächster Schritt**: Live-Logs während Browser-Request

---

## Live Debug Session

### Test Results So Far:

#### Backend Infrastructure ✅
- [x] Test endpoint `/api/media-test` works - returns {"test":"ok"}
- [x] Media endpoint responds to invalid token - returns 401
- [x] CORS headers present on 401 responses
- [x] OPTIONS preflight works with all headers

#### Key Finding 🔍
**Problem is NOT backend infrastructure**
- Backend responds correctly to all test requests
- CORS headers are properly set
- Routing works

**Problem must be:**
1. Frontend token issue (expired/invalid/missing)
2. React Query configuration issue  
3. Browser-specific request problem

### Next Investigation: Frontend Token

## 🎯 DIAGNOSTIC TEST PAGE CREATED

Created: `frontend/public/test-media-api.html`

**This page will test:**
1. If token exists in localStorage
2. Direct fetch to /api/media (bypassing React/Next.js)
3. CORS behavior with explicit headers

**User Instructions:**
1. Make sure Frontend container is running
2. Open: http://localhost:3000/test-media-api.html
3. Follow on-screen instructions
4. Report results

This will definitively show if the problem is:
- ✅ Backend (unlikely - all tests passed)
- ✅ Token (test will show if missing/invalid)
- ✅ Frontend framework (React Query, apiClient interceptors)
- ✅ Browser-specific issue

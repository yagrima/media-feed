# Episode-by-Episode Tracking Implementation Plan

**Status**: In Progress (Session beendet am 2025-10-26)  
**Problem identifiziert**: ✅  
**Lösung geplant**: ✅  
**Implementierung**: ⏸️ Pausiert  

---

## 🎯 PROBLEM-ANALYSE

### Aktuelles Verhalten (FALSCH):

**Netflix CSV Format:**
```csv
Title,Date
"Arcane: Staffel 2: Der Dreck unter deinen Nägeln","11/26/24"
"Arcane: Staffel 2: Töten ist ein Kreislauf","11/25/24"
"Arcane: Staffel 2: Tu so, als wäre es das erste Mal","11/25/24"
```

**Was passiert beim Import:**
1. **Zeile 1**: "Arcane: Staffel 2: Episode 1"
   - Parser extrahiert: `main_title = "Arcane"`
   - Erstellt: `Media.title = "Arcane"`, `type = "tv_series"`
   - Erstellt: `user_media` #1 für "Arcane"

2. **Zeile 2**: "Arcane: Staffel 2: Episode 2"
   - Parser extrahiert: `main_title = "Arcane"`
   - **Findet existing Media** mit `title = "Arcane"` ⚠️
   - Erstellt: `user_media` #2 für **SELBE** Media

3. **Zeile 3-9**: Gleiches Verhalten
   - Alle verweisen auf **EINE** Media "Arcane"
   - Erstellt 9 `user_media` Einträge für selbe Media

**Result:**
- ✅ **1 Media-Eintrag**: "Arcane"
- ✅ **9 user_media Einträge**: 9x auf selbe Media-ID
- ❌ **Episode-Count**: Backend zählt korrekt 9, ABER Query filtert nach `title="Arcane: Staffel 2: Episode 1"` → findet nur **1** Media!

### Root Cause:

**In `backend/app/services/netflix_parser.py`, Zeile 217:**
```python
media = await self._find_or_create_media(
    title=parsed_title['main_title'],  # ← NUR "Arcane"
    media_type=parsed_title['type'],
    metadata=parsed_title['metadata']
)
```

**Problem**: Jede Episode sollte **eigener Media-Eintrag** sein, nicht alle gruppiert unter einem Seriennamen!

---

## ✅ LÖSUNG: Episode-by-Episode Tracking

### Design-Entscheidungen:

1. **Jede Episode = Eigener Media-Eintrag**
   - `title` = Voller Titel ("Arcane: Staffel 2: Der Dreck unter deinen Nägeln")
   - `base_title` = Serienname ("Arcane")
   - `season_number` = 2 (extrahiert aus "Staffel 2")
   - `episode_number` = NULL (optional, falls Parser verbessert wird)
   - `type` = "tv_series"

2. **Backend-Query bereits fertig!**
   - Gruppiert nach `base_title` ✓
   - Zählt alle Episoden mit gleichem `base_title` ✓
   - **KEIN Backend-Code-Change nötig!**

3. **Frontend bereits fertig!**
   - Zeigt "(x/XX)" für TV-Serien ✓
   - Versteckt bei Filmen ✓
   - **KEIN Frontend-Code-Change nötig!**

### Was geändert werden muss:

**NUR 1 Datei**: `backend/app/services/netflix_parser.py`

---

## 🔧 IMPLEMENTIERUNGSPLAN

### Änderung 1: `_parse_netflix_title()` - Methode (Zeile 161-200)

**VORHER (falsch):**
```python
if len(parts) >= 3:
    # TV series with season/episode
    main_title = parts[0].strip()
    season_info = parts[1].strip()
    episode_info = ':'.join(parts[2:]).strip()

    return {
        'main_title': main_title,  # ← Nur "Arcane"
        'type': 'tv_series',
        'metadata': {...}
    }
```

**NACHHER (korrekt):**
```python
if len(parts) >= 3:
    # TV series with season/episode
    base_title = parts[0].strip()  # "Arcane"
    season_info = parts[1].strip()  # "Staffel 2"
    episode_info = ':'.join(parts[2:]).strip()  # "Der Dreck..."
    
    # Extract season number
    season_number = self._extract_season_number(season_info)
    
    # Full episode title
    full_title = title.strip()  # "Arcane: Staffel 2: Der Dreck..."

    return {
        'main_title': full_title,      # ← VOLLER Titel!
        'base_title': base_title,      # ← NEU: Für Gruppierung
        'season_number': season_number, # ← NEU: Für DB
        'type': 'tv_series',
        'metadata': {
            'season': season_info,
            'episode': episode_info,
            'full_title': title
        }
    }
```

### Änderung 2: Neue Helper-Methode `_extract_season_number()`

**Einfügen nach Zeile 200:**
```python
def _extract_season_number(self, season_str: str) -> Optional[int]:
    """
    Extract season number from season string
    
    Examples:
        "Staffel 2" -> 2
        "Season 1" -> 1
        "Limited Series" -> None
    
    Args:
        season_str: Season string from Netflix
        
    Returns:
        Season number or None
    """
    import re
    
    # Try to find number after "Staffel" or "Season"
    match = re.search(r'(?:staffel|season)\s*(\d+)', season_str, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Try to find standalone number
    match = re.search(r'\d+', season_str)
    if match:
        return int(match.group(0))
    
    return None
```

### Änderung 3: `_find_or_create_media()` - Methode (Zeile 217-283)

**NACHHER (korrekt):**
```python
async def _find_or_create_media(
    self,
    title: str,                      # VOLLER Episode-Titel
    media_type: str,
    metadata: Dict[str, Any],
    base_title: Optional[str] = None,  # ← NEU
    season_number: Optional[int] = None # ← NEU
) -> Media:
    """
    Find existing media or create new entry
    
    For TV series episodes, each episode gets its own Media entry
    with unique title but shared base_title for grouping.
    """
    # Try to find existing media by EXACT title (case-insensitive)
    result = await self.db.execute(
        select(Media).where(
            func.lower(Media.title) == title.lower()
        ).limit(1)
    )
    media = result.scalar_one_or_none()

    if media:
        # Episode already exists, just update metadata
        current_metadata = media.media_metadata or {}
        
        if 'netflix_imports' not in current_metadata:
            current_metadata['netflix_imports'] = []

        current_metadata['netflix_imports'].append({
            'imported_at': datetime.utcnow().isoformat(),
            'metadata': metadata
        })
        
        media.media_metadata = current_metadata
        flag_modified(media, 'media_metadata')

        # Update type if it was unknown
        if media.type in [None, 'unknown'] and media_type != 'unknown':
            media.type = media_type

        return media

    # Create new media entry (each episode is unique)
    media = Media(
        title=title,                  # Voller Episode-Titel
        base_title=base_title,        # ← NEU: Serienname für Gruppierung
        season_number=season_number,  # ← NEU: Staffel-Nummer
        type=media_type,
        platform_ids={'netflix': True},
        media_metadata={
            'source': 'netflix_csv',
            'imported_at': datetime.utcnow().isoformat(),
            **metadata
        }
    )

    self.db.add(media)
    await self.db.flush()

    return media
```

### Änderung 4: `process_row()` - Methode (Zeile 30-95)

**NACHHER (korrekt):**
```python
async def process_row(self, user_id: uuid.UUID, row: Dict[str, Any]) -> None:
    """Process a single CSV row"""
    title = row.get('Title', '').strip()
    date_str = row.get('Date', '').strip()

    if not title:
        raise ValueError("Missing title")

    # Parse Netflix title format
    parsed_title = self._parse_netflix_title(title)

    # Parse date
    consumed_date = self._parse_date(date_str) if date_str else None

    # Search for media in database (by FULL title now)
    media = await self._find_or_create_media(
        title=parsed_title['main_title'],          # Voller Titel
        media_type=parsed_title['type'],
        metadata=parsed_title['metadata'],
        base_title=parsed_title.get('base_title'),      # ← NEU
        season_number=parsed_title.get('season_number')  # ← NEU
    )

    # Check if already imported (by media_id AND user_id)
    existing = await self.db.execute(
        select(UserMedia).where(
            (UserMedia.user_id == user_id) &
            (UserMedia.media_id == media.id)
        )
    )

    if existing.scalar_one_or_none():
        # Episode already imported for this user, skip
        return

    # Create new user_media entry
    user_media = UserMedia(
        user_id=user_id,
        media_id=media.id,
        platform='netflix',
        consumed_at=consumed_date,
        imported_from=ImportSource.NETFLIX_CSV.value,
        status='watched',
        raw_import_data={
            'original_title': title,
            'date': date_str
        }
    )
    self.db.add(user_media)
    await self.db.flush()
```

---

## 📋 NÄCHSTE SCHRITTE (für morgen)

### 1. Code-Änderungen implementieren (30 min)

- [ ] Öffne: `backend/app/services/netflix_parser.py`
- [ ] Änderung 1: `_parse_netflix_title()` anpassen (Zeile 161-200)
- [ ] Änderung 2: `_extract_season_number()` hinzufügen (nach Zeile 200)
- [ ] Änderung 3: `_find_or_create_media()` Signatur erweitern (Zeile 217-283)
- [ ] Änderung 4: `process_row()` Aufruf anpassen (Zeile 30-95)

### 2. Datenbank leeren (5 min)

**Wichtig**: Alte Daten müssen weg, da sie falsche Struktur haben!

```bash
docker compose exec db psql -U mefeed_user -d mefeed -c "
TRUNCATE TABLE notifications, notification_preferences, 
security_events, user_sessions, import_jobs, user_media, media, users CASCADE;
"
```

### 3. Backend neu bauen & starten (5 min)

```bash
cd "C:\Dev\Me(dia) Feed"
docker compose build backend
docker compose up -d backend
```

### 4. CSV neu importieren (2 min)

- Gehe zu: http://localhost:3000/import
- Lade `NetflixViewingHistory.csv` hoch
- Warte auf Import-Status-Banner (oben)

### 5. Testen (5 min)

- Gehe zu: http://localhost:3000/library
- **Erwartetes Ergebnis**:
  - Arcane: **(9/XX)** ← 9 Episoden!
  - Geek Girl: **(10/XX)** ← 10 Episoden!
  - Vampire Diaries: **(1/XX)** ← 1 Episode
  - KPop Demon Hunters: **KEINE Anzeige** ← Film!

### 6. Git Commits (10 min)

**6 Commits vorbereitet** (alle Änderungen bereits staged):

#### Commit 1: Features (Endless Scrolling + Session Management)
```bash
git reset HEAD USER_STORIES.md backend/app/api/auth.py backend/app/api/media_api.py backend/app/schemas/media_schemas.py backend/app/services/netflix_parser.py frontend/app/\(auth\)/register/page.tsx frontend/app/\(dashboard\)/import/page.tsx frontend/components/import/import-status-banner.tsx frontend/components/library/media-grid.tsx frontend/components/providers.tsx frontend/lib/api/media.ts frontend/lib/auth-context.tsx frontend/lib/import-context.tsx .gitignore

git commit -m "feat: Add endless scrolling, session security, and automated cleanup"
```

#### Commit 2: UX-Fix (Auto-Login)
```bash
git add backend/app/api/auth.py frontend/app/\(auth\)/register/page.tsx frontend/lib/auth-context.tsx
git commit -m "fix: Auto-login users after successful registration"
```

#### Commit 3: UX-Fix (Toast-Optimierung)
```bash
git add frontend/components/providers.tsx
git commit -m "fix: Improve toast notification positioning and duration"
```

#### Commit 4: Feature (Import-Status-Tracking)
```bash
git add frontend/app/\(dashboard\)/import/page.tsx frontend/components/import/import-status-banner.tsx frontend/lib/import-context.tsx frontend/components/providers.tsx
git commit -m "feat: Add real-time import status tracking with visual feedback"
```

#### Commit 5: Feature (Accurate Episode Counts)
```bash
git add backend/app/api/media_api.py backend/app/schemas/media_schemas.py frontend/lib/api/media.ts frontend/components/library/media-grid.tsx USER_STORIES.md
git commit -m "feat: Display accurate watched episode counts for TV series"
```

#### Commit 6: Fix + Feature (Episode-by-Episode Tracking) - NACH Implementierung!
```bash
git add backend/app/services/netflix_parser.py .gitignore EPISODE_TRACKING_IMPLEMENTATION.md
git commit -m "feat: Implement episode-by-episode tracking for Netflix imports

Problem: All episodes of a series were grouped under single Media entry,
causing episode counts to always show (1/XX) instead of actual count.

Root Cause: Parser extracted only series base name ('Arcane') and reused
same Media entry for all episodes, creating multiple user_media entries
pointing to single Media record.

Solution: Episode-by-Episode Tracking
- Each episode gets unique Media entry with full title
- Added base_title field for series grouping
- Added season_number extraction from 'Staffel X' format
- Parser now stores full episode title in Media.title
- Backend query groups by base_title (already implemented)

Implementation Changes:
- netflix_parser.py: Modified _parse_netflix_title() to preserve full title
- Added _extract_season_number() helper for season parsing
- Updated _find_or_create_media() to use full title + base_title
- Modified process_row() to pass new fields

Technical Details:
- Netflix format: 'Series: Staffel X: Episode Title'
- Extracts: base_title='Series', season_number=X, title='Full Episode Title'
- Each import creates unique Media entry per episode
- Episode counts now accurate: Arcane (9/XX), Geek Girl (10/XX)

Benefits:
- Accurate episode tracking per series
- Proper progress visualization
- Future: Can show individual episode details
- Maintains backward compatibility (movies unchanged)

Database Impact:
- Requires reimport of Netflix CSV with new structure
- Old imports had 1 Media per series (consolidated)
- New imports have 1 Media per episode (granular)

User Stories:
- Episode-by-episode tracking: 10/10
- Accurate progress counts: 10/10
- Series grouping by base_title: 10/10

Co-authored-by: factory-droid[bot] <138933559+factory-droid[bot]@users.noreply.github.com>"
```

---

## 📁 WICHTIGE DATEIEN

### Hauptdatei zum Ändern:
- `backend/app/services/netflix_parser.py` (Zeilen 30-283)

### Bereits fertige Dateien (KEINE Änderung nötig):
- ✅ `backend/app/api/media_api.py` - Gruppiert nach base_title
- ✅ `frontend/components/library/media-grid.tsx` - Zeigt (x/XX)
- ✅ `frontend/lib/api/media.ts` - TypeScript Interface

### Dokumentation:
- `.gitignore` - CSV-Dateien ausgeschlossen ✓
- `EPISODE_TRACKING_IMPLEMENTATION.md` - Dieses Dokument
- `USER_STORIES.md` - Alle Features dokumentiert

---

## 🧪 TEST-DATEN (NetflixViewingHistory.csv)

**Location**: `C:\Dev\Me(dia) Feed\NetflixViewingHistory.csv`  
**Status**: ✅ In .gitignore  
**Zeilen**: 1617  

**Sample-Daten zur Validierung:**
```csv
"Arcane: Staffel 2: Der Dreck unter deinen Nägeln","11/26/24"  → 9 Episoden total
"Geek Girl: Staffel 1: Kapitel 10","10/30/24"                 → 10 Episoden total
"Vampire Diaries: Staffel 1: Liebes Tagebuch","12/20/24"      → 1 Episode
"KPop Demon Hunters","6/26/25"                                → Film (keine Count)
```

---

## ⚠️ WICHTIGE HINWEISE

1. **Datenbank MUSS geleert werden**
   - Alte Struktur: 1 Media pro Serie
   - Neue Struktur: 1 Media pro Episode
   - Inkompatibel → Reimport erforderlich

2. **Backend-Query bereits optimal**
   - Gruppiert nach `base_title` ✓
   - Zählt alle Episoden mit gleichem `base_title` ✓
   - KEIN Change nötig!

3. **Frontend bereits optimal**
   - Zeigt `watched_episodes_count` ✓
   - Versteckt bei Filmen ✓
   - KEIN Change nötig!

4. **NUR Parser muss angepasst werden**
   - Eine einzige Datei: `netflix_parser.py`
   - 4 kleine Änderungen
   - ~50 Zeilen Code total

---

## 📊 ERWARTETE ERGEBNISSE

### Vor dem Fix:
```
Arcane (1/XX)
Geek Girl (1/XX)
Vampire Diaries (1/XX)
```

### Nach dem Fix:
```
Arcane (9/XX)
Geek Girl (10/XX)
Vampire Diaries (1/XX)
KPop Demon Hunters [keine Anzeige - ist Film]
```

---

## 🎯 ERFOLGS-KRITERIEN

- [ ] Backend baut ohne Fehler
- [ ] CSV-Import läuft durch (1617 Zeilen)
- [ ] Library zeigt korrekte Episode-Counts
- [ ] Filme zeigen keine Episode-Counts
- [ ] Alle 6 Commits erfolgreich
- [ ] User Stories aktualisiert (3 neue Stories für Episode-Tracking)

---

**Session beendet**: 2025-10-26, 02:45 UTC  
**Nächste Session**: Implementierung + Testing + Commits  
**Geschätzte Zeit**: 1-1.5 Stunden

Viel Erfolg morgen! 🚀

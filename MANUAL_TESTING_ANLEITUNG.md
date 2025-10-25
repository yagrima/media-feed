# Manuelle Test-Anleitung - Me Feed

**Erstellt am**: 20. Oktober 2025
**Letzte Aktualisierung**: 20. Oktober 2025
**Status**: ✅ Bereit zum Testen
**Geschätzte Dauer**: 2-3 Stunden

---

## 📋 Inhaltsverzeichnis

1. [Vorbereitung](#vorbereitung)
2. [Umgebung einrichten](#umgebung-einrichten)
3. [Test-Durchführung](#test-durchführung)
4. [Probleme dokumentieren](#probleme-dokumentieren)
5. [Häufige Probleme](#häufige-probleme)

---

## 🎯 Vorbereitung

### Was Sie brauchen

- [ ] Windows PC mit Administratorrechten
- [ ] PostgreSQL installiert (oder bereit zur Installation)
- [ ] Redis installiert (oder bereit zur Installation)
- [ ] Node.js 18+ installiert
- [ ] Python 3.9+ installiert
- [ ] Mindestens 2 GB freier Festplattenspeicher
- [ ] Internetverbindung
- [ ] Einen Texteditor (z.B. Notepad++, VS Code)
- [ ] Ca. 2-3 Stunden Zeit

### Wichtiger Hinweis

⚠️ **Das Projekt liegt auf Google Drive und hat Berechtigungsprobleme!**

Sie müssen das Projekt zuerst auf eine lokale Festplatte kopieren:

```
Von: G:\My Drive\KI-Dev\Me(dia) Feed
Nach: C:\Dev\MeFeed
```

---

## 🚀 Umgebung einrichten

### Schritt 1: Projekt auf lokale Festplatte kopieren

**Option A: Mit Windows Explorer**
1. Öffnen Sie Windows Explorer
2. Navigieren Sie zu `G:\My Drive\KI-Dev\Me(dia) Feed`
3. Kopieren Sie den gesamten Ordner
4. Fügen Sie ihn ein unter `C:\Dev\MeFeed`
5. Warten Sie, bis alle Dateien kopiert sind

**Option B: Mit Kommandozeile**
```bash
# Öffnen Sie PowerShell als Administrator
xcopy "G:\My Drive\KI-Dev\Me(dia) Feed" "C:\Dev\MeFeed" /E /I /H
```

✅ **Prüfung**: Öffnen Sie `C:\Dev\MeFeed` - Sie sollten die Ordner `backend`, `frontend`, `docs`, etc. sehen

---

### Schritt 2: PostgreSQL installieren und starten

**Wenn PostgreSQL noch nicht installiert ist:**

1. Download von https://www.postgresql.org/download/windows/
2. Installieren Sie PostgreSQL 15 oder höher
3. Merken Sie sich das Master-Passwort!
4. Standard-Port: 5432 (nicht ändern)

**PostgreSQL starten:**

1. Öffnen Sie "Services" (Windows-Taste + R, dann `services.msc`)
2. Suchen Sie "PostgreSQL"
3. Rechtsklick → "Start" (falls nicht läuft)
4. Status sollte "Running" sein

**Datenbank erstellen:**

```bash
# Öffnen Sie PowerShell
cd C:\Dev\MeFeed\backend

# PostgreSQL SQL Shell öffnen (suchen Sie "psql" im Startmenü)
# Oder nutzen Sie pgAdmin
```

Führen Sie diese SQL-Befehle aus:
```sql
CREATE DATABASE mefeed;
CREATE USER mefeed_user WITH PASSWORD 'ihr_sicheres_passwort';
GRANT ALL PRIVILEGES ON DATABASE mefeed TO mefeed_user;
```

✅ **Prüfung**: Verbindung testen mit `psql -U mefeed_user -d mefeed`

---

### Schritt 3: Redis installieren und starten

**Redis installieren (Windows):**

**Option A: Mit WSL (empfohlen)**
```bash
# Windows Subsystem for Linux installieren (falls nicht vorhanden)
wsl --install

# In WSL:
sudo apt update
sudo apt install redis-server
redis-server
```

**Option B: Mit Memurai (Windows-native Redis Alternative)**
1. Download von https://www.memurai.com/
2. Installieren und starten
3. Standard-Port: 6379

**Option C: Mit Docker**
```bash
docker run -d -p 6379:6379 redis:latest
```

✅ **Prüfung**:
```bash
# Öffnen Sie eine neue PowerShell
redis-cli ping
# Sollte "PONG" zurückgeben
```

---

### Schritt 4: Backend einrichten

```bash
# Öffnen Sie PowerShell
cd C:\Dev\MeFeed\backend

# Python Virtual Environment erstellen
python -m venv venv

# Virtual Environment aktivieren
.\venv\Scripts\activate

# Dependencies installieren (dauert ca. 2-3 Minuten)
pip install -r requirements.txt
```

**Umgebungsvariablen konfigurieren:**

1. Öffnen Sie `C:\Dev\MeFeed\backend\.env` im Texteditor
2. Passen Sie folgende Werte an:

```env
# Database
DATABASE_URL=postgresql://mefeed_user:ihr_passwort@localhost:5432/mefeed
REDIS_URL=redis://localhost:6379

# Security (die Dateien existieren bereits in secrets/)
JWT_PRIVATE_KEY_PATH=./secrets/jwt_private.pem
JWT_PUBLIC_KEY_PATH=./secrets/jwt_public.pem
ENCRYPTION_KEY_PATH=./secrets/encryption.key

# Aus secrets/secret_key.txt kopieren
SECRET_KEY=<kopieren Sie den Wert aus secrets/secret_key.txt>

# CORS
ALLOWED_ORIGINS=http://localhost:3000
ALLOWED_HOSTS=localhost,127.0.0.1

# Optional: TMDB API (für Sequel-Detection)
# Falls Sie keinen Key haben, lassen Sie es leer
TMDB_API_KEY=

# Features
ENABLE_EMAIL_VERIFICATION=false
ENFORCE_HTTPS=false
DEBUG=true
```

**Datenbank-Migrationen ausführen:**

```bash
# Im selben PowerShell-Fenster (venv sollte aktiviert sein)
cd C:\Dev\MeFeed\backend
alembic upgrade head
```

✅ **Prüfung**: Sollte ohne Fehler durchlaufen und "Running upgrade" anzeigen

---

### Schritt 5: Frontend einrichten

**Neue PowerShell öffnen (lassen Sie die erste offen!):**

```bash
cd C:\Dev\MeFeed\frontend

# Dependencies installieren (dauert ca. 3-5 Minuten)
npm install
```

**Umgebungsvariablen konfigurieren:**

1. Erstellen Sie eine neue Datei: `C:\Dev\MeFeed\frontend\.env.local`
2. Fügen Sie folgende Zeile ein:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

✅ **Prüfung**:
```bash
# Prüfen Sie, ob node_modules erstellt wurde
dir node_modules
# Sollte viele Ordner anzeigen
```

---

### Schritt 6: Server starten

**🚀 NEU: Vereinfachter Start mit einem einzigen Skript!**

Öffnen Sie PowerShell im Hauptverzeichnis und führen Sie aus:

```powershell
cd C:\Dev\MeFeed
.\start-all.ps1
```

Das Skript wird:
1. Alle Voraussetzungen prüfen (PostgreSQL, Redis, Dependencies)
2. Backend-Server in einem neuen Fenster starten
3. Frontend-Server in einem neuen Fenster starten
4. Ihnen die URLs anzeigen

✅ **Erwartet**:
- Zwei neue PowerShell-Fenster öffnen sich
- Backend läuft auf http://localhost:8000
- Frontend läuft auf http://localhost:3000

**Alternative: Manueller Start**

Falls Sie die Server einzeln starten möchten:

**Terminal 1 - Backend starten:**
```bash
cd C:\Dev\MeFeed\backend
.\start-backend.ps1
```

**Terminal 2 - Frontend starten:**
```bash
cd C:\Dev\MeFeed\frontend
.\start-frontend.ps1
```

**Legacy-Methode (falls Skripte nicht funktionieren):**

```bash
# Terminal 1 - Backend
cd C:\Dev\MeFeed\backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd C:\Dev\MeFeed\frontend
npm run dev
```

✅ **Prüfung**:
- Öffnen Sie Browser → http://localhost:8000/docs (API-Dokumentation)
- Öffnen Sie Browser → http://localhost:3000 (Login-Seite)

---

## 🧪 Test-Durchführung

### Phase 1: Grundfunktionen (30 Minuten)

#### Test 1.1: Benutzer-Registrierung

1. Öffnen Sie http://localhost:3000
2. Klicken Sie auf "Register" (oder navigieren Sie zu `/register`)
3. **Testen Sie FEHLERHAFTE Eingaben:**
   - [ ] Leere Email → Fehlermeldung sollte erscheinen
   - [ ] Ungültige Email (ohne @) → Fehlermeldung
   - [ ] Passwort zu kurz (< 12 Zeichen) → Fehlermeldung
   - [ ] Passwort ohne Großbuchstaben → Fehlermeldung
   - [ ] Passwort ohne Zahl → Fehlermeldung
   - [ ] Passwörter stimmen nicht überein → Fehlermeldung

4. **Registrieren Sie einen GÜLTIGEN Benutzer:**
   ```
   Email: test@example.com
   Passwort: TestPasswort123!
   Passwort bestätigen: TestPasswort123!
   ```

   ✅ **Erwartet**:
   - Erfolgs-Toast erscheint
   - Weiterleitung zum Dashboard oder Login

5. **Versuchen Sie DOPPELTE Registrierung:**
   - Registrieren Sie sich erneut mit derselben Email

   ✅ **Erwartet**: Fehlermeldung "Email bereits registriert"

📝 **Notizen:**
```
✅ Funktioniert  ⚠️ Problem  ❌ Fehler

[  ] Registrierung erfolgreich
[  ] Fehlervalidierung funktioniert
[  ] Duplikat-Check funktioniert
Problem (falls vorhanden): _________________________________
```

---

#### Test 1.2: Benutzer-Login

1. Navigieren Sie zu http://localhost:3000/login
2. **Testen Sie FEHLERHAFTE Anmeldung:**
   - [ ] Falsche Email → Fehlermeldung
   - [ ] Falsches Passwort → Fehlermeldung
   - [ ] Leere Felder → Validierungsfehler

3. **ERFOLGREICHE Anmeldung:**
   ```
   Email: test@example.com
   Passwort: TestPasswort123!
   ```

   ✅ **Erwartet**:
   - Erfolgs-Toast erscheint
   - Weiterleitung zu `/dashboard`
   - Navbar erscheint oben mit Navigation

4. **Prüfen Sie die Session:**
   - Drücken Sie F12 (Developer Tools)
   - Gehen Sie zu "Application" → "Local Storage" → http://localhost:3000
   - Sie sollten sehen:
     - `access_token`
     - `refresh_token`
     - `token_expiry`

📝 **Notizen:**
```
[  ] Login erfolgreich
[  ] Tokens werden gespeichert
[  ] Weiterleitung funktioniert
Problem: _________________________________
```

---

#### Test 1.3: Navigation

1. **Prüfen Sie alle Navbar-Links:**
   - [ ] "Library" → /dashboard
   - [ ] "Import" → /dashboard/import
   - [ ] "Notifications" → /dashboard/notifications
   - [ ] "Settings" → /dashboard/settings

2. **Prüfen Sie aktive Markierung:**
   - Der aktuelle Link sollte farblich hervorgehoben sein

3. **Logout testen:**
   - Klicken Sie auf "Logout"

   ✅ **Erwartet**:
   - Erfolgs-Toast "Logged out successfully"
   - Weiterleitung zu `/login`
   - Tokens gelöscht (prüfen Sie Local Storage)

📝 **Notizen:**
```
[  ] Alle Links funktionieren
[  ] Logout funktioniert
Problem: _________________________________
```

---

### Phase 2: CSV Import (45 Minuten)

#### Test 2.1: CSV Upload Vorbereitung

**Erstellen Sie eine Test-CSV-Datei:**

1. Öffnen Sie Notepad
2. Kopieren Sie folgenden Inhalt:

```csv
Title,Date
Breaking Bad: Season 1,2024-01-15
The Matrix,2024-02-20
Stranger Things: Season 3,2024-03-10
Inception,2024-04-05
Game of Thrones: Season 1,2024-05-12
```

3. Speichern Sie als `test_import.csv` auf dem Desktop

✅ **Prüfung**: Öffnen Sie die Datei erneut - sollte als CSV angezeigt werden

---

#### Test 2.2: CSV Upload durchführen

1. Navigieren Sie zu http://localhost:3000/dashboard/import
2. **Testen Sie UNGÜLTIGE Dateien:**
   - [ ] Ziehen Sie eine .txt Datei → Sollte abgelehnt werden
   - [ ] Ziehen Sie eine sehr große Datei (> 10MB) → Sollte abgelehnt werden

3. **Upload der TEST-CSV:**
   - Ziehen Sie `test_import.csv` in den Upload-Bereich
   - ODER klicken Sie und wählen Sie die Datei aus

   ✅ **Erwartet**:
   - Grüner Rand erscheint beim Drag-Over
   - Upload startet automatisch
   - Erfolgs-Toast erscheint
   - Sie sehen eine Job-ID

4. **Beobachten Sie den Fortschritt:**
   - Status sollte wechseln: "processing" → "completed"
   - Fortschrittsbalken sollte sich füllen
   - Zähler zeigen: "5 rows processed" (oder ähnlich)
   - Status aktualisiert sich alle 2 Sekunden automatisch

📝 **Notizen:**
```
[  ] Upload erfolgreich
[  ] Status-Tracking funktioniert
[  ] Zeilen wurden importiert
Importierte Zeilen: ____
Fehlerhafte Zeilen: ____
Problem: _________________________________
```

---

#### Test 2.3: Import History prüfen

1. Scrollen Sie auf der Import-Seite nach unten
2. Sie sollten "Import History" sehen

✅ **Erwartet**:
- Ihr gerade durchgeführter Import ist aufgelistet
- Zeigt: Dateiname, Datum, Status, Zeilen-Anzahl
- Status-Badge ist grün (für "completed")

📝 **Notizen:**
```
[  ] History wird angezeigt
[  ] Daten sind korrekt
Problem: _________________________________
```

---

### Phase 3: Media Library (30 Minuten)

#### Test 3.1: Medien-Anzeige

1. Navigieren Sie zu http://localhost:3000/dashboard (oder /dashboard/library)
2. **Prüfen Sie die Anzeige:**

   ✅ **Erwartet**:
   - Grid mit Media-Karten
   - Jede Karte zeigt:
     - Titel
     - Typ-Icon (Film oder TV)
     - Badge (Movie / TV Series)
     - Platform
     - Datum
   - Responsive Grid (4 Spalten auf Desktop, 2 auf Tablet, 1 auf Handy)

📝 **Notizen:**
```
Angezeigte Medien: ____
[  ] Alle 5 Medien werden angezeigt
[  ] Icons korrekt
[  ] Daten vollständig
Problem: _________________________________
```

---

#### Test 3.2: Filter testen

1. **Filter-Buttons:**
   - [ ] Klicken Sie auf "All" → Alle Medien
   - [ ] Klicken Sie auf "Movies" → Nur Filme
   - [ ] Klicken Sie auf "TV Series" → Nur Serien

2. **Zählen Sie:**
   - Anzahl Filme: ____
   - Anzahl Serien: ____
   - Gesamt: ____

✅ **Erwartet**: Filter funktionieren sofort, keine Seiten-Neuladen

📝 **Notizen:**
```
[  ] Filter funktionieren
[  ] Anzahlen stimmen
Problem: _________________________________
```

---

#### Test 3.3: Pagination testen

**Nur relevant, wenn Sie > 20 Medien haben**

Falls Sie nur 5 Medien haben (von unserem Test-CSV):

1. Erstellen Sie eine größere CSV-Datei mit 25+ Zeilen
2. Importieren Sie diese
3. Gehen Sie zurück zur Library

✅ **Pagination sollte erscheinen:**
- Erste/Zurück/Weiter/Letzte Buttons
- Seitenzahlen
- "Showing X to Y of Z results"

📝 **Notizen:**
```
[  ] Pagination erscheint (falls > 20 Medien)
[  ] Blättern funktioniert
[  ] Smooth scroll nach oben
Problem: _________________________________
```

---

### Phase 4: Benachrichtigungen (30 Minuten)

#### Test 4.1: Benachrichtigungs-Anzeige

1. Navigieren Sie zu http://localhost:3000/dashboard/notifications
2. **Prüfen Sie die Anzeige:**

✅ **Erwartet**:
- Falls Benachrichtigungen vorhanden:
  - Liste mit Benachrichtigungs-Karten
  - Icons je nach Typ (Upload/Film/Alert)
  - "New" Badge bei ungelesenen
  - Zeitstempel
- Falls keine Benachrichtigungen:
  - "No notifications" Nachricht
  - Icon und freundlicher Text

**Benachrichtigung erstellen (falls keine vorhanden):**
- Laden Sie eine weitere CSV hoch
- Nach Abschluss sollte eine "Import Complete" Benachrichtigung erscheinen

📝 **Notizen:**
```
Anzahl Benachrichtigungen: ____
[  ] Anzeige funktioniert
[  ] Icons korrekt
Problem: _________________________________
```

---

#### Test 4.2: Benachrichtigungen verwalten

1. **Als gelesen markieren:**
   - Klicken Sie auf "Mark read" bei einer Benachrichtigung

   ✅ **Erwartet**:
   - "New" Badge verschwindet
   - Hintergrund wechselt zu gedämpfter Farbe
   - Unread-Count in Navbar verringert sich

2. **Alle als gelesen markieren:**
   - Klicken Sie auf "Mark all read" (oben rechts)

   ✅ **Erwartet**:
   - Alle Benachrichtigungen werden gedämpft
   - Success-Toast erscheint
   - Badge in Navbar verschwindet

3. **Benachrichtigung löschen:**
   - Klicken Sie auf Papierkorb-Icon

   ✅ **Erwartet**:
   - Benachrichtigung verschwindet
   - Success-Toast erscheint

📝 **Notizen:**
```
[  ] Markieren funktioniert
[  ] Löschen funktioniert
[  ] Badge aktualisiert sich
Problem: _________________________________
```

---

#### Test 4.3: Auto-Refresh testen

1. Lassen Sie die Benachrichtigungs-Seite offen
2. **Warten Sie 30 Sekunden**
3. In der Zwischenzeit: Laden Sie in einem anderen Tab/Fenster eine CSV hoch

✅ **Erwartet**:
- Nach max. 30 Sekunden erscheint die neue Benachrichtigung automatisch
- Kein manuelles Neuladen nötig

**Oder testen Sie manuell:**
- Klicken Sie auf den Refresh-Button (oben rechts)
- Toast "Notifications refreshed" sollte erscheinen

📝 **Notizen:**
```
[  ] Auto-Refresh funktioniert
[  ] Manueller Refresh funktioniert
Problem: _________________________________
```

---

### Phase 5: Einstellungen (15 Minuten)

#### Test 5.1: Profil-Anzeige

1. Navigieren Sie zu http://localhost:3000/dashboard/settings
2. **Prüfen Sie die Anzeige:**

✅ **Erwartet**:
- Ihre Email wird angezeigt
- "Member since" Datum wird angezeigt
- "Active" Badge sichtbar

📝 **Notizen:**
```
Email korrekt: [  ]
Datum korrekt: [  ]
Problem: _________________________________
```

---

#### Test 5.2: Benachrichtigungs-Einstellungen

1. Klicken Sie auf "Manage Notification Settings"
2. Sollte zu `/dashboard/notifications/preferences` weiterleiten

3. **Testen Sie die Switches:**
   - [ ] "Email Notifications" umschalten
   - [ ] "Sequel Detected" umschalten
   - [ ] "Import Status" umschalten
   - [ ] "System Updates" umschalten

✅ **Erwartet**:
- Switches animieren sich smooth
- "Save Preferences" Button aktiviert sich

4. **Speichern Sie die Änderungen:**
   - Klicken Sie "Save Preferences"

   ✅ **Erwartet**:
   - Success-Toast: "Preferences updated successfully"
   - Button deaktiviert sich wieder (keine Änderungen)

5. **Seite neu laden (F5):**
   - Ihre Einstellungen sollten gespeichert sein

📝 **Notizen:**
```
[  ] Switches funktionieren
[  ] Speichern funktioniert
[  ] Einstellungen bleiben gespeichert
Problem: _________________________________
```

---

### Phase 6: Fehlerbehandlung (30 Minuten)

#### Test 6.1: Netzwerk-Fehler

1. **Stoppen Sie den Backend-Server:**
   - Gehen Sie zum Terminal-Fenster mit dem Backend
   - Drücken Sie `STRG+C`

2. **Versuchen Sie, sich anzumelden:**
   - Gehen Sie zu http://localhost:3000/login
   - Versuchen Sie, sich anzumelden

   ✅ **Erwartet**:
   - Toast-Nachricht: "Network error - Unable to reach the server"
   - Klare Fehlermeldung

3. **Starten Sie den Backend-Server neu:**
   ```bash
   # Option 1: Mit Startskript
   cd C:\Dev\MeFeed\backend
   .\start-backend.ps1

   # Option 2: Manuell
   .\venv\Scripts\activate
   uvicorn app.main:app --reload --port 8000
   ```

4. **Versuchen Sie erneut:**
   - Login sollte jetzt funktionieren

📝 **Notizen:**
```
[  ] Fehler wird angezeigt
[  ] Fehlermeldung ist klar
[  ] Nach Neustart funktioniert es
Problem: _________________________________
```

---

#### Test 6.2: Validierungs-Fehler

1. **Login mit ungültigen Daten:**
   ```
   Email: fake@example.com
   Passwort: WrongPassword123!
   ```

   ✅ **Erwartet**:
   - Fehlermeldung erscheint
   - Kein Crash
   - User bleibt auf Login-Seite

2. **CSV mit falscher Struktur uploaden:**
   - Erstellen Sie eine .csv Datei ohne korrekte Spalten

   ✅ **Erwartet**:
   - Import schlägt fehl
   - Klare Fehlermeldung in Error Log

📝 **Notizen:**
```
[  ] Fehler werden abgefangen
[  ] Keine Crashes
Problem: _________________________________
```

---

#### Test 6.3: 404-Seite

1. Navigieren Sie zu einer nicht existierenden Seite:
   ```
   http://localhost:3000/does-not-exist
   ```

✅ **Erwartet**:
- 404-Seite wird angezeigt
- "Page Not Found" Nachricht
- Buttons "Go to Dashboard" und "Go to Login"
- Kein Crash

📝 **Notizen:**
```
[  ] 404-Seite erscheint
[  ] Buttons funktionieren
Problem: _________________________________
```

---

### Phase 7: Responsive Design (15 Minuten)

#### Test 7.1: Mobile Ansicht

1. Drücken Sie `F12` (Developer Tools)
2. Klicken Sie auf das Handy-Icon (Toggle Device Toolbar)
3. Wählen Sie "iPhone 12 Pro" oder ähnlich

**Testen Sie alle Seiten:**
- [ ] Login-Seite lesbar
- [ ] Dashboard / Library: Cards in 1 Spalte
- [ ] Import-Seite: Upload-Bereich gut erreichbar
- [ ] Notifications: Gut lesbar
- [ ] Settings: Formulare nutzbar

✅ **Erwartet**:
- Alles lesbar ohne horizontales Scrollen
- Buttons erreichbar
- Formulare nutzbar

📝 **Notizen:**
```
[  ] Mobile Ansicht funktioniert
Problem: _________________________________
```

---

#### Test 7.2: Tablet Ansicht

1. Wählen Sie "iPad" oder ähnlich in DevTools
2. Prüfen Sie Library:
   - Sollte 2 Spalten haben

✅ **Erwartet**: Layout passt sich an

📝 **Notizen:**
```
[  ] Tablet Ansicht funktioniert
Problem: _________________________________
```

---

## 📝 Probleme dokumentieren

### Problem-Bericht Vorlage

Wenn Sie einen Fehler finden, dokumentieren Sie ihn so:

```
===============================================
PROBLEM #1

Titel: [Kurze Beschreibung]
Schweregrad: [Kritisch / Hoch / Mittel / Niedrig]

Schritte zum Reproduzieren:
1.
2.
3.

Erwartet:
[Was sollte passieren]

Tatsächlich:
[Was passiert wirklich]

Screenshots/Fehler:
[Screenshot einfügen oder Fehlermeldung kopieren]

Browser: [Chrome / Firefox / Edge]
Datum: [TT.MM.JJJJ]
Uhrzeit: [HH:MM]
===============================================
```

**Speichern Sie alle Probleme in einer Datei:**
`C:\Dev\MeFeed\TEST_PROBLEME.txt`

---

## 🔧 Häufige Probleme

### Problem: "Execution Policy" Fehler beim Start-Skript

**Fehlermeldung:**
```
.\start-all.ps1 : File cannot be loaded because running scripts is disabled on this system.
```

**Lösung:**
```powershell
# PowerShell als Administrator öffnen
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Danach sollte das Skript funktionieren
.\start-all.ps1
```

---

### Problem: "Port 8000 already in use"

**Lösung:**
```bash
# Windows: Prozess auf Port 8000 finden
netstat -ano | findstr :8000

# Prozess beenden (ersetzen Sie PID mit der Nummer)
taskkill /PID <PID> /F

# Oder starten Sie das Skript einfach neu - es prüft automatisch
.\start-all.ps1
```

---

### Problem: "Database connection failed"

**Lösung:**
1. Prüfen Sie, ob PostgreSQL läuft (services.msc)
2. Prüfen Sie Credentials in `.env`
3. Testen Sie Verbindung:
   ```bash
   psql -U mefeed_user -d mefeed
   ```

---

### Problem: "Redis connection failed"

**Lösung:**
1. Prüfen Sie, ob Redis läuft:
   ```bash
   redis-cli ping
   ```
2. Starten Sie Redis neu
3. Prüfen Sie Port in `.env` (sollte 6379 sein)

---

### Problem: Frontend zeigt weißen Bildschirm

**Lösung:**
1. Öffnen Sie Browser DevTools (F12)
2. Gehen Sie zum "Console" Tab
3. Suchen Sie nach roten Fehlermeldungen
4. Notieren Sie den Fehler
5. Starten Sie Frontend neu:
   ```bash
   # STRG+C im Frontend-Terminal
   npm run dev
   ```

---

### Problem: "Module not found" Fehler

**Lösung:**
```bash
cd C:\Dev\MeFeed\frontend
rm -rf node_modules
rm package-lock.json
npm install
```

---

### Problem: CSV Import zeigt "Failed"

**Mögliche Ursachen:**
1. CSV-Format falsch → Prüfen Sie Spalten (Title, Date)
2. Datei zu groß → Max. 10MB, 10.000 Zeilen
3. Ungültige Zeichen → Nutzen Sie UTF-8 Encoding

**CSV-Format prüfen:**
```csv
Title,Date
Film oder Serie: Season X,YYYY-MM-DD
```

---

## ✅ Test-Abschluss Checkliste

Wenn Sie ALLE Tests durchgeführt haben:

### Kritische Funktionen
- [ ] Registrierung funktioniert
- [ ] Login funktioniert
- [ ] CSV Import funktioniert
- [ ] Medien werden angezeigt
- [ ] Benachrichtigungen funktionieren
- [ ] Einstellungen können gespeichert werden

### Fehlerbehandlung
- [ ] Netzwerk-Fehler werden abgefangen
- [ ] Validierungs-Fehler werden angezeigt
- [ ] 404-Seite funktioniert
- [ ] Keine App-Crashes

### UI/UX
- [ ] Alle Links funktionieren
- [ ] Navbar korrekt
- [ ] Responsive auf Mobile
- [ ] Responsive auf Tablet
- [ ] Loading-States sichtbar
- [ ] Toast-Benachrichtigungen erscheinen

### Performance
- [ ] Seiten laden schnell (< 3 Sekunden)
- [ ] Keine Verzögerungen beim Navigieren
- [ ] Auto-Refresh funktioniert ohne Ruckeln

---

## 📊 Test-Zusammenfassung

**Test-Statistik:**
```
Durchgeführte Tests: ____ / 43
Erfolgreich: ____
Fehlgeschlagen: ____
Nicht getestet: ____

Pass-Rate: _____%

Kritische Fehler: ____
Hohe Priorität: ____
Mittlere Priorität: ____
Niedrige Priorität: ____
```

**Gesamtbewertung:**
```
[ ] Bereit für Produktion
[ ] Kleinere Fixes nötig
[ ] Größere Probleme gefunden
[ ] Nicht bereit
```

**Nächste Schritte:**
```
1. ________________________________
2. ________________________________
3. ________________________________
```

---

## 🎉 Fertig!

Herzlichen Glückwunsch! Sie haben das manuelle Testing abgeschlossen.

**Was nun?**

1. **Senden Sie Ihren Test-Bericht:**
   - Datei: `C:\Dev\MeFeed\TEST_PROBLEME.txt`
   - An: Entwicklungsteam

2. **Falls alles funktioniert:**
   - Projekt ist bereit für Staging-Deployment

3. **Falls Probleme gefunden:**
   - Entwickler werden die Fehler beheben
   - Danach erneutes Testing nötig

---

**Vielen Dank für Ihre Zeit beim Testen!**

**Fragen?** Kontaktieren Sie das Entwicklungsteam.

**Dokument-Version:** 1.0
**Erstellt von:** Claude Code (Developer Persona)
**Datum:** 20. Oktober 2025

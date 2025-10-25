# Startup Scripts - Me Feed

## 📋 Übersicht

Das Me Feed Projekt enthält automatisierte Startup-Skripte, die den Entwicklungs- und Testprozess erheblich vereinfachen.

## 🚀 Quick Start

**Alle Server mit einem Befehl starten:**

```powershell
.\start-bulletproof.ps1
```

Das war's! Beide Server starten automatisch im Hintergrund ohne neue Fenster.

---

## 📁 Verfügbare Skripte

### 1. `start-bulletproof.ps1` (Hauptverzeichnis) - ⭐ EMPFOHLEN

**Zweck:** Bulletproof Master-Skript zum Starten aller Services im Hintergrund
**Pfad:** `C:\Dev\Me(dia) Feed\start-bulletproof.ps1`

**Was es tut:**
1. ✓ Prüft alle Voraussetzungen (Python, Node.js, Docker)
2. ✓ Startet PostgreSQL und Redis via Docker
3. ✓ Startet Backend im Hintergrundprozess (kein neues Fenster)
4. ✓ Startet Frontend im Hintergrundprozess (kein neues Fenster)
5. ✓ Health Checks für alle Services
6. ✓ Monitoring und Selbstheilung bei Problemen

**Verwendung:**
```powershell
cd "C:\Dev\Me(dia) Feed"
.\start-bulletproof.ps1
```

**Voraussetzungen:**
- Python 3.9+ installiert
- Node.js 18+ installiert  
- Docker Desktop installiert
- Alle anderen Komponenten werden automatisch gestartet/installiert

---

### 2. `backend\start-backend.ps1`

**Zweck:** Startet nur den Backend-Server
**Pfad:** `C:\Dev\Me(dia) Feed\backend\start-backend.ps1`

**Was es tut:**
1. ✓ Setzt Umgebungsvariablen für lokale Entwicklung
2. ✓ Prüft PostgreSQL-Verbindung
3. ✓ Startet Uvicorn mit Auto-Reload

**Verwendung:**
```powershell
cd "C:\Dev\Me(dia) Feed\backend"
.\start-backend.ps1
```

**URLs nach dem Start:**
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

### 3. `frontend\start-frontend.ps1`

**Zweck:** Startet nur den Frontend-Server
**Pfad:** `C:\Dev\Me(dia) Feed\frontend\start-frontend.ps1`

**Was es tut:**
1. ✓ Prüft node_modules (installiert ggf. Dependencies)
2. ✓ Startet Next.js Development Server

**Verwendung:**
```powershell
cd "C:\Dev\Me(dia) Feed\frontend"
.\start-frontend.ps1
```

**URL nach dem Start:**
- Frontend: http://localhost:3000

---

### 4. `stop-bulletproof.ps1` (Hauptverzeichnis)

**Zweck:** Beendet alle via start-bulletproof.ps1 gestarteten Services
**Pfad:** `C:\Dev\Me(dia) Feed\stop-bulletproof.ps1`

**Was es tut:**
1. ✓ Stoppt Hintergrundprozesse (Backend & Frontend)
2. ✓ Stoppt Docker-Container (PostgreSQL & Redis)
3. ✓ Bereinigt alle Hintergrundjobs

**Verwendung:**
```powershell
cd "C:\Dev\Me(dia) Feed"
.\stop-bulletproof.ps1
```

---

## 🛠️ Troubleshooting

### Problem: "Execution Policy" Fehler

**Fehlermeldung:**
```
.\start-bulletproof.ps1 : File cannot be loaded because running scripts is disabled on this system.
```

**Lösung:**
```powershell
# PowerShell als Administrator öffnen
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### Problem: "PostgreSQL connection failed"

**Symptom:** Warnung beim Backend-Start

**Lösung:**
1. Prüfen Sie, ob PostgreSQL läuft:
   ```powershell
   # Windows Services prüfen
   Get-Service -Name postgresql*
   ```

2. Starten Sie PostgreSQL falls nötig:
   ```powershell
   # Als Administrator
   Start-Service postgresql-x64-18
   ```

3. Testen Sie die Verbindung:
   ```powershell
   $env:PGPASSWORD="Evangeline2019!"
   & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U mefeed_user -d mefeed -c "SELECT 1;"
   ```

---

### Problem: Redis nicht verfügbar

**Symptom:** Backend-Start zeigt Redis-Warnung

**Lösung:**

**Wenn Sie WSL nutzen:**
```bash
# In WSL-Terminal
sudo service redis-server start
redis-cli ping  # Sollte "PONG" zurückgeben
```

**Wenn Sie Memurai nutzen:**
1. Öffnen Sie Memurai-Dienst in Windows Services
2. Starten Sie den Dienst

**Wenn Sie Docker nutzen:**
```powershell
docker run -d -p 6379:6379 --name redis redis:latest
```

---

### Problem: "Port already in use"

**Symptom:** Server kann nicht starten, Port 8000 oder 3000 belegt

**Lösung:**
```powershell
# Finden Sie den Prozess
netstat -ano | findstr :8000    # Für Backend
netstat -ano | findstr :3000    # Für Frontend

# Beenden Sie den Prozess (PID aus obigem Befehl)
taskkill /PID <PID> /F

# Oder schließen Sie einfach das alte Terminal-Fenster
```

---

## 🔒 Sicherheitshinweise

Die Startup-Skripte sind für **lokale Entwicklung** und **Testing** konzipiert:

✅ **Lokale Entwicklung:**
- DEBUG=true
- CORS allow all origins
- Localhost-URLs
- Sicherer für schnelle Iterationen

❌ **NICHT für Produktion:**
- Keine Environment-Isolation
- Passwörter in Klartext
- Debug-Modus aktiviert
- Keine HTTPS

**Für Produktion:** Nutzen Sie Docker-Container mit separaten .env Files und Secrets Management.

---

## 🎯 Design-Philosophie

Die Skripte folgen den drei Entwickler-Personas:

### Technical Lead
- ✓ Klare Struktur und Modularität
- ✓ Automatisierte Prerequisite-Checks
- ✓ Umfassende Dokumentation

### Developer
- ✓ Schneller Einstieg (ein Befehl)
- ✓ Pragmatische Fehlermeldungen
- ✓ Minimale Reibung im Workflow

### Security Expert
- ✓ Trennung Development/Production
- ✓ Explizite Umgebungsvariablen
- ✓ Keine hinterlistigen Defaults

---

## 📝 Wartung

### Skripte anpassen

Falls Sie Ports oder Konfiguration ändern möchten:

**Backend-Port ändern:**
```powershell
# In backend/start-backend.ps1, Zeile am Ende ändern:
& "./venv/Scripts/python.exe" -m uvicorn app.main:app --reload --port 8001

# Dann in frontend/.env.local:
NEXT_PUBLIC_API_URL=http://localhost:8001
```

**Frontend-Port ändern:**
```powershell
# In frontend/start-frontend.ps1:
npm run dev -- --port 3001
```

---

## 📚 Weitere Ressourcen

- [MANUAL_TESTING_ANLEITUNG.md](./MANUAL_TESTING_ANLEITUNG.md) - Vollständige Testanleitung
- [backend/.env](./backend/.env) - Backend-Konfiguration
- [frontend/.env.local](./frontend/.env.local) - Frontend-Konfiguration

---

**Version:** 1.0
**Erstellt:** 21. Oktober 2025
**Autor:** Claude Code (basierend auf Developer, Technical Lead, Security Expert Personas)

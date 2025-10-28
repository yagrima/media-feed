# Frontend Railway Deployment - Korrekte Methode

## ✅ Wie das Backend deployed wurde (Referenz)

Das Backend nutzt:
- **railway.json im ROOT** mit:
  ```json
  {
    "dockerfilePath": "backend/Dockerfile",
    "dockerContext": "."
  }
  ```
- **Dockerfile** kopiert mit `COPY backend/` die richtigen Dateien

## 🎯 Frontend Deployment - Korrekter Ansatz

Da Railway nur EINE `railway.json` pro Service liest, haben wir folgende Optionen:

### Option A: Environment Variable (EMPFOHLEN)

**Schritt 1: Neues Service in Railway erstellen**
1. Railway Dashboard öffnen: https://railway.app/project/empathetic-miracle
2. Klick **"+ New"** → **"GitHub Repo"**
3. Wähle Repository: `yagrima/media-feed`

**Schritt 2: Service konfigurieren**
- **Name**: frontend
- **WICHTIG**: Setze Environment Variable:
  ```
  RAILWAY_DOCKERFILE_PATH=frontend/Dockerfile
  ```

**Schritt 3: Weitere Environment Variables**
```
NEXT_PUBLIC_API_URL=https://media-feed-production.up.railway.app
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1
```

**Schritt 4: Deploy**
- Railway baut automatisch mit `frontend/Dockerfile` und Root-Context
- Das Dockerfile wurde bereits angepasst: `COPY frontend/ .`

---

### Option B: Separate railway.json via CLI

Wenn du die Railway CLI nutzt, kannst du spezifizieren welche Config-Datei genutzt werden soll:

```bash
cd frontend/
railway up --service frontend
```

Railway nutzt dann automatisch die `frontend/railway.json`

---

## ✅ Angepasstes Frontend Dockerfile

Das Dockerfile wurde angepasst für Root-Context:

```dockerfile
# Dependencies
COPY frontend/package.json frontend/package-lock.json* ./

# Code
COPY frontend/ .
```

Dies funktioniert mit `dockerContext: "."` (Root des Repos)

---

## 📋 Komplette Deployment-Schritte

1. ✅ Dockerfile angepasst (bereits gemacht)
2. ✅ Änderungen committen und pushen
3. ⏳ Railway Service erstellen mit RAILWAY_DOCKERFILE_PATH
4. ⏳ Environment Variables setzen
5. ⏳ Deploy abwarten
6. ⏳ Backend CORS aktualisieren
7. ⏳ Testen

---

## 🚨 WICHTIG: Keine "Root Directory" Option mehr

Railway hat die "Root Directory" Option entfernt. Stattdessen:
- `dockerContext` in railway.json
- `RAILWAY_DOCKERFILE_PATH` Environment Variable
- Dockerfile-Pfade müssen relativ zum dockerContext sein

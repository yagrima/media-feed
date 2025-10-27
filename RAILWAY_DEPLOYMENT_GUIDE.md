# 🚂 Railway Deployment Guide - Me(dia) Feed

**Status**: Ready to Deploy  
**Estimated Time**: 45-60 minutes  
**Prerequisites**: GitHub account, Railway account

---

## 📋 Overview

Dieses Deployment verwendet:
- **Railway Backend Service** (mit Dockerfile)
- **Railway PostgreSQL Plugin** (managed database)
- **Railway Redis Plugin** (managed cache)

---

## 🔐 Schritt 1: Secrets vorbereiten (lokal)

Bevor du deployst, musst du deine lokalen Secrets in Railway-kompatible ENV-Variablen umwandeln.

### 1.1 JWT Keys als ENV-Variable formatieren

```powershell
# In deinem lokalen Projekt (PowerShell)
cd "C:\Dev\Me(dia) Feed"

# JWT Private Key (multiline → single line mit \n)
$privateKey = Get-Content "..\Media Feed Secrets\secrets\jwt_private.pem" -Raw
$privateKeyEnv = $privateKey -replace "`r`n", "\n" -replace "`n", "\n"
Write-Host "JWT_PRIVATE_KEY=" -NoNewline
Write-Host $privateKeyEnv

# JWT Public Key
$publicKey = Get-Content "..\Media Feed Secrets\secrets\jwt_public.pem" -Raw
$publicKeyEnv = $publicKey -replace "`r`n", "\n" -replace "`n", "\n"
Write-Host "JWT_PUBLIC_KEY=" -NoNewline
Write-Host $publicKeyEnv

# Encryption Key (base64 encoded binary)
$encKey = Get-Content "..\Media Feed Secrets\secrets\encryption.key" -Raw
Write-Host "ENCRYPTION_KEY=$encKey"

# Secret Key
$secretKey = Get-Content "..\Media Feed Secrets\secrets\secret_key.txt" -Raw
Write-Host "SECRET_KEY=$secretKey"
```

**⚠️ Wichtig**: Kopiere diese Ausgaben in eine sichere Textdatei (nicht ins Git!). Du brauchst sie gleich in Railway.

---

## 🚀 Schritt 2: Railway Projekt erstellen

### 2.1 Railway Account & GitHub verbinden

1. Gehe zu [railway.app](https://railway.app)
2. Klicke **"Start a New Project"**
3. Wähle **"Deploy from GitHub repo"**
4. Autorisiere Railway für dein GitHub-Konto
5. Wähle das Repository **"Me(dia) Feed"**

### 2.2 PostgreSQL hinzufügen

1. Im Railway Dashboard: Klicke **"+ New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway erstellt automatisch die Datenbank
3. Notiere dir die **DATABASE_URL** (oder merke, wo du sie findest: Service → Variables → DATABASE_URL)

### 2.3 Redis hinzufügen

1. Im Railway Dashboard: Klicke **"+ New"** → **"Database"** → **"Add Redis"**
2. Railway erstellt automatisch Redis
3. Notiere dir die **REDIS_URL** (oder merke: Service → Variables → REDIS_URL)

---

## ⚙️ Schritt 3: Backend Service konfigurieren

### 3.1 Service Settings

1. Gehe zu deinem **Backend Service** (das aus GitHub importiert wurde)
2. Klicke auf **"Settings"**
3. **Root Directory**: Setze auf `backend`
4. **Builder**: Sollte automatisch "Dockerfile" erkennen

### 3.2 Environment Variables setzen

Gehe zu **"Variables"** Tab und füge folgende Variablen hinzu:

#### 🔐 Secrets (aus Schritt 1)
```bash
JWT_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\nMIIEvgIBA...(dein Key)\n-----END PRIVATE KEY-----
JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----\nMIIBIjANB...(dein Key)\n-----END PUBLIC KEY-----
ENCRYPTION_KEY=gAAAAAB...(dein Encryption Key)
SECRET_KEY=dein_secret_key_mindestens_32_zeichen
```

#### 📧 Email (Brevo SMTP)
```bash
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=deine_brevo_email@example.com
SMTP_PASSWORD=dein_brevo_smtp_password
FROM_EMAIL=noreply@deinedomain.com
```

#### 🔗 Database & Redis (automatisch von Railway gesetzt)
Diese werden automatisch von Railway bereitgestellt:
- `DATABASE_URL` (von PostgreSQL Plugin)
- `REDIS_URL` (von Redis Plugin)

**Prüfe**, ob diese Variablen vorhanden sind. Falls nicht, erstelle Service-Links:
1. Gehe zu Backend Service → **"Settings"** → **"Service Variables"**
2. Klicke **"+ Add Reference"**
3. Wähle PostgreSQL → `DATABASE_URL`
4. Wähle Redis → `REDIS_URL`

#### 🌐 App Configuration
```bash
DEBUG=false
APP_NAME=Me Feed
APP_VERSION=1.1.0

# CORS (später durch deine Railway-Domain ersetzen)
ALLOWED_ORIGINS=https://your-frontend.railway.app
ALLOWED_HOSTS=your-backend.railway.app

# Feature Flags
ENABLE_EMAIL_VERIFICATION=true
ENABLE_2FA=false
```

#### 🎯 TMDB API (falls du Media-Daten nutzt)
```bash
TMDB_API_KEY=dein_tmdb_api_key
```

---

## 🚢 Schritt 4: Deploy starten

### 4.1 Ersten Deployment triggern

1. Railway sollte automatisch deployen, sobald du die Variablen gesetzt hast
2. Falls nicht: Gehe zu **"Deployments"** → Klicke **"Deploy"**

### 4.2 Logs überwachen

1. Gehe zu **"Deployments"** → Neuester Deploy
2. Klicke auf **"View Logs"**
3. Achte auf:
   ```
   ✓ JWT private key written to file
   ✓ JWT public key written to file
   ✓ Encryption key written to file
   ✓ All secrets configured successfully
   🚀 Starting application...
   ```

### 4.3 Health Check testen

Sobald der Deploy erfolgreich ist:
1. Kopiere die **Railway-URL** deines Backend Service (z.B. `https://mefeed-backend-production.up.railway.app`)
2. Öffne im Browser: `https://your-backend.railway.app/health`
3. Erwartete Antwort:
   ```json
   {
     "status": "healthy",
     "service": "Me Feed",
     "version": "1.1.0"
   }
   ```

---

## 🗄️ Schritt 5: Datenbank initialisieren

### 5.1 Database Migrations ausführen

Railway bietet keine direkte Shell, aber du kannst Migrations über ein Python-Script triggern:

**Option A: Lokal mit Railway DB URL**
```powershell
# Lokal auf deinem PC
cd "C:\Dev\Me(dia) Feed\backend"

# Setze DATABASE_URL von Railway
$env:DATABASE_URL = "postgresql://postgres:password@region.railway.app:5432/railway"

# Migrations ausführen
.\venv\Scripts\activate
alembic upgrade head
```

**Option B: Railway CLI** (empfohlen)
```bash
# Installiere Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link zu deinem Projekt
railway link

# Run migrations
railway run alembic upgrade head
```

---

## 🧪 Schritt 6: Integration Tests

### 6.1 Test User Registration

```bash
# POST /api/auth/register
curl -X POST https://your-backend.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!",
    "username": "testuser"
  }'
```

Erwartete Antwort:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### 6.2 Test Email Sending

Prüfe, ob Verification-Email angekommen ist (falls ENABLE_EMAIL_VERIFICATION=true).

---

## 📊 Schritt 7: Monitoring & Logs

### 7.1 Railway Dashboard

- **Metrics**: CPU, Memory, Network im Service-Dashboard
- **Logs**: Echtzeit-Logs unter "Deployments"
- **Incidents**: Automatische Benachrichtigung bei Crashes

### 7.2 Custom Domain (optional)

1. Gehe zu Backend Service → **"Settings"** → **"Domains"**
2. Klicke **"+ Add Custom Domain"**
3. Füge deine Domain hinzu (z.B. `api.mefeed.com`)
4. Konfiguriere DNS (CNAME oder A-Record)
5. Railway generiert automatisch SSL-Zertifikat

---

## 🛠️ Troubleshooting

### Problem: "JWT_PRIVATE_KEY environment variable not set"

**Lösung**: 
- Stelle sicher, dass die ENV-Variable **JWT_PRIVATE_KEY** (nicht JWT_PRIVATE_KEY_PATH) gesetzt ist
- Format muss `\n` für Zeilenumbrüche enthalten (nicht echte Newlines)

### Problem: "Database connection failed"

**Lösung**:
- Prüfe, ob **DATABASE_URL** in Backend Service vorhanden ist
- Falls nicht: Service-Link zu PostgreSQL Plugin erstellen
- Format sollte sein: `postgresql://user:password@host:port/db`

### Problem: "Redis connection timeout"

**Lösung**:
- Prüfe **REDIS_URL** in Backend Service
- Falls nicht: Service-Link zu Redis Plugin erstellen
- Format: `redis://default:password@host:port`

### Problem: "Health check failing"

**Lösung**:
1. Prüfe Logs: `railway logs`
2. Teste manuell: `curl https://your-backend.railway.app/health`
3. Checke, ob alle Secrets korrekt gesetzt sind

---

## 💰 Kosten-Übersicht

### Railway Pricing (Stand Oktober 2025)

**Hobby Plan** (empfohlen für MVP):
- **$5/Monat** pro Service (Backend)
- **PostgreSQL**: $5/Monat
- **Redis**: $5/Monat
- **Gesamt**: ~$15/Monat

**Pro Plan** (für Production):
- **$20/Monat** pro Service
- **PostgreSQL**: $10/Monat (HA)
- **Redis**: $10/Monat (HA)
- **Gesamt**: ~$40/Monat

### Free Tier Limits
- $5 gratis Credits pro Monat
- Nur für Development/Testing nutzbar

---

## 🎉 Success Checklist

Nach erfolgreichem Deployment sollte alles funktionieren:

- [ ] Backend Service läuft ohne Errors
- [ ] `/health` Endpoint antwortet mit Status 200
- [ ] PostgreSQL Plugin verbunden
- [ ] Redis Plugin verbunden
- [ ] User Registration funktioniert
- [ ] JWT Tokens werden generiert
- [ ] Email Verification sendet Emails (falls aktiviert)
- [ ] Logs zeigen keine kritischen Errors
- [ ] Railway Dashboard zeigt "Healthy" Status

---

## 📚 Nächste Schritte

Nach erfolgreichem Backend-Deployment:

1. **Frontend deployen** (Next.js auf Railway/Vercel)
2. **Custom Domain** konfigurieren
3. **Monitoring** erweitern (Sentry, LogTail)
4. **Backup-Strategy** planen
5. **CI/CD Pipeline** mit GitHub Actions

---

## 🆘 Support

Bei Problemen:
- Railway Docs: [docs.railway.app](https://docs.railway.app)
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- GitHub Issues: Erstelle ein Issue im Repository

---

**Viel Erfolg mit dem Deployment! 🚀**

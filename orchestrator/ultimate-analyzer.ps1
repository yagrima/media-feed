# Ultimate Me Feed Analyzer mit robuster Port-Bereinigung
# Automatische Projektanalyse und intelligentes Konflikt-Management

param([switch]$NoAutoStart, [switch]$ForceCleanup)

Write-Host "" -ForegroundColor Cyan
Write-Host "🔧 Ultimate Me Feed Analyzer mit Port-Konflikt-Management" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $time = Get-Date -Format "HH:mm:ss"
    $color = switch($Level) { "SUCCESS" { "Green" } "WARN" { "Yellow" } "ERROR" { "Red" } default { "Gray" } }
    Write-Host "[$time] [ULTIMATE] $Message" -ForegroundColor $color
}

function Test-ProjectServices {
    $services = @{}
    try { 
        $resp = Invoke-WebRequest -Uri http://localhost:3000 -TimeoutSec 2 -ErrorAction Stop
        $services.Frontend = $resp.StatusCode -eq 200 
    } catch { $services.Frontend = $false }
    
    try { 
        $resp = Invoke-WebRequest -Uri http://localhost:8000/health -TimeoutSec 2 -ErrorAction Stop  
        $services.Backend = $resp.StatusCode -eq 200
    } catch { $services.Backend = $false }
    
    try { 
        $db = docker-compose -f docker-compose-simple.yml ps 2>$null
        $services.Database = $db -match "Up" -and $db.Count -ge 2 
    } catch { $services.Database = $false }
    
    return $services
}

function Invoke-PortCleanup {
    param([switch]$ForceMode)
    
    Write-Log "Starte umfassende Port-Bereinigung..." "WARN"
    
    $cleanupScript = Join-Path $PSScriptRoot "port-cleanup.ps1"
    
    try {
        if ($ForceMode) {
            Write-Log "Modus: ERZWUNGEN (alle Prozesse, Vorsicht!)" "WARN"
            & $cleanupScript -Ports @(3000, 8000, 5432, 6379) -Force -ErrorAction SilentlyContinue
        } else {
            Write-Log "Modus: SICHER (nur Me Feed Prozesse)" "INFO"
            & $cleanupScript -Ports @(3000, 8000) -ErrorAction SilentlyContinue
        }
        
        $success = ($LASTEXITCODE -eq 0)
        if ($success) {
            Write-Log "Port-Bereinigung erfolgreich" "SUCCESS"
        } else {
            Write-Log "Port-Bereinigung teilweise erfolgreich" "WARN"
        }
        
        return $success
        
    } catch {
        Write-Log "Port-Bereinigung Fehler: $_" "WARN"
        return $false
    }
}

function Start-ServicesIntelligently {
    if ($NoAutoStart) {
        Write-Log "Auto-Start deaktiviert" "WARN"
        return
    }
    
    $current = Test-ProjectServices
    $allRunning = $current.Frontend -and $current.Backend -and $current.Database
    
    if ($allRunning) {
        Write-Log "Alle Services bereits aktiv - keine Aktion nötig" "SUCCESS"
        return
    }
    
    Write-Log "Intelligenter Service-Start wird initialisiert..." "INFO"
    
    # Port-Bereinigung wenn Backend oder Frontend fehlt
    if (-not $current.Backend -or -not $current.Frontend) {
        Write-Log "Port-Konflikte erkannt - bereinige Ports" "WARN"
        Invoke-PortCleanup -ForceMode:$ForceCleanup
        Start-Sleep -Seconds 5
    }
    
    try {
        # Datenbank
        if (-not $current.Database) {
            Write-Log "Starte Datenbank-Dienste..." "INFO"
            docker-compose -f docker-compose-simple.yml down 2>$null
            docker-compose -f docker-compose-simple.yml up -d
            Start-Sleep -Seconds 5
        }
        
        # Frontend
        if (-not $current.Frontend) {
            Write-Log "Starte Frontend (Next.js)..." "INFO"
            try {
                Start-Process -WorkingDirectory "frontend" npm -ArgumentList "run", "dev" -WindowStyle Hidden
                Write-Log "Frontend-Startprozess initialisiert" "SUCCESS"
            } catch {
                Write-Log "Frontend-Start fehlgeschlagen: $_" "ERROR"
            }
            Start-Sleep -Seconds 8
        }
        
        # Backend
        if (-not $current.Backend) {
            Write-Log "Starte Backend (FastAPI)..." "INFO"
            try {
                $backendCommand = ".\venv\Scripts\activate.ps1; python minimal_app.py"
                Start-Process -WorkingDirectory "backend" powershell -ArgumentList "-Command", $backendCommand -WindowStyle Hidden
                Write-Log "Backend-Startprozess initialisiert" "SUCCESS"
            } catch {
                Write-Log "Backend-Start fehlgeschlagen: $_" "ERROR"
            }
            Start-Sleep -Seconds 8
        }
        
    } catch {
        Write-Log "Service-Start Fehler: $_" "ERROR"
    }
}

function Show-ComprehensiveStatus {
    $services = Test-ProjectServices
    
    Write-Host "`n" + "="*50 -ForegroundColor White
    Write-Host "📊 COMPREHENSIVER PROJEKT-STATUS" -ForegroundColor White
    Write-Host "="*50 -ForegroundColor White
    
    $frontendStatus = if ($services.Frontend) { 
        "✅ AKTIV - http://localhost:3000" 
    } else { 
        "❌ INAKTIV - Port 3000" 
    }
    
    $backendStatus = if ($services.Backend) { 
        "✅ AKTIV - http://localhost:8000" 
    } else { 
        "❌ INAKTIV - Port 8000" 
    }
    
    $dbStatus = if ($services.Database) { 
        "✅ AKTIV - PostgreSQL + Redis" 
    } else { 
        "❌ INAKTIV - Container" 
    }
    
    Write-Host "" -ForegroundColor White
    Write-Host "Frontend: $frontendStatus" -ForegroundColor $(if ($services.Frontend) { "Green" } else { "Red" })
    Write-Host "Backend:  $backendStatus" -ForegroundColor $(if ($services.Backend) { "Green" } else { "Red" })
    Write-Host "Database: $dbStatus" -ForegroundColor $(if ($services.Database) { "Green" } else { "Red" })
    
    # Port-Eckdaten
    Write-Host "" -ForegroundColor White
    Write-Host "Port-Informationen:" -ForegroundColor Gray
    try {
        $port3000 = netstat -ano | findstr ":3000" | Measure-Object
        $port8000 = netstat -ano | findstr ":8000" | Measure-Object
        Write-Host "  Port 3000: $($port3000.Count) Prozess(e)" -ForegroundColor Gray
        Write-Host "  Port 8000: $($port8000.Count) Prozess(e)" -ForegroundColor Gray
    } catch {
        Write-Host "  Port-Information nicht verfügbar" -ForegroundColor Gray
    }
    
    # Zusammenfassender Status
    Write-Host "" -ForegroundColor White
    $status = $services.Frontend -and $services.Backend -and $services.Database
    if ($status) {
        Write-Host "🎉 PROJEKT IST BEREIT FÜR VOLLSTÄNDIGE ANALYSE!" -ForegroundColor Green
        Write-Host "   Frontend Test: http://localhost:3000" -ForegroundColor Cyan
        Write-Host "   API Test:     http://localhost:8000/docs" -ForegroundColor Cyan
    } else {
        Write-Host "⚠️  PROJEKT IST TEILWEISE VERFÜGBAR" -ForegroundColor Yellow
        $missing = @()
        if (-not $services.Frontend) { $missing += "Frontend" }
        if (-not $services.Backend) { $missing += "Backend" }
        if (-not $services.Database) { $missing += "Database" }
        Write-Host "   Fehlende Services: $($missing -join ', ')" -ForegroundColor Yellow
    }
    
    Write-Host "" -ForegroundColor White
    Write-Host "="*50 -ForegroundColor White
    
    # Status speichern
    $statusObj = @{
        Services = $services
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        AllRunning = $services.Frontend -and $services.Backend -and $services.Database
        ForceCleanupUsed = $ForceCleanup
    }
    
    $statusObj | ConvertTo-Json -Depth 10 | Out-File -FilePath "current-project-status.json" -Encoding UTF8
    
    return $statusObj
}

# Hauptausführung
Write-Log "Ultimate Analyzer mit Port-Konflikt-Management wird initialisiert..." "INFO"

# Vor Analyse Port-Status zeigen
Write-Log "Prüfe initialen Port-Status..." "INFO"
$initialCleanup = Invoke-PortCleanup

if (-not $NoAutoStart) {
    Start-ServicesIntelligently
}

$finalStatus = Show-ComprehensiveStatus

if ($finalStatus.AllRunning) {
    Write-Log "Ultimate Analyse abgeschlossen - Projekt voll betriebsbereit!" "SUCCESS"
    exit 0
} else {
    Write-Log "Ultimate Analyse abgeschlossen - Projekt teilweise betriebsbereit" "WARN"
    Write-Log "Tipp: Verwenden Sie -ForceCleanup für aggressive Port-Bereinigung" "INFO"
    exit 1
}

# Smart Analyzer für Me Feed mit automatischem Projektstart
# Wird vom Orchestrator bei jeder Analyse automatisch ausgeführt

param([switch]$NoAutoStart)

Write-Host "" -ForegroundColor Cyan
Write-Host "🤖 Me Feed Smart Analyzer - Automatische Projektprüfung & Start" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $time = Get-Date -Format "HH:mm:ss"
    $color = switch($Level) { "SUCCESS" { "Green" } "WARN" { "Yellow" } "ERROR" { "Red" } default { "Gray" } }
    Write-Host "[$time] 🤖 $Message" -ForegroundColor $color
}

function Test-ServicesQuick {
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

function Ensure-ServicesRunning {
    if ($NoAutoStart) {
        Write-Log "Auto-Start deaktiviert" "WARN"
        return
    }
    
    $current = Test-ServicesQuick
    $allRunning = $current.Frontend -and $current.Backend -and $current.Database
    
    if ($allRunning) {
        Write-Log "✅ Alle Services bereits aktiv - Analyse beginnt sofort" "SUCCESS"
        return
    }
    
    Write-Log "🚀 Starte benötigte Services automatisch..." "INFO"
    
    try {
        # Datenbank prüfen/starten
        if (-not $current.Database) {
            Write-Log "Starte Datenbanken..." "INFO"
            docker-compose -f docker-compose-simple.yml down 2>$null
            docker-compose -f docker-compose-simple.yml up -d
            Start-Sleep -Seconds 3
        }
        
        # Frontend prüfen/starten
        if (-not $current.Frontend) {
            Write-Log "Starte Frontend..." "INFO"
            Start-Process -WorkingDirectory "frontend" npm -ArgumentList "run", "dev" -WindowStyle Hidden
            Start-Sleep -Seconds 5
        }
        
        # Backend prüfen/starten
        if (-not $current.Backend) {
            Write-Log "Starte Backend..." "INFO"
            
            # Prüfen ob Port frei ist
            $portInUse = $false
            try {
                $port = netstat -ano | findstr ":8000"
                if ($port) {
                    Write-Log "Port 8000 belegt, beende Prozess..." "WARN"
                    $portInUse = $true
                    
                    # Beende den Prozess
                    $pid = ($port -split "\s+")[4] | Select-Object -First 1
                    if ($pid) {
                        taskkill /F /PID $pid 2>$null
                        Start-Sleep -Seconds 2
                    }
                }
            } catch {}
            
            # Backend starten
            try {
                Start-Process -WorkingDirectory "backend" powershell -ArgumentList "-Command", ".\venv\Scripts\activate.ps1; python minimal_app.py" -WindowStyle Hidden
                Start-Sleep -Seconds 3
            } catch {
                Write-Log "Backend Start fehlgeschlagen: $_" "ERROR"
            }
        }
        
        # Kurze Wartezeit und finaler Check
        Start-Sleep -Seconds 5
        $final = Test-ServicesQuick
        
        if ($final.Frontend -and $final.Backend) {
            Write-Log "🎉 Alle Services erfolgreich gestartet!" "SUCCESS"
        } elseif ($final.Frontend) {
            Write-Log "⚠️ Nur Frontend aktiv - Backend hat Startprobleme" "WARN"
        } else {
            Write-Log "❌ Services konnten nicht vollständig gestartet werden" "ERROR"
        }
        
    } catch {
        Write-Log "Start-Prozess Fehler: $_" "ERROR"
    }
}

function Show-ProjectStatus {
    $services = Test-ServicesQuick
    
    Write-Host "`n📊 Projekt-Status:" -ForegroundColor White
    
    Write-Host "Frontend: $(if ($services.Frontend) { '✅ http://localhost:3000' } else { '❌ Nicht erreichbar' })" -ForegroundColor $(if ($services.Frontend) { "Green" } else { "Red" })
    Write-Host "Backend:  $(if ($services.Backend) { '✅ http://localhost:8000' } else { '❌ Nicht erreichbar' })" -ForegroundColor $(if ($services.Backend) { "Green" } else { "Red" })
    Write-Host "DB:       $(if ($services.Database) { '✅ PostgreSQL + Redis' } else { '❌ Nicht erreichbar' })" -ForegroundColor $(if ($services.Database) { "Green" } else { "Red" })
    
    $status = @{
        Services = $services
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        AllRunning = $services.Frontend -and $services.Backend -and $services.Database
    }
    
    # Status für Orchestrator speichern
    $status | ConvertTo-Json -Depth 10 | Out-File -FilePath "orchestrator\current-status.json" -Encoding UTF8
    
    return $status
}

# Hauptausführung
Write-Log "Smart Analyzer wird initialisiert..." "INFO"

if (-not $NoAutoStart) {
    Ensure-ServicesRunning
}

$status = Show-ProjectStatus

if ($status.AllRunning) {
    Write-Host "`n🚀 Projekt ist bereit für vollständige Analyse!" -ForegroundColor Green
    Write-Host "Frontend Test: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "API Test:     http://localhost:8000/docs" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host "`n Analyse kann mit teilweisen Services fortgesetzt werden" -ForegroundColor Yellow
    exit 1
}

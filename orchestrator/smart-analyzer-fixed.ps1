# Smart Analyzer für Me Feed mit automatischem Projektstart

param([switch]$NoAutoStart)

Write-Host "" -ForegroundColor Cyan
Write-Host "Me Feed Smart Analyzer - Automatische Projektpruefung" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $time = Get-Date -Format "HH:mm:ss"
    $color = switch($Level) { "SUCCESS" { "Green" } "WARN" { "Yellow" } "ERROR" { "Red" } default { "Gray" } }
    Write-Host "[$time] [SMART] $Message" -ForegroundColor $color
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

function Start-IfNeeded {
    if ($NoAutoStart) {
        Write-Log "Auto-Start deaktiviert"
        return
    }
    
    $current = Test-ProjectServices
    $allRunning = $current.Frontend -and $current.Backend -and $current.Database
    
    if ($allRunning) {
        Write-Log "Alle Services bereits aktiv" "SUCCESS"
        return
    }
    
    Write-Log "Starte Services automatisch..." "INFO"
    
    try {
        # Datenbank
        if (-not $current.Database) {
            Write-Log "Starte Datenbank..."
            docker-compose -f docker-compose-simple.yml down 2>$null
            docker-compose -f docker-compose-simple.yml up -d
            Start-Sleep -Seconds 3
        }
        
        # Frontend
        if (-not $current.Frontend) {
            Write-Log "Starte Frontend..."
            Start-Process -WorkingDirectory "frontend" npm -ArgumentList "run", "dev" -WindowStyle Minimized
            Start-Sleep -Seconds 5
        }
        
        # Backend
        if (-not $current.Backend) {
            Write-Log "Starte Backend..."
            try {
                # Port pruefen und ggf. beenden
                $portCheck = netstat -ano | findstr ":8000"
                if ($portCheck) {
                    $pid = ($portCheck -split "\s+")[4] | Select-Object -First 1
                    if ($pid) { taskkill /F /PID $pid 2>$null }
                    Start-Sleep -Seconds 2
                }
                
                Start-Process -WorkingDirectory "backend" powershell -ArgumentList "-Command", ".\venv\Scripts\activate.ps1; python minimal_app.py" -WindowStyle.Minimized
                Start-Sleep -Seconds 5
            } catch {
                Write-Log "Backend Start fehlgeschlagen: $_" "ERROR"
            }
        }
        
    } catch {
        Write-Log "Start-Fehler: $_" "ERROR"
    }
}

function Show-Status {
    $services = Test-ProjectServices
    
    Write-Host "`nProjekt-Status:" -ForegroundColor White
    
    $frontendStatus = if ($services.Frontend) { "OK - http://localhost:3000" } else { "NICHT ERREICHBAR" }
    $backendStatus = if ($services.Backend) { "OK - http://localhost:8000" } else { "NICHT ERREICHBAR" }  
    $dbStatus = if ($services.Database) { "OK - PostgreSQL + Redis" } else { "NICHT ERREICHBAR" }
    
    Write-Host "Frontend: $frontendStatus" -ForegroundColor $(if ($services.Frontend) { "Green" } else { "Red" })
    Write-Host "Backend:  $backendStatus" -ForegroundColor $(if ($services.Backend) { "Green" } else { "Red" })
    Write-Host "Database: $dbStatus" -ForegroundColor $(if ($services.Database) { "Green" } else { "Red" })
    
    $status = @{
        Services = $services
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        AllRunning = $services.Frontend -and $services.Backend -and $services.Database
    }
    
    # Status speichern
    $status | ConvertTo-Json -Depth 10 | Out-File -FilePath "current-project-status.json" -Encoding UTF8
    
    return $status
}

# Hauptausführung
Write-Log "Smart Analyzer initialisiert" "INFO"

if (-not $NoAutoStart) {
    Start-IfNeeded
}

$finalStatus = Show-Status

if ($finalStatus.AllRunning) {
    Write-Host "`nProjekt bereit fuer Analyse!" -ForegroundColor Green
    Write-Host "Frontend Test: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "API Test:     http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    exit 0
} else {
    Write-Host "`nAnalyse moeglich (teilweise Services)" -ForegroundColor Yellow
    exit 1
}

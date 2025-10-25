# Schneller Start für Orchestrator Integration
param(
    [switch]$Force
)

Write-Host "[ORCHESTRATOR] Schnellstart wird initialisiert..." -ForegroundColor Cyan

# Erst prüfen ob bereits alles läuft
function Test-Services {
    $running = @{}
    
    try {
        $frontend = Invoke-WebRequest -Uri http://localhost:3000 -TimeoutSec 1 -ErrorAction Stop
        $running.Frontend = ($frontend.StatusCode -eq 200)
    } catch { $running.Frontend = $false }
    
    try {
        $backend = Invoke-WebRequest -Uri http://localhost:8000/health -TimeoutSec 1 -ErrorAction Stop
        $running.Backend = ($backend.StatusCode -eq 200)
    } catch { $running.Backend = $false }
    
    try {
        $docker = docker-compose -f docker-compose-simple.yml ps 2>$null
        $running.Database = ($docker -match "Up" -and $docker.Count -ge 2)
    } catch { $running.Database = $false }
    
    return $running
}

$services = Test-Services

if ($services.Frontend -and $services.Backend -and $services.Database -and -not $Force) {
    Write-Host "[ORCHESTRATOR] Alle Services bereits aktiv!" -ForegroundColor Green
    return $true
}

Write-Host "[ORCHESTRATOR] Starte benötigte Services..." -ForegroundColor Yellow

# Datenbank starten
if (-not $services.Database -or $Force) {
    Write-Host "[ORCHESTRATOR] Starte Datenbanken (Daten bleiben erhalten)..." -ForegroundColor Gray
    docker-compose -f docker-compose-simple.yml down 2>$null
    # WICHTIG: Niemals -v verwenden, um Daten zu erhalten
    docker-compose -f docker-compose-simple.yml up -d
    Start-Sleep -Seconds 5
}

# Backend starten
if (-not $services.Backend -or $Force) {
    Write-Host "[ORCHESTRATOR] Starte Backend..." -ForegroundColor Gray
    $backendJob = Start-Job -ScriptBlock {
        Set-Location (Join-Path $using:PWD "backend")
        try {
            & .\venv\Scripts\activate.ps1
            python minimal_app.py
        } catch { Write-Host "Backend error: $_" }
    }
    Start-Sleep -Seconds 3
}

# Frontend starten  
if (-not $services.Frontend -or $Force) {
    Write-Host "[ORCHESTRATOR] Starte Frontend..." -ForegroundColor Gray
    $frontendJob = Start-Job -ScriptBlock {
        Set-Location (Join-Path $using:PWD "frontend")
        try {
            npm run dev
        } catch { Write-Host "Frontend error: $_" }
    }
    Start-Sleep -Seconds 5
}

# Prüfung
for ($i = 0; $i -lt 10; $i++) {
    Start-Sleep -Seconds 2
    $current = Test-Services
    
    Write-Host "[ORCHESTRATOR] Check $($i+1): Frontend=$($current.Frontend), Backend=$($current.Backend), Database=$($current.Database)" -ForegroundColor Gray
    
    if ($current.Frontend -and $current.Backend) {
        Write-Host "[ORCHESTRATOR] Projekt erfolgreich gestartet!" -ForegroundColor Green
        return $true
    }
}

Write-Host "[ORCHESTRATOR] Projekt teilweise gestartet - Analyse kann fortgesetzt werden" -ForegroundColor Yellow
return $false

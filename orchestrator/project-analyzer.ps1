# Me Feed Project Analyzer mit Auto-Start Integration
# Automatisch aufgerufen vom Orchestrator bei Projektanalysen

param(
    [string]$Mode = "analyze",
    [switch]$SkipStart
)

$ErrorActionPreference = "SilentlyContinue"

function Invoke-ProjectAnalysis {
    param([switch]$SkipAutoStart)
    
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "Me Feed Projekt Analyzer mit Auto-Start" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
    
    if (-not $SkipAutoStart) {
        Write-Host "Starte Auto-Start Integration..." -ForegroundColor Yellow
        
        # Auto-Start im Background aufrufen
        $autoStartScript = Join-Path $PSScriptRoot "auto-start-integration.ps1"
        
        try {
            $autoResult = & $autoStartScript
            $autoSuccess = ($LASTEXITCODE -eq 0)
            
            if ($autoSuccess) {
                Write-Host "Auto-Start erfolgreich: Projekt läuft" -ForegroundColor Green
            } else {
                Write-Host "Auto-Start teilweise erfolgreich" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "Auto-Start Fehler, fahre mit Analyse fort" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Auto-Start übersprungen (manuell)" -ForegroundColor Gray
    }
    
    # Projektstatus prüfen
    Write-Host "`nPrüfe Projektstatus..." -ForegroundColor Cyan
    
    $status = @{
        Frontend = $false
        Backend = $false
        Database = $false
        Timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    }
    
    # Service-Tests
    try {
        $frontendTest = Invoke-WebRequest -Uri http://localhost:3000 -TimeoutSec 3
        $status.Frontend = ($frontendTest.StatusCode -eq 200)
    } catch {}
    
    try {
        $backendTest = Invoke-WebRequest -Uri http://localhost:8000/health -TimeoutSec 3
        $status.Backend = ($backendTest.StatusCode -eq 200)
    } catch {}
    
    try {
        $dbTest = docker-compose -f docker-compose-simple.yml ps 2>$null
        $status.Database = ($dbTest -match "Up" -and $dbTest.Count -ge 2)
    } catch {}
    
    # Status-Report
    Write-Host "`nProjektstatus:" -ForegroundColor White
    
    if ($status.Frontend) {
        Write-Host "  Frontend:    ✅ http://localhost:3000" -ForegroundColor Green
    } else {
        Write-Host "  Frontend:    ❌ Nicht erreichbar" -ForegroundColor Red
    }
    
    if ($status.Backend) {
        Write-Host "  Backend:     ✅ http://localhost:8000" -ForegroundColor Green
    } else {
        Write-Host "  Backend:     ❌ Nicht erreichbar" -ForegroundColor Red
    }
    
    if ($status.Database) {
        Write-Host "  Datenbank:   ✅ PostgreSQL + Redis" -ForegroundColor Green
    } else {
        Write-Host "  Datenbank:   ❌ Nicht erreichbar" -ForegroundColor Red
    }
    
    # Nächste Schritte
    $allRunning = $status.Frontend -and $status.Backend -and $status.Database
    
    if ($allRunning) {
        Write-Host "`n🚀 Projekt ist voll funktionsfähig!" -ForegroundColor Green
        Write-Host "Frontend testing: http://localhost:3000" -ForegroundColor Cyan
        Write-Host "API testing:     http://localhost:8000/docs" -ForegroundColor Cyan
    } else {
        Write-Host "`n⚠️  Projekt teilweise verfügbar" -ForegroundColor Yellow
        
        if (-not $status.Frontend) {
            Write-Host "Frontend: Manuelles Start mit cd frontend && npm run dev" -ForegroundColor Gray
        }
        
        if (-not $status.Backend) {
            Write-Host "Backend:  Manuelles Start mit cd backend && python minimal_app.py" -ForegroundColor Gray
        }
        
        if (-not $status.Database) {
            Write-Host "Database:  Manuelles Start mit docker-compose -f docker-compose-simple.yml up -d" -ForegroundColor Gray
        }
    }
    
    # Status als JSON speichern für Orchestrator
    $statusJson = $status | ConvertTo-Json -Depth 10
    $statusJson | Out-File -FilePath (Join-Path $PSScriptRoot "..\project-status.json") -Encoding UTF8
    
    Write-Host "`n analysesc: Projektstatus gespeichert" -ForegroundColor Green
    return $status
}

# Main execution
switch ($Mode) {
    "analyze" {
        Invoke-ProjectAnalysis -SkipAutoStart:$SkipStart
    }
    "quickstart" {
        $autoStartScript = Join-Path $PSScriptRoot "auto-start-integration.ps1"
        & $autoStartScript
    }
    "status" {
        $autoStartScript = Join-Path $PSScriptRoot "auto-start-integration.ps1"
        & $autoStartScript -VerifyOnly
    }
    default {
        Write-Host "Unknown mode: $Mode" -ForegroundColor Red
        exit 1
    }
}

# Orchestrator Auto-Start Integration für Me Feed Projekt
# Wird automatisch bei Projektanalysen ausgeführt

param(
    [switch]$ForceRestart,
    [switch]$VerifyOnly
)

$ErrorActionPreference = "SilentlyContinue"
$ProgressPreference = "SilentlyContinue"

function Write-OrchestratorLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] [ORCHESTRATOR-$Level] $Message" -ForegroundColor $(switch($Level) {"ERROR" {"Red"} "WARN" {"Yellow"} default {"Gray"}})
}

function Test-ProjectRunning {
    $services = @{}
    
    # Frontend prüfen
    try {
        $frontend = Invoke-WebRequest -Uri http://localhost:3000 -TimeoutSec 2
        if ($frontend.StatusCode -eq 200) {
            $services.Frontend = $true
            Write-OrchestratorLog "Frontend läuft auf http://localhost:3000" "INFO"
        }
    } catch {
        $services.Frontend = $false
    }
    
    # Backend prüfen
    try {
        $backend = Invoke-WebRequest -Uri http://localhost:8000/health -TimeoutSec 2
        if ($backend.StatusCode -eq 200) {
            $services.Backend = $true
            Write-OrchestratorLog "Backend läuft auf http://localhost:8000" "INFO"
        }
    } catch {
        $services.Backend = $false
    }
    
    # Datenbank prüfen
    try {
        $dbStatus = docker-compose -f docker-compose-simple.yml ps 2>$null
        if ($dbStatus -match "Up") {
            $services.Database = $true
            Write-OrchestratorLog "Datenbanken laufen" "INFO"
        }
    } catch {
        $services.Database = $false
    }
    
    return $services
}

function Start-ProjectIfNeeded {
    param([bool]$Force)
    
    $currentServices = Test-ProjectRunning
    
    if ($Force) {
        Write-OrchestratorLog "Erzwungener Neustart (Daten bleiben erhalten)..." "WARN"
        try {
            & .\stop-bulletproof.ps1
            Start-Sleep -Seconds 2
        } catch {
            Write-OrchestratorLog "Stoppen fehlgeschlagen, geht weiter..." "WARN"
        }
    } else {
        $allRunning = ($currentServices.Frontend -eq $true -and 
                     $currentServices.Backend -eq $true -and 
                     $currentServices.Database -eq $true)
        
        if ($allRunning) {
            Write-OrchestratorLog "Alle Services bereits aktiv - Analysis kann beginnen" "INFO"
            return $true
        }
        
        Write-OrchestratorLog "Services unvollständig: Frontend=$($currentServices.Frontend), Backend=$($currentServices.Backend), Database=$($currentServices.Database)" "WARN"
    }
    
    Write-OrchestratorLog "Starte Me Feed Projekt im Hintergrund..." "INFO"
    
    try {
        # Projekt im Background starten
        $startScript = {
            param($ProjectPath)
            Set-Location $ProjectPath
            try {
                & .\start-bulletproof.ps1
            } catch {
                Write-Host "Background startup error: $_"
            }
        }
        
        Start-Job -ScriptBlock $startScript -ArgumentList (Get-Location) -Name "MeFeedAutoStart" | Out-Null
        
        # Warten und prüfen
        Write-OrchestratorLog "Warte auf Dienststart..." "INFO"
        $maxWait = 60
        $waited = 0
        
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds 3
            $waited += 3
            
            $services = Test-ProjectRunning
            
            if ($services.Frontend -and $services.Backend -and $services.Database) {
                Write-OrchestratorLog "Projekt erfolgreich gestartet (nach ${waited}s)" "INFO"
                return $true
            }
            
            Write-OrchestratorLog "Status nach ${waited}s: Frontend=$($services.Frontend), Backend=$($services.Backend), Database=$($services.Database)" "INFO"
        }
        
        Write-OrchestratorLog "Timeout beim Start - Projekt läuft möglicherweise teilweise" "WARN"
        return $false
        
    } catch {
        Write-OrchestratorLog "Fehler beim Projektstart: $_" "ERROR"
        return $false
    }
}

# Hauptlogik
Write-OrchestratorLog "Me Feed Auto-Start Integration aktiviert" "INFO"
Write-OrchestratorLog "Projektverzeichnis: $(Get-Location)" "INFO"

if ($VerifyOnly) {
    Write-OrchestratorLog "=== VERIFIKATIONSMODUS ===" "INFO"
    $services = Test-ProjectRunning
    Write-OrchestratorLog "Projektstatus: Frontend=$($services.Frontend), Backend=$($services.Backend), Database=$($services.Database)" "INFO"
    exit 0
}

$success = Start-ProjectIfNeeded -Force:$ForceRestart

if ($success) {
    Write-OrchestratorLog "Projekt bereit für Analyse" "INFO"
    Write-OrchestratorLog "Frontend: http://localhost:3000" "INFO"
    Write-OrchestratorLog "Backend:  http://localhost:8000" "INFO"
    Write-OrchestratorLog "API:      http://localhost:8000/docs" "INFO"
    exit 0
} else {
    Write-OrchestratorLog "Projektstart nicht vollständig - Analyse kann trotzdem erfolgen" "WARN"
    exit 1
}

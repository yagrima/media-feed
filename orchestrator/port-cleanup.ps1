# Robuste Port-Bereinigung für Me Feed Projekt
# Eliminiert Prozesse die auf项目 Ports laufen

param(
    [int[]]$Ports = @(3000, 8000, 5432, 6379),
    [switch]$Force,
    [switch]$Simulate
)

function Write-CleanupLog {
    param([string]$Message, [string]$Level = "INFO")
    $time = Get-Date -Format "HH:mm:ss"
    $color = switch($Level) { "KILL" { "Red" } "WARN" { "Yellow" } "SUCCESS" { "Green" } default { "Gray" } }
    Write-Host "[$time] [CLEANUP] $Message" -ForegroundColor $color
}

function Get-PortProcessInfo {
    param([int]$Port)
    
    try {
        $netstat = netstat -ano | findstr ":$Port"
        if (-not $netstat) {
            return $null
        }
        
        $processes = @()
        foreach ($line in $netstat) {
            # Parse netstat output
            $parts = $line -split "\s+" | Where-Object { $_ -ne "" }
            
            if ($parts.Count -ge 5) {
                $localAddress = $parts[1]
                $processId = $parts[$parts.Count - 1]
                
                if ($localAddress -match ":$Port`$") {
                    $processInfo = Get-Process -Id $processId -ErrorAction SilentlyContinue
                    
                    if ($processInfo) {
                        $processes += @{
                            PID = $processId
                            ProcessName = $processInfo.ProcessName
                            Path = $processInfo.Path
                            StartTime = $processInfo.StartTime
                            CommandLines = (Get-WmiObject Win32_Process -Filter "ProcessId=$pid" -ErrorAction SilentlyContinue).CommandLine
                            Port = $Port
                            LocalAddress = $localAddress
                        }
                    }
                }
            }
        }
        
        return $processes
    } catch {
        Write-CleanupLog "Fehler bei Port $Port Analyze: $_" "WARN"
        return $null
    }
}

function Test-IfMeFeedProcess {
    param([object]$ProcessInfo)
    
    if (-not $ProcessInfo) { return $false }
    
    # Check if it's a known Me Feed process
    $meFeedIndicators = @(
        "python.exe",
        "node.exe", 
        "npm",
        "uvicorn",
        "minimal_app.py",
        "next.js",
        "webpack",
        "react",
        "frontend",
        "backend"
    )
    
    # Check command line
    if ($ProcessInfo.CommandLines) {
        foreach ($indicator in $meFeedIndicators) {
            if ($ProcessInfo.CommandLines -like "*$indicator*") {
                return $true
            }
        }
    }
    
    # Check process name
    if ($ProcessInfo.ProcessName) {
        foreach ($indicator in $meFeedIndicators) {
            if ($ProcessInfo.ProcessName -like "*$indicator*") {
                return $true
            }
        }
    }
    
    # Check path
    if ($ProcessInfo.Path) {
        if ($ProcessInfo.Path -like "*Me Feed*" -or $ProcessInfo.Path -like "*mefeed*") {
            return $true
        }
    }
    
    return $false
}

function Remove-PortProcess {
    param([object]$ProcessInfo, [switch]$SimulateMode)
    
    if (-not $ProcessInfo) { return $false }
    
    try {
        if ($SimulateMode) {
            Write-CleanupLog "SIMULATION: Würde Prozess beenden: PID=$($ProcessInfo.PID), Name=$($ProcessInfo.ProcessName), Port=$($ProcessInfo.Port)" "WARN"
            return $true
        }
        
        # Safety check - never kill critical system processes
        $criticalProcesses = @("csrss.exe", "winlogon.exe", "lsass.exe", "svchost.exe", "explorer.exe")
        if ($ProcessInfo.ProcessName -in $criticalProcesses) {
            Write-CleanupLog "ÜBERSPRUNGEN: Kritischer Systemprozess $($ProcessInfo.ProcessName) PID=$($ProcessInfo.PID)" "WARN"
            return $false
        }
        
        Write-CleanupLog "Beende Prozess: PID=$($ProcessInfo.PID), Name=$($ProcessInfo.ProcessName), Port=$($ProcessInfo.Port)" "KILL"
        
        # Try graceful kill first
        Stop-Process -Id $ProcessInfo.PID -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        
        # Check if still running and force kill if needed
        $stillRunning = Get-Process -Id $ProcessInfo.PID -ErrorAction SilentlyContinue
        if ($stillRunning) {
            Write-CleanupLog "Erzwinge Beendigung für PID=$($ProcessInfo.PID)" "KILL"
            try {
                Stop-Process -Id $ProcessInfo.PID -Force -ErrorAction SilentlyContinue
            } catch {
                # Fallback wenn Stop-Process fehlschlägt
                taskkill /F /PID $ProcessInfo.PID 2>$null
            }
            Start-Sleep -Seconds 1
        }
        
        return $true
        
    } catch {
        Write-CleanupLog "Fehler beim Beenden von PID=$($ProcessInfo.PID): $_" "WARN"
        return $false
    }
}

function Clear-PortsComprehensive {
    param([int[]]$TargetPorts, [switch]$ForceMode, [switch]$SimulateMode)
    
    Write-CleanupLog "Starte umfassende Port-Bereinigung für Ports: $($TargetPorts -join ', ')" "INFO"
    
    $totalKilled = 0
    $meFeedKilled = 0
    $otherKilled = 0
    
    foreach ($port in $TargetPorts) {
        Write-CleanupLog "Analysiere Port $port..." "INFO"
        
        $processes = Get-PortProcessInfo -Port $port
        
        if (-not $processes -or $processes.Count -eq 0) {
            Write-CleanupLog "Port $port ist frei" "SUCCESS"
            continue
        }
        
        Write-CleanupLog "Gefunden $($processes.Count) Prozess(e) auf Port $port" "WARN"
        
        foreach ($process in $processes) {
            $isMeFeed = Test-IfMeFeedProcess -ProcessInfo $process
            
            if (-not $ForceMode -and -not $isMeFeed) {
                Write-CleanupLog "ÜBERSPRUNGEN: Nicht-MeFeed Prozess PID=$($process.PID), Name=$($process.ProcessName)" "WARN"
                continue
            }
            
            $killResult = Remove-PortProcess -ProcessInfo $process -SimulateMode:$SimulateMode
            
            if ($killResult) {
                $totalKilled++
                if ($isMeFeed) {
                    $meFeedKilled++
                    Write-CleanupLog "Me Feed Prozess eliminiert: PID=$($process.PID)" "SUCCESS"
                } else {
                    $otherKilled++
                    Write-CleanupLog "Fremder Prozess eliminiert: PID=$($process.PID)" "SUCCESS"
                }
            }
        }
    }
    
    # Final verification
    Start-Sleep -Seconds 3
    $remainingProcesses = 0
    
    foreach ($port in $TargetPorts) {
        $remaining = Get-PortProcessInfo -Port $port
        if ($remaining) {
            $remainingProcesses += $remaining.Count
            Write-CleanupLog "WARNUNG: Port $port immer noch belegt von $($remaining.Count) Prozess(en)" "WARN"
        }
    }
    
    Write-CleanupLog "Bereinigung abgeschlossen:" "INFO"
    Write-CleanupLog "  Getötet gesamt: $totalKilled Prozesse" "INFO"
    Write-CleanupLog "  Davon Me Feed: $meFeedKilled Prozesse" "INFO"
    Write-CleanupLog "  Fremdprozesse: $otherKilled Prozesse" "INFO"
    Write-CleanupLog "  Noch belegt: $remainingProcesses Prozesse" "INFO"
    
    return @{
        TotalKilled = $totalKilled
        MeFeedKilled = $meFeedKilled
        OtherKilled = $otherKilled
        Remaining = $remainingProcesses
        Success = $remainingProcesses -eq 0
    }
}

# Hauptausführung
Write-CleanupLog "Port-Bereinigungssystem wird initialisiert..." "INFO"
Write-CleanupLog "Modus: $(if ($Simulate) { 'SIMULATION' } elseif ($Force) { 'ERZWUNGEN' } else { 'SICHER (nur Me Feed Prozesse)' })" "INFO"

$result = Clear-PortsComprehensive -TargetPorts $Ports -ForceMode:$Force -SimulateMode:$Simulate

if ($result.Success) {
    Write-CleanupLog "Alle Ziel-Ports erfolgreich bereinigt!" "SUCCESS"
    exit 0
} else {
    Write-CleanupLog "Einige Ports bleiben belegt - möglicherweise Requires ('Force' Parameter)" "WARN"
    exit 1
}

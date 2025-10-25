#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test script to verify both frontend and backend are running

.DESCRIPTION
    Simple health check script to verify both services are accessible
    after startup. Can be used for automated testing.
#>

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Me Feed - Startup Verification" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

$backendHealthy = $false
$frontendRunning = $false

# Test Backend
Write-Host "[1/2] Testing Backend Health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✓ Backend is healthy" -ForegroundColor Green
        $backendHealthy = $true
        
        # Parse response for details
        try {
            $healthData = $response.Content | ConvertFrom-Json
            Write-Host "    Service: $($healthData.service)" -ForegroundColor Gray
            Write-Host "    Version: $($healthData.version)" -ForegroundColor Gray
            Write-Host "    Status:  $($healthData.status)" -ForegroundColor Gray
        } catch {
            Write-Host "    Response: $($response.Content)" -ForegroundColor Gray
        }
    } else {
        Write-Warning "  ✗ Backend returned status $($response.StatusCode)"
    }
} catch {
    Write-Warning "  ✗ Backend not accessible: $($_.Exception.Message)"
}

Write-Host ""

# Test Frontend
Write-Host "[2/2] Testing Frontend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri http://localhost:3000 -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✓ Frontend is running" -ForegroundColor Green
        $frontendRunning = $true
        
        if ($response.Content -match "Me Feed") {
            Write-Host "    ✓ Application title detected" -ForegroundColor Gray
        }
    } else {
        Write-Warning "  ✗ Frontend returned status $($response.StatusCode)"
    }
} catch {
    Write-Warning "  ✗ Frontend not accessible: $($_.Exception.Message)"
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "VERIFICATION SUMMARY" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

if ($backendHealthy -and $frontendRunning) {
    Write-Host "ALL SYSTEMS OPERATIONAL" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access URLs:" -ForegroundColor White
    Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Green
    Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Green
    Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Green
    exit 0
} else {
    Write-Host "SOME SERVICES HAVE ISSUES" -ForegroundColor Red
    Write-Host ""
    Write-Host "Status:" -ForegroundColor White
    if ($backendHealthy) {
        Write-Host "  Backend:  Running" -ForegroundColor Green
    } else {
        Write-Host "  Backend:  Not responding" -ForegroundColor Red
    }
    if ($frontendRunning) {
        Write-Host "  Frontend: Running" -ForegroundColor Green
    } else {
        Write-Host "  Frontend: Not responding" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  - Ensure both services were started with .\start-all.ps1" -ForegroundColor Gray
    Write-Host "  - Check for port conflicts (8000, 3000)" -ForegroundColor Gray
    Write-Host "  - Verify PostgreSQL and Redis are running" -ForegroundColor Gray
    exit 1
}

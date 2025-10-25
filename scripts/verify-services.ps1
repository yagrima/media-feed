#!/usr/bin/env pwsh
# Simple verification script for Me Feed services

Write-Host "Me Feed - Service Verification" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

$backendOK = $false
$frontendOK = $false

# Test Backend
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "Backend: HEALTHY" -ForegroundColor Green
        $backendOK = $true
    }
} catch {
    Write-Host "Backend: NOT RESPONDING" -ForegroundColor Red
}

# Test Frontend  
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:3000" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "Frontend: RUNNING" -ForegroundColor Green
        $frontendOK = $true
    }
} catch {
    Write-Host "Frontend: NOT RESPONDING" -ForegroundColor Red
}

Write-Host "================================" -ForegroundColor Cyan

if ($backendOK -and $frontendOK) {
    Write-Host "ALL SYSTEMS OPERATIONAL" -ForegroundColor Green
    Write-Host ""
    Write-Host "Frontend: http://localhost:3000"
    Write-Host "Backend:  http://localhost:8000"
    Write-Host "API Docs: http://localhost:8000/docs"
} else {
    Write-Host "ISSUES DETECTED" -ForegroundColor Red
    exit 1
}

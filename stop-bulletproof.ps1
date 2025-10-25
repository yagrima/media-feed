#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Bulletproof stop script for Me Feed application
.DESCRIPTION
    Safely stops all Me Feed services with proper cleanup
#>

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Stopping Me Feed Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Stop background jobs
Write-Host "Stopping background services..." -ForegroundColor Yellow
try {
    Stop-Job -Name "MeFeedBackend" -ErrorAction SilentlyContinue
    Stop-Job -Name "MeFeedFrontend" -ErrorAction SilentlyContinue
    Remove-Job -Name "MeFeedBackend" -ErrorAction SilentlyContinue
    Remove-Job -Name "MeFeedFrontend" -ErrorAction SilentlyContinue
    Write-Host "Background jobs stopped." -ForegroundColor Green
} catch {
    Write-Host "No background jobs to stop." -ForegroundColor Gray
}

# Stop Docker services (preserve data)
Write-Host "Stopping Docker services (preserving data)..." -ForegroundColor Yellow
try {
    docker-compose down 2>$null
    # NEVER use -v flag to preserve database data
    Write-Host "Docker services stopped. Database data preserved." -ForegroundColor Green
} catch {
    Write-Host "Docker services may not be running." -ForegroundColor Gray
}

# Kill any stray processes
Write-Host "Cleaning up stray processes..." -ForegroundColor Yellow
try {
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "Process cleanup completed." -ForegroundColor Green
} catch {
    Write-Host "No stray processes found." -ForegroundColor Gray
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "All Me Feed services stopped!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

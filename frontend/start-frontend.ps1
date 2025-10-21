#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start the Me Feed frontend development server

.DESCRIPTION
    Starts the Next.js 14 frontend in development mode on port 3000.

.NOTES
    Prerequisites:
    - Node.js and npm installed
    - Dependencies installed (npm install)
    - Backend server running on http://localhost:8000
#>

# Set location to frontend directory
Set-Location $PSScriptRoot

# Check if node_modules exists
if (-not (Test-Path "./node_modules")) {
    Write-Warning "node_modules not found. Installing dependencies..."
    npm install --legacy-peer-deps
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install dependencies"
        exit 1
    }
}

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Starting Me Feed Frontend Server" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Frontend URL: http://localhost:3000" -ForegroundColor Green
Write-Host "Backend API:  http://localhost:8000" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Start Next.js development server
npm run dev

#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start all Me Feed services for development/testing

.DESCRIPTION
    Starts both backend and frontend servers in separate terminal windows.
    This is the single entry point for starting the entire application stack.

.NOTES
    Prerequisites:
    - PostgreSQL 18 running on localhost:5432
    - Docker Desktop (for Redis) - will be started automatically if not running
    - Python virtual environment set up in backend/venv
    - Node.js dependencies installed in frontend/node_modules

    Troubleshooting:
    - If you experience issues after making code changes, try a full server restart
    - Close the backend/frontend terminal windows and run this script again
    - Python's auto-reload may not always pick up all module changes

.EXAMPLE
    .\start-all.ps1
    Starts both backend and frontend servers in separate windows
#>

$ErrorActionPreference = "Stop"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Me Feed - Starting All Services" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "[1/5] Checking prerequisites..." -ForegroundColor Yellow

# Check if PostgreSQL is running
$env:PGPASSWORD = "Evangeline2019!"
try {
    $pgCheck = & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U mefeed_user -d mefeed -c "SELECT 1;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ PostgreSQL is running" -ForegroundColor Green
    } else {
        Write-Warning "  ✗ PostgreSQL connection failed"
        Write-Host "    Please ensure PostgreSQL is running on localhost:5432" -ForegroundColor Yellow
        Write-Host "    Database: mefeed, User: mefeed_user" -ForegroundColor Yellow
        $continue = Read-Host "Continue anyway? (y/N)"
        if ($continue -ne "y") {
            exit 1
        }
    }
} catch {
    Write-Warning "  ✗ Could not check PostgreSQL status"
}

# Check and start Redis via Docker
Write-Host "  Checking Redis..." -ForegroundColor Cyan
try {
    $dockerRunning = docker ps 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ℹ Starting Docker Desktop..." -ForegroundColor Yellow
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        Write-Host "  ⏳ Waiting 15 seconds for Docker to start..." -ForegroundColor Gray
        Start-Sleep -Seconds 15
    }

    # Check if Redis container exists
    $redisContainer = docker ps -a --filter "name=mefeed_redis_dev" --format "{{.Names}}" 2>&1
    if ($redisContainer -eq "mefeed_redis_dev") {
        # Check if it's running
        $redisStatus = docker ps --filter "name=mefeed_redis_dev" --format "{{.Names}}" 2>&1
        if ($redisStatus -ne "mefeed_redis_dev") {
            Write-Host "  ℹ Starting existing Redis container..." -ForegroundColor Yellow
            docker start mefeed_redis_dev | Out-Null
        }
        Write-Host "  ✓ Redis is running" -ForegroundColor Green
    } else {
        Write-Host "  ℹ Creating Redis container..." -ForegroundColor Yellow
        docker run -d --name mefeed_redis_dev -p 6379:6379 redis:7-alpine | Out-Null
        Start-Sleep -Seconds 2
        Write-Host "  ✓ Redis started" -ForegroundColor Green
    }
} catch {
    Write-Warning "  ✗ Could not start Redis via Docker"
    Write-Host "    Please ensure Docker Desktop is installed" -ForegroundColor Yellow
    Write-Host "    Or start Redis manually on localhost:6379" -ForegroundColor Yellow
}

# Check backend virtual environment
if (-not (Test-Path "./backend/venv/Scripts/python.exe")) {
    Write-Error "  ✗ Backend virtual environment not found at ./backend/venv"
    Write-Host "    Please run: cd backend && python -m venv venv && .\venv\Scripts\activate && pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}
Write-Host "  ✓ Backend virtual environment exists" -ForegroundColor Green

# Check frontend dependencies
if (-not (Test-Path "./frontend/node_modules")) {
    Write-Warning "  ✗ Frontend dependencies not installed"
    Write-Host "    Installing dependencies..." -ForegroundColor Yellow
    Set-Location "./frontend"
    npm install --legacy-peer-deps
    Set-Location ".."
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Frontend dependencies installed" -ForegroundColor Green
    } else {
        Write-Error "Failed to install frontend dependencies"
        exit 1
    }
} else {
    Write-Host "  ✓ Frontend dependencies installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/5] Ensuring Redis is running..." -ForegroundColor Yellow
Write-Host "  (Redis check already completed above)" -ForegroundColor Gray

Write-Host ""
Write-Host "[3/5] Starting backend server..." -ForegroundColor Yellow

# Start backend in new terminal
$backendScript = Join-Path $PSScriptRoot "backend\start-backend.ps1"
Start-Process pwsh -ArgumentList "-NoExit", "-File", "`"$backendScript`""
Write-Host "  ✓ Backend starting in new window" -ForegroundColor Green

# Wait a moment for backend to initialize
Write-Host "  ⏳ Waiting 3 seconds for backend to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "[4/5] Starting frontend server..." -ForegroundColor Yellow

# Start frontend in new terminal
$frontendScript = Join-Path $PSScriptRoot "frontend\start-frontend.ps1"
Start-Process pwsh -ArgumentList "-NoExit", "-File", "`"$frontendScript`""
Write-Host "  ✓ Frontend starting in new window" -ForegroundColor Green

Write-Host ""
Write-Host "[5/5] Services started!" -ForegroundColor Yellow
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "✓ All Services Started Successfully" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access the application at:" -ForegroundColor White
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor Green
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor Green
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "To stop the servers:" -ForegroundColor White
Write-Host "  - Close the backend and frontend terminal windows" -ForegroundColor Gray
Write-Host "  - Or press Ctrl+C in each window" -ForegroundColor Gray
Write-Host ""
Write-Host "Happy testing! 🚀" -ForegroundColor Cyan

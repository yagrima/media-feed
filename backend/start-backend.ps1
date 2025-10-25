#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start the Me Feed backend server for development/testing

.DESCRIPTION
    Starts the FastAPI backend with uvicorn in reload mode on port 8000.
    Sets required environment variables for local development.

.NOTES
    Prerequisites:
    - Python virtual environment activated or available at ./venv
    - PostgreSQL running on localhost:5432 with mefeed database
    - Redis running on localhost:6379
#>

# Set location to backend directory
Set-Location $PSScriptRoot

# Check if virtual environment exists
if (-not (Test-Path "./venv/Scripts/python.exe")) {
    Write-Error "Virtual environment not found at ./venv"
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Load configuration from JSON file
$configPath = Join-Path $PSScriptRoot "..\..\config\secrets.json"
$dbCredentials = $null
$redisCredentials = $null
$configData = $null

if (Test-Path $configPath) {
    try {
        $configData = Get-Content $configPath | ConvertFrom-Json
        $dbCredentials = $configData.database
        $redisCredentials = $configData.redis
        Write-Host "✓ Configuration loaded successfully from config/secrets.json" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to load configuration. Using environment variables."
    }
} else {
    Write-Warning "Configuration file not found at $configPath. Using environment variables."
}

# Set environment variables for local development
$env:DEBUG = "true"

# Configure database connection
if ($configData -and $configData.database) {
    $dbCreds = $configData.database
    $dbConnString = "postgresql+asyncpg://{0}:{1}@{2}:{3}/{4}" -f `
        $dbCreds.user, `
        $dbCreds.password, `
        $dbCreds.host, `
        $dbCreds.port, `
        $dbCreds.name
    $env:DATABASE_URL = $dbConnString
    Write-Host "  ✓ Database configuration loaded" -ForegroundColor Green
} elseif ($env:DATABASE_URL) {
    # Use existing environment variable
    Write-Host "  ✓ Using DATABASE_URL from environment" -ForegroundColor Green
} else {
    Write-Error "Database configuration required. Set DATABASE_URL environment variable or configure config/secrets.json"
    exit 1
}

# Configure Redis connection
if ($configData -and $configData.redis) {
    $redisCreds = $configData.redis
    if ($redisCreds.password) {
        $redisConnString = "redis://:{0}@{1}:{2}/{3}" -f `
            $redisCreds.password, `
            $redisCreds.host, `
            $redisCreds.port, `
            $redisCreds.db
    } else {
        $redisConnString = "redis://{0}:{1}/{2}" -f `
            $redisCreds.host, `
            $redisCreds.port, `
            $redisCreds.db
    }
    $env:REDIS_URL = $redisConnString
    Write-Host "  ✓ Redis configuration loaded" -ForegroundColor Green
} elseif ($env:REDIS_URL) {
    # Use existing environment variable
    Write-Host "  ✓ Using REDIS_URL from environment" -ForegroundColor Green
} else {
    $env:REDIS_URL = "redis://localhost:6379/0"
    Write-Host "  ✓ Using default Redis configuration" -ForegroundColor Yellow
}

# Configure SECRET_KEY
if ($configData -and $configData.security -and $configData.security.secret_key) {
    $env:SECRET_KEY = $configData.security.secret_key
    Write-Host "  ✓ Secret key loaded from configuration" -ForegroundColor Green
} elseif ($env:SECRET_KEY) {
    # Use existing environment variable
    Write-Host "  ✓ Using SECRET_KEY from environment" -ForegroundColor Green
} else {
    Write-Warning "SECRET_KEY not configured. Using default for development."
    $env:SECRET_KEY = "dev_secret_key_for_development_only_minimum_64_characters_long_string"
    Write-Host "  ⚠ Using development default (CHANGE IN PRODUCTION)" -ForegroundColor Yellow
}

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Starting Me Feed Backend Server" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Backend URL: http://localhost:8000" -ForegroundColor Green
Write-Host "API Docs:    http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Health:      http://localhost:8000/health" -ForegroundColor Green
Write-Host ""
Write-Host "Configuration:" -ForegroundColor White
Write-Host "  Database: PostgreSQL configured" -ForegroundColor Gray
Write-Host "  Redis:    Configured" -ForegroundColor Gray
Write-Host "  Debug:    $env:DEBUG" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Start uvicorn with auto-reload
& "./venv/Scripts/python.exe" -m uvicorn app.main:app --reload --port 8000

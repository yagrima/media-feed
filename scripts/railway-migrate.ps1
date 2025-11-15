# Railway Database Migration Script
# Run Alembic migrations against Railway database

Write-Host "Railway Database Migration" -ForegroundColor Cyan
Write-Host ""

# Check if railway CLI is available
if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Railway CLI not found. Install with: npm install -g @railway/cli" -ForegroundColor Red
    exit 1
}

# Get DATABASE_URL from Railway
Write-Host "Fetching DATABASE_URL from Railway..." -ForegroundColor Yellow
$databaseUrl = railway variables --service media-feed | Select-String "DATABASE_URL" | ForEach-Object { $_.ToString().Split('=', 2)[1].Trim() }

if (-not $databaseUrl) {
    Write-Host "ERROR: Could not fetch DATABASE_URL from Railway" -ForegroundColor Red
    Write-Host "Make sure you are linked to the correct project (railway link)" -ForegroundColor Yellow
    exit 1
}

Write-Host "DATABASE_URL found" -ForegroundColor Green
Write-Host ""

# Navigate to backend directory
$backendPath = Join-Path $PSScriptRoot "..\backend"
if (-not (Test-Path $backendPath)) {
    Write-Host "ERROR: Backend directory not found at $backendPath" -ForegroundColor Red
    exit 1
}

Set-Location $backendPath

# Check if venv exists
$venvPath = Join-Path $backendPath "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "ERROR: Virtual environment not found at $venvPath" -ForegroundColor Red
    Write-Host "Create it with: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Activate venv and run migrations
Write-Host "Running Alembic migrations..." -ForegroundColor Yellow
$env:DATABASE_URL = $databaseUrl

& "$venvPath\Scripts\python.exe" -m alembic upgrade head

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "SUCCESS: Database migrations completed!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "ERROR: Migration failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

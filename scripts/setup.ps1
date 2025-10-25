# Me Feed - Project Setup Script (PowerShell)
# Run this script to set up the development environment on Windows

$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Me Feed - Development Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "[1/7] Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion found" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check Docker
Write-Host ""
Write-Host "[2/7] Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✓ $dockerVersion found" -ForegroundColor Green
} catch {
    Write-Host "⚠ Docker not found. Install Docker to use docker-compose setup" -ForegroundColor Yellow
}

# Generate security keys
Write-Host ""
Write-Host "[3/7] Generating security keys..." -ForegroundColor Yellow
if (-Not (Test-Path "secrets")) {
    pip install cryptography | Out-Null
    python scripts/generate_keys.py
} else {
    Write-Host "⚠ secrets/ directory already exists. Skipping key generation." -ForegroundColor Yellow
    Write-Host "  Delete secrets/ and re-run if you need new keys." -ForegroundColor Yellow
}

# Create .env file
Write-Host ""
Write-Host "[4/7] Setting up environment file..." -ForegroundColor Yellow
if (-Not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"

    # Read generated secret key
    if (Test-Path "secrets/secret_key.txt") {
        $secretKey = Get-Content "secrets/secret_key.txt" -Raw
        $secretKey = $secretKey.Trim()

        # Replace SECRET_KEY in .env
        $envContent = Get-Content ".env"
        $envContent = $envContent -replace "SECRET_KEY=.*", "SECRET_KEY=$secretKey"
        $envContent | Set-Content ".env"

        Write-Host "✓ .env file created with generated SECRET_KEY" -ForegroundColor Green
    } else {
        Write-Host "✓ .env file created (manually update SECRET_KEY)" -ForegroundColor Green
    }
} else {
    Write-Host "⚠ .env file already exists. Keeping existing configuration." -ForegroundColor Yellow
}

# Create virtual environment
Write-Host ""
Write-Host "[5/7] Creating Python virtual environment..." -ForegroundColor Yellow
if (-Not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "⚠ venv/ already exists. Skipping." -ForegroundColor Yellow
}

# Install dependencies
Write-Host ""
Write-Host "[6/7] Installing Python dependencies..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip | Out-Null
Set-Location backend
pip install -r requirements.txt | Out-Null
Set-Location ..
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Start Docker services
Write-Host ""
Write-Host "[7/7] Starting Docker services..." -ForegroundColor Yellow
$response = Read-Host "Start PostgreSQL and Redis with Docker? (y/n)"
if ($response -eq "y" -or $response -eq "Y") {
    docker-compose up -d db redis
    Write-Host "✓ Database and Redis started" -ForegroundColor Green

    # Wait for services to be healthy
    Write-Host "  Waiting for services to be ready..." -ForegroundColor Gray
    Start-Sleep -Seconds 5

    # Run migrations
    Write-Host "  Running database migrations..." -ForegroundColor Gray
    Set-Location backend
    alembic upgrade head
    Set-Location ..
    Write-Host "✓ Migrations complete" -ForegroundColor Green
} else {
    Write-Host "⚠ Skipping Docker services. Start manually when ready." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Review .env file and update any settings"
Write-Host "  2. Activate virtual environment:"
Write-Host "     venv\Scripts\Activate.ps1  (PowerShell)"
Write-Host "     venv\Scripts\activate.bat  (CMD)"
Write-Host "  3. Start the backend:"
Write-Host "     cd backend"
Write-Host "     uvicorn app.main:app --reload"
Write-Host "  4. Access API docs at: http://localhost:8000/docs"
Write-Host ""
Write-Host "For Docker-based setup:"
Write-Host "  docker-compose up -d"
Write-Host ""

# Production Deployment Script for Me Feed (Windows PowerShell)
param(
    [switch]$SkipTests,
    [switch]$Force,
    [switch]$Help
)

if ($Help) {
    Write-Host "Me Feed Production Deployment Script"
    Write-Host "===================================="
    Write-Host "Usage: .\deploy-production.ps1 [options]"
    Write-Host "Options:"
    Write-Host "  -SkipTests   Skip production tests"
    Write-Host "  -Force       Force deployment even if services are running"
    Write-Host "  -Help        Show this help message"
    exit 0
}

# Error handling
$ErrorActionPreference = "Stop"

# Colors
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

# Check prerequisites
function Check-Prerequisites {
    Write-ColorOutput "📋 Checking prerequisites..." "Yellow"
    
    # Check Docker
    try {
        docker info > $null 2>&1
    } catch {
        Write-ColorOutput "❌ Docker is not running. Please start Docker Desktop first." "Red"
        exit 1
    }
    
    # Check secrets directory
    $secretsPath = "..\Media Feed Secrets"
    if (-not (Test-Path $secretsPath)) {
        Write-ColorOutput "❌ Secrets directory not found: $secretsPath" "Red"
        exit 1
    }
    
    # Check critical secret files
    $secretFiles = @("jwt_private.pem", "jwt_public.pem", "encryption.key", "db_password.txt")
    foreach ($file in $secretFiles) {
        $filePath = Join-Path $secretsPath "secrets\$file"
        if (-not (Test-Path $filePath)) {
            Write-ColorOutput "❌ Secret file missing: $file" "Red"
            exit 1
        }
    }
    
    Write-ColorOutput "✅ All prerequisites met" "Green"
}

# Backup current deployment
function Backup-CurrentDeployment {
    Write-ColorOutput "💾 Backing up current deployment..." "Yellow"
    
    try {
        $runningServices = docker ps --filter "name=mefeed" --quiet | Measure-Object
        if ($runningServices.Count -gt 0) {
            docker-compose -f docker-checks.yml down > $null 2>&1
            
            # Backup volumes
            $volumes = docker volume ls --filter "name=mefeed" --quiet
            foreach ($volume in $volumes) {
                $zipFile = "volume_$volume.zip"
                docker run --rm -v "$volume`:data -v "$(PWD):backup" alpine tar czf "backup/$zipFile" -C /data .
            }
            Write-ColorOutput "✅ Backup completed" "Green"
        } else {
            Write-ColorOutput "ℹ️  No running services to backup" "Yellow"
        }
    } catch {
        Write-ColorOutput "⚠️  Backup failed, continuing..." "Yellow"
    }
}

# Clean up old containers and images
function Invoke-Cleanup {
    Write-ColorOutput "🧹 Cleaning up old containers and images..." "Yellow"
    
    try {
        docker system prune -f > $null 2>&1
        docker volume prune -f > $null 2>&1
        Write-ColorOutput "✅ Cleanup completed" "Green"
    } catch {
        Write-ColorOutput "⚠️  Cleanup partially failed, continuing..." "Yellow"
    }
}

# Build and start services
function Deploy-Services {
    Write-ColorOutput "🔨 Building and starting services..." "Yellow"
    
    # Build backend
    Write-Host "Building backend image..."
    try {
        docker build -t yagrima/mefeed-backend:latest backend/ > $null 2>&1
    } catch {
        Write-ColorOutput "❌ Backend build failed" "Red"
        exit 1
    }
    
    # Build frontend
    Write-Host "Building frontend image..."
    try {
        docker build -t yagrima/mefeed-frontend:latest frontend/ > $null 2>&1
    } catch {
        Write-ColorOutput "❌ Frontend build failed" "Red"
        exit 1
    }
    
    # Start services
    Write-Host "Starting services..."
    try {
        docker-compose -f docker-checks.yml up -d > $null 2>&1
        Write-ColorOutput "✅ Services deployed successfully" "Green"
    } catch {
        Write-ColorOutput "❌ Service startup failed" "Red"
        exit 1
    }
}

# Wait for services to be healthy
function Wait-ForHealth {
    Write-ColorOutput "⏳ Waiting for services to become healthy..." "Yellow"
    
    # Database
    Write-Host -NoNewline "Database: "
    $dbReady = $false
    for ($i = 1; $i -le 12; $i++) {
        try {
            $result = docker exec mefeed_db_prod_check pg_isready -U mefeed_user 2>$null
            if ($result -match "accepting connections") {
                Write-ColorOutput "✅" "Green"
                $dbReady = $true
                break
            }
        } catch {}
        Write-Host -NoNewline "."
        Start-Sleep 5
    }
    if (-not $dbReady) {
        Write-ColorOutput "❌ Database failed to start" "Red"
        exit 1
    }
    
    # Redis
    Write-Host -NoNewline "Redis: "
    $redisReady = $false
    for ($i = 1; $i -le 6; $i++) {
        try {
            $result = docker exec mefeed_redis_prod_check redis-cli ping 2>$null
            if ($result -match "PONG") {
                Write-ColorOutput "✅" "Green"
                $redisReady = $true
                break
            }
        } catch {}
        Write-Host -NoNewline "."
        Start-Sleep 5
    }
    if (-not $redisReady) {
        Write-ColorOutput "❌ Redis failed to start" "Red"
        exit 1
    }
    
    # Backend
    Write-Host -NoNewline "Backend: "
    $backendReady = $false
    for ($i = 1; $i -le 24; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-ColorOutput "✅" "Green"
                $backendReady = $true
                break
            }
        } catch {}
        Write-Host -NoNewline "."
        Start-Sleep 5
    }
    if (-not $backendReady) {
        Write-ColorOutput "❌ Backend failed to start" "Red"
        exit 1
    }
    
    # Frontend
    Write-Host -NoNewline "Frontend: "
    $frontendReady = $false
    for ($i = 1; $i -le 12; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-ColorOutput "✅" "Green"
                $frontendReady = $true
                break
            }
        } catch {}
        Write-Host -NoNewline "."
        Start-Sleep 5
    }
    if (-not $frontendReady) {
        Write-ColorOutput "❌ Frontend failed to start" "Red"
        exit 1
    }
}

# Run production tests
function Invoke-Tests {
    if ($SkipTests) {
        Write-ColorOutput "⏭️  Skipping tests as requested" "Yellow"
        return
    }
    
    Write-ColorOutput "🧪 Running production tests..." "Yellow"
    
    try {
        python tests/integration/test_production_readiness.py
        Write-ColorOutput "✅ All tests passed" "Green"
    } catch {
        Write-ColorOutput "❌ Production tests failed" "Red"
        Write-Host $_.Exception.Message
        exit 1
    }
}

# Show final status
function Show-Status {
    Write-ColorOutput "🎉 Production deployment completed successfully!" "Green"
    Write-Host ""
    Write-Host "📊 Service Status:"
    Write-Host "=================================="
    docker-compose -f docker-checks.yml ps
    Write-Host ""
    Write-Host "🌐 Application URLs:"
    Write-Host "=================================="
    Write-Host "Frontend: http://localhost:3000"
    Write-Host "Backend API: http://localhost:8000"
    Write-Host "API Documentation: http://localhost:8000/docs"
    Write-Host "Health Check: http://localhost/health"
    Write-Host ""
    Write-Host "🔍 Monitoring Commands:"
    Write-Host "=================================="
    Write-Host "View logs: docker-compose -f docker-checks.yml logs -f [service]"
    Write-Host "Check status: docker-compose -f docker-checks.yml ps"
    Write-Host "Stop services: docker-compose -f docker-checks.yml down"
    Write-Host ""
    Write-ColorOutput "🚀 Your Me Feed application is now running in production mode!" "Green"
}

# Main deployment function
function Start-Deployment {
    Write-ColorOutput "🚀 Me Feed Production Deployment" "Cyan"
    Write-ColorOutput "==================================" "Cyan"
    
    Check-Prerequisites
    Backup-CurrentDeployment
    Invoke-Cleanup
    Deploy-Services
    Wait-ForHealth
    Invoke-Tests
    Show-Status
}

# Handle Ctrl+C gracefully
try {
    Start-Deployment
    Write-ColorOutput "✨ All done! Your Me Feed application is production-ready! ✨" "Green"
} catch {
    Write-ColorOutput "❌ Deployment interrupted or failed: $_" "Red"
    exit 1
}

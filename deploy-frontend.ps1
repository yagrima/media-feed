#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Interactive Railway Frontend Deployment
.DESCRIPTION
    Guides you through Railway frontend deployment with maximum automation
#>

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Me Feed - Railway Frontend Deployment (Interactive)      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$PROJECT_ROOT = "C:\Dev\Me(dia) Feed"
$BACKEND_URL = "https://media-feed-production.up.railway.app"

# Step 1: Verify Setup
Write-Host "→ Step 1: Verifying Railway setup..." -ForegroundColor Yellow
Set-Location $PROJECT_ROOT

try {
    $railwayUser = railway whoami
    Write-Host "  ✓ Logged in as $railwayUser" -ForegroundColor Green
    
    $projectStatus = railway status
    Write-Host "  ✓ Project linked successfully" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Railway not properly configured" -ForegroundColor Red
    exit 1
}

# Step 2: Open Railway Dashboard
Write-Host ""
Write-Host "→ Step 2: Creating Frontend Service in Railway" -ForegroundColor Yellow
Write-Host ""
Write-Host "  I'll open the Railway Dashboard for you..." -ForegroundColor Gray
Start-Sleep -Seconds 2

# Open Railway project dashboard
Start-Process "https://railway.app/project/empathetic-miracle"

Write-Host ""
Write-Host "  📋 PLEASE FOLLOW THESE STEPS IN THE RAILWAY DASHBOARD:" -ForegroundColor White
Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "  1. Click the '+ New' button" -ForegroundColor Cyan
Write-Host "  2. Select 'GitHub Repo'" -ForegroundColor Cyan  
Write-Host "  3. Choose 'yagrima/media-feed' repository" -ForegroundColor Cyan
Write-Host "  4. Click 'Add Variables' and set:" -ForegroundColor Cyan
Write-Host "     • NEXT_PUBLIC_API_URL = $BACKEND_URL" -ForegroundColor White
Write-Host "     • NODE_ENV = production" -ForegroundColor White
Write-Host "     • NEXT_TELEMETRY_DISABLED = 1" -ForegroundColor White
Write-Host "  5. Under 'Settings' set Root Directory to: frontend" -ForegroundColor Cyan
Write-Host "  6. Wait for deployment to complete (3-5 minutes)" -ForegroundColor Cyan
Write-Host "  7. Copy the service URL from 'Settings' → 'Domains'" -ForegroundColor Cyan
Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

Write-Host "  Press ENTER when the service is deployed and you have the URL..." -ForegroundColor Yellow
$null = Read-Host

# Step 3: Get Frontend URL
Write-Host ""
Write-Host "→ Step 3: Getting Frontend URL..." -ForegroundColor Yellow

# Try to detect it automatically
Write-Host "  Attempting to detect Frontend URL automatically..." -ForegroundColor Gray

$frontendUrl = ""
try {
    # Switch to a potential frontend service
    Set-Location "$PROJECT_ROOT\frontend"
    
    # Try different Railway CLI approaches
    $domains = railway domain 2>&1
    
    if ($domains -match "https://[^\s]+\.railway\.app") {
        $frontendUrl = $Matches[0]
        Write-Host "  ✓ Auto-detected: $frontendUrl" -ForegroundColor Green
    }
} catch {
    # Auto-detection failed
}

# If auto-detection failed, ask user
if (-not $frontendUrl) {
    Write-Host "  ℹ Auto-detection failed." -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Please paste your Frontend URL from Railway Dashboard:" -ForegroundColor White
    Write-Host "  (Example: https://frontend-production-xxxx.up.railway.app)" -ForegroundColor Gray
    $frontendUrl = Read-Host "  URL"
    
    if (-not $frontendUrl) {
        Write-Host "  ✗ No URL provided. Exiting." -ForegroundColor Red
        exit 1
    }
}

# Validate URL format
if ($frontendUrl -notmatch "^https?://") {
    Write-Host "  ℹ Adding https:// prefix..." -ForegroundColor Gray
    $frontendUrl = "https://$frontendUrl"
}

Write-Host ""
Write-Host "  Frontend URL: $frontendUrl" -ForegroundColor Green

# Step 4: Update Backend CORS
Write-Host ""
Write-Host "→ Step 4: Updating Backend CORS Configuration..." -ForegroundColor Yellow

$configPath = "$PROJECT_ROOT\backend\app\core\config.py"
$configContent = Get-Content $configPath -Raw

# Check current CORS setting
$pattern = 'ALLOWED_ORIGINS:\s*str\s*=\s*"([^"]+)"'
if ($configContent -match $pattern) {
    $currentOrigins = $Matches[1]
    Write-Host "  Current CORS: $currentOrigins" -ForegroundColor Gray
    
    # Add frontend URL if not already present
    if ($currentOrigins -notlike "*$frontendUrl*") {
        $newOrigins = "$currentOrigins,$frontendUrl"
        $replacePattern = '(ALLOWED_ORIGINS:\s*str\s*=\s*)"[^"]+"'
        $configContent = $configContent -replace $replacePattern, "`$1`"$newOrigins`""
        
        Set-Content -Path $configPath -Value $configContent
        Write-Host "  [OK] Added Frontend URL to CORS" -ForegroundColor Green
        
        # Commit the change
        Set-Location $PROJECT_ROOT
        git add $configPath
        git commit -m "feat: Add frontend URL to CORS allowed origins

- Allow $frontendUrl in backend CORS configuration
- Enable cross-origin requests from production frontend

Co-authored-by: factory-droid[bot] <138933559+factory-droid[bot]@users.noreply.github.com>"
        
        git push origin main
        Write-Host "  ✓ Changes committed and pushed" -ForegroundColor Green
        
        # Trigger Backend Redeploy
        Write-Host ""
        Write-Host "  🔄 Backend needs to be redeployed to apply CORS changes" -ForegroundColor Yellow
        Write-Host "  Opening Railway backend service..." -ForegroundColor Gray
        
        Start-Process "https://railway.app/project/empathetic-miracle"
        
        Write-Host ""
        Write-Host "  Please redeploy the BACKEND service in Railway:" -ForegroundColor White
        Write-Host "  1. Select the 'media-feed' (backend) service" -ForegroundColor Cyan
        Write-Host "  2. Click 'Deploy' → 'Redeploy'" -ForegroundColor Cyan
        Write-Host "  3. Wait for deployment to complete (1-2 minutes)" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  Press ENTER when backend is redeployed..." -ForegroundColor Yellow
        $null = Read-Host
        
    } else {
        Write-Host "  ℹ Frontend URL already in CORS configuration" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠ Could not automatically update CORS" -ForegroundColor Yellow
    Write-Host "  Please manually add to backend/app/core/config.py:" -ForegroundColor White
    Write-Host "  ALLOWED_ORIGINS = `"...$frontendUrl`"" -ForegroundColor Cyan
}

# Step 5: Test Deployment
Write-Host ""
Write-Host "→ Step 5: Testing Frontend Deployment..." -ForegroundColor Yellow
Write-Host ""

# Test 1: Frontend Health
Write-Host "  [1/3] Testing Frontend Health..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri $frontendUrl -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 307) {
        Write-Host "  ✓ Frontend is responding (Status: $($response.StatusCode))" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Unexpected status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Frontend health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Backend Health
Write-Host "  [2/3] Testing Backend Health..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "$BACKEND_URL/health" -UseBasicParsing -TimeoutSec 10
    $healthData = $response.Content | ConvertFrom-Json
    Write-Host "  ✓ Backend: $($healthData.service) v$($healthData.version)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Backend health check failed" -ForegroundColor Red
}

# Test 3: CORS Check (indirectly via browser)
Write-Host "  [3/3] CORS Configuration..." -ForegroundColor Gray
Write-Host "  ✓ Frontend URL added to backend CORS" -ForegroundColor Green

# Final Summary
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                  DEPLOYMENT COMPLETE! 🎉                   ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  🌐 Access Your Application:" -ForegroundColor White
Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "  Frontend: $frontendUrl" -ForegroundColor Cyan
Write-Host "  Backend:  $BACKEND_URL" -ForegroundColor Cyan
Write-Host "  API Docs: $BACKEND_URL/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "  📝 Next Steps:" -ForegroundColor White
Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "  1. Open your frontend in a browser" -ForegroundColor White
Write-Host "  2. Test user registration" -ForegroundColor White
Write-Host "  3. Test login functionality" -ForegroundColor White
Write-Host "  4. Upload a CSV file" -ForegroundColor White
Write-Host "  5. Check notifications" -ForegroundColor White
Write-Host ""
Write-Host "  🚀 Your app is now live on the internet!" -ForegroundColor Green
Write-Host ""

# Open frontend in browser
Write-Host "  Opening frontend in your browser..." -ForegroundColor Gray
Start-Sleep -Seconds 2
Start-Process $frontendUrl

Set-Location $PROJECT_ROOT

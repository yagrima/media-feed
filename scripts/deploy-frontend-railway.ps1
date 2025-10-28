#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy Me Feed Frontend to Railway
.DESCRIPTION
    Automated deployment script for Railway frontend service
#>

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Me Feed Frontend - Railway Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$PROJECT_ROOT = "C:\Dev\Me(dia) Feed"
$FRONTEND_DIR = "$PROJECT_ROOT\frontend"
$BACKEND_URL = "https://media-feed-production.up.railway.app"
$SERVICE_NAME = "frontend"

# Step 1: Verify Prerequisites
Write-Host "[1/6] Verifying prerequisites..." -ForegroundColor Yellow

# Check Railway CLI
try {
    $railwayVersion = railway --version
    Write-Host "  ✓ Railway CLI: $railwayVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Railway CLI not found" -ForegroundColor Red
    exit 1
}

# Check if logged in
try {
    $user = railway whoami
    Write-Host "  ✓ Logged in as: $user" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Not logged in to Railway" -ForegroundColor Red
    Write-Host "  Run: railway login" -ForegroundColor Yellow
    exit 1
}

# Check if in project
Set-Location $PROJECT_ROOT
try {
    $status = railway status
    Write-Host "  ✓ Project linked" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Project not linked" -ForegroundColor Red
    Write-Host "  Run: railway link" -ForegroundColor Yellow
    exit 1
}

# Step 2: Commit changes
Write-Host ""
Write-Host "[2/6] Committing configuration files..." -ForegroundColor Yellow

git add frontend/railway.json frontend/.env.production
$changes = git status --porcelain | Select-String "railway.json|.env.production"
if ($changes) {
    git commit -m "feat: Add Railway frontend deployment configuration

- Add railway.json for frontend service
- Add production environment variables template
- Configure Next.js standalone build for Railway"
    Write-Host "  ✓ Changes committed" -ForegroundColor Green
} else {
    Write-Host "  ℹ No changes to commit" -ForegroundColor Gray
}

# Step 3: Push to GitHub
Write-Host ""
Write-Host "[3/6] Pushing to GitHub..." -ForegroundColor Yellow

try {
    git push origin main
    Write-Host "  ✓ Pushed to GitHub" -ForegroundColor Green
} catch {
    Write-Host "  ℹ Already up to date" -ForegroundColor Gray
}

# Step 4: Manual Step - Create Service in Railway Dashboard
Write-Host ""
Write-Host "[4/6] Create Frontend Service in Railway Dashboard" -ForegroundColor Yellow
Write-Host "  ⚠️  This step requires manual action in Railway Dashboard" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Please follow these steps:" -ForegroundColor White
Write-Host "  1. Open: https://railway.app/project/empathetic-miracle" -ForegroundColor Cyan
Write-Host "  2. Click '+ New' → 'GitHub Repo'" -ForegroundColor Cyan
Write-Host "  3. Select 'yagrima/media-feed' repository" -ForegroundColor Cyan
Write-Host "  4. Set Root Directory: 'frontend'" -ForegroundColor Cyan
Write-Host "  5. Railway will auto-detect Dockerfile and deploy" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Press Enter when service is created..." -ForegroundColor White
$null = Read-Host

# Step 5: Set Environment Variables
Write-Host ""
Write-Host "[5/6] Setting environment variables..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  In Railway Dashboard → Frontend Service → Variables, add:" -ForegroundColor White
Write-Host ""
Write-Host "  NEXT_PUBLIC_API_URL=$BACKEND_URL" -ForegroundColor Cyan
Write-Host "  NODE_ENV=production" -ForegroundColor Cyan
Write-Host "  NEXT_TELEMETRY_DISABLED=1" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Press Enter when variables are set..." -ForegroundColor White
$null = Read-Host

# Step 6: Wait for deployment
Write-Host ""
Write-Host "[6/6] Waiting for deployment to complete..." -ForegroundColor Yellow
Write-Host "  Check Railway Dashboard for deployment progress" -ForegroundColor Gray
Write-Host "  This usually takes 3-5 minutes" -ForegroundColor Gray
Write-Host ""
Write-Host "  Press Enter when deployment is complete..." -ForegroundColor White
$null = Read-Host

# Step 7: Get Frontend URL
Write-Host ""
Write-Host "Getting frontend URL..." -ForegroundColor Yellow

# Try to get domain from Railway (this might not work for new service immediately)
try {
    Set-Location $FRONTEND_DIR
    $frontendUrl = railway domain 2>$null
    if ($frontendUrl) {
        Write-Host "  ✓ Frontend URL: $frontendUrl" -ForegroundColor Green
    }
} catch {
    Write-Host "  ℹ Get URL from Railway Dashboard → Frontend Service → Settings → Domains" -ForegroundColor Gray
}

# Step 8: Update Backend CORS
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps: Update Backend CORS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Note your frontend URL from Railway Dashboard" -ForegroundColor White
Write-Host "2. Add it to backend CORS configuration" -ForegroundColor White
Write-Host "3. Redeploy backend service" -ForegroundColor White
Write-Host ""
Write-Host "I can help you with that next!" -ForegroundColor Green
Write-Host ""

Set-Location $PROJECT_ROOT

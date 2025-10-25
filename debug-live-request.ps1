# Live Request Debugger
# Monitors backend logs while simulating browser request

Write-Host "=== MEDIA API LIVE DEBUGGER ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Start log monitoring in background
Write-Host "[1/4] Starting log monitor..." -ForegroundColor Yellow
$logJob = Start-Job -ScriptBlock {
    docker logs -f mefeed_backend 2>&1
}

Start-Sleep -Seconds 2

# Step 2: Get fresh auth token
Write-Host "[2/4] Attempting login to get fresh token..." -ForegroundColor Yellow

$loginBody = @{
    email = "rene.matis89@gmail.com"
    password = "test123"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/auth/login" `
        -Method POST `
        -Body $loginBody `
        -ContentType "application/json" `
        -UseBasicParsing
    
    $tokenData = $loginResponse.Content | ConvertFrom-Json
    $token = $tokenData.access_token
    
    if ($token) {
        Write-Host "  ✓ Token obtained: $($token.Substring(0,20))..." -ForegroundColor Green
    } else {
        Write-Host "  ✗ No token in response" -ForegroundColor Red
        $loginResponse.Content
        Stop-Job $logJob
        Remove-Job $logJob
        exit 1
    }
} catch {
    Write-Host "  ✗ Login failed: $($_.Exception.Message)" -ForegroundColor Red
    Stop-Job $logJob
    Remove-Job $logJob
    exit 1
}

# Step 3: Make the actual media request
Write-Host "[3/4] Making GET /api/media request..." -ForegroundColor Yellow
$apiUrl = 'http://localhost:8000/api/media?page=1&limit=20'
Write-Host "  URL: $apiUrl" -ForegroundColor Gray

Start-Sleep -Seconds 1

try {
    $headers = @{
        "Authorization" = "Bearer $token"
        "Origin" = "http://localhost:3000"
    }
    
    $response = Invoke-WebRequest -Uri $apiUrl `
        -Method GET `
        -Headers $headers `
        -UseBasicParsing
    
    Write-Host "  ✓ Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "  ✓ Content-Type: $($response.Headers['Content-Type'])" -ForegroundColor Green
    
    # Parse response
    $data = $response.Content | ConvertFrom-Json
    Write-Host "  ✓ Total items: $($data.total)" -ForegroundColor Green
    Write-Host "  ✓ Items returned: $($data.items.Count)" -ForegroundColor Green
    
    if ($data.items.Count -gt 0) {
        Write-Host "  ✓ Sample item: $($data.items[0].media.title)" -ForegroundColor Green
    }
    
} catch {
    Write-Host "  ✗ Request failed!" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        Write-Host "  Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    }
}

# Step 4: Get and display logs
Write-Host ""
Write-Host "[4/4] Backend logs from last 30 seconds:" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

Start-Sleep -Seconds 2
Stop-Job $logJob
$logs = Receive-Job $logJob
Remove-Job $logJob

# Filter and display relevant logs
$logs | Select-Object -Last 50 | Where-Object { 
    $_ -match "media|error|Error|Exception|Traceback|GET|POST" 
} | ForEach-Object {
    if ($_ -match "error|Error|Exception|Traceback") {
        Write-Host $_ -ForegroundColor Red
    } elseif ($_ -match "GET.*media") {
        Write-Host $_ -ForegroundColor Cyan
    } else {
        Write-Host $_ -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "=== DEBUG SESSION COMPLETE ===" -ForegroundColor Cyan

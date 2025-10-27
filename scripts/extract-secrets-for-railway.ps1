# Extract secrets for Railway deployment
# Converts local secret files to Railway-compatible environment variables

Write-Host "Extracting secrets for Railway deployment..." -ForegroundColor Cyan
Write-Host ""

$secretsDir = Join-Path $PSScriptRoot "..\..\Media Feed Secrets\secrets"

if (-not (Test-Path $secretsDir)) {
    Write-Host "ERROR: Secrets directory not found at: $secretsDir" -ForegroundColor Red
    Write-Host "Please ensure the Media Feed Secrets directory exists." -ForegroundColor Yellow
    exit 1
}

Write-Host "Reading secrets from: $secretsDir" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkGray
Write-Host "COPY THE FOLLOWING TO RAILWAY (Variable Name = Value)" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor DarkGray
Write-Host ""

# JWT Private Key
$privateKeyPath = Join-Path $secretsDir "jwt_private.pem"
if (Test-Path $privateKeyPath) {
    $privateKey = Get-Content $privateKeyPath -Raw
    # Convert newlines to \n for Railway
    $privateKeyEscaped = $privateKey -replace "`r`n", "`n" -replace "`n", "\n"
    Write-Host "JWT_PRIVATE_KEY=" -NoNewline -ForegroundColor Yellow
    Write-Host $privateKeyEscaped
    Write-Host ""
} else {
    Write-Host "WARNING: JWT Private Key not found" -ForegroundColor Red
}

# JWT Public Key
$publicKeyPath = Join-Path $secretsDir "jwt_public.pem"
if (Test-Path $publicKeyPath) {
    $publicKey = Get-Content $publicKeyPath -Raw
    $publicKeyEscaped = $publicKey -replace "`r`n", "`n" -replace "`n", "\n"
    Write-Host "JWT_PUBLIC_KEY=" -NoNewline -ForegroundColor Yellow
    Write-Host $publicKeyEscaped
    Write-Host ""
} else {
    Write-Host "WARNING: JWT Public Key not found" -ForegroundColor Red
}

# Encryption Key
$encKeyPath = Join-Path $secretsDir "encryption.key"
if (Test-Path $encKeyPath) {
    $encKey = Get-Content $encKeyPath -Raw
    $encKeyTrimmed = $encKey.Trim()
    Write-Host "ENCRYPTION_KEY=" -NoNewline -ForegroundColor Yellow
    Write-Host $encKeyTrimmed
    Write-Host ""
} else {
    Write-Host "WARNING: Encryption Key not found" -ForegroundColor Red
}

# Secret Key
$secretKeyPath = Join-Path $secretsDir "secret_key.txt"
if (Test-Path $secretKeyPath) {
    $secretKey = Get-Content $secretKeyPath -Raw
    $secretKeyTrimmed = $secretKey.Trim()
    Write-Host "SECRET_KEY=" -NoNewline -ForegroundColor Yellow
    Write-Host $secretKeyTrimmed
    Write-Host ""
} else {
    Write-Host "WARNING: Secret Key not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkGray
Write-Host "Extraction complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Copy the output above (without the === lines)" -ForegroundColor White
Write-Host "2. Save it in a temporary file for reference" -ForegroundColor White
Write-Host "3. Go to Railway Dashboard and paste each variable" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT: Never commit the temp file to Git!" -ForegroundColor Yellow
Write-Host ""

<#
.SYNOPSIS
    Setup production secrets for Me Feed
.DESCRIPTION
    Creates required production secrets that are NOT committed to Git.
.NOTES
    This script creates placeholders that must be filled with actual values.
    NEVER commit the actual secrets!
#>

Write-Host "Setting up Me Feed Production Secrets" -ForegroundColor Yellow

# Create secrets directory structure
$secretDirs = @(
    "secrets\prod",
    "secrets\certs",
    "logs",
    "logs\nginx"
)

foreach ($dir in $secretDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "Created: $dir" -ForegroundColor Green
    }
}

Write-Host "`n" -ForegroundColor Yellow

# Create placeholder files with instructions
$secrets = @(
    @{
        Name = "secrets\prod\db_name.txt"
        Content = "mefeed_prod"
        Description = "Production database name"
    },
    @{
        Name = "secrets\prod\db_user.txt" 
        Content = "mefeed_prod_user"
        Description = "Production database username"
    },
    @{
        Name = "secrets\prod\db_password.txt"
        Content = "CHANGE_ME_STRONG_DB_PASSWORD_32_CHARS_MIN"
        Description = "Production database password - SET REAL VALUE"
    },
    @{
        Name = "secrets\prod\redis_password.txt"
        Content = "CHANGE_ME_STRONG_REDIS_PASSWORD_48_CHARS"
        Description = "Production Redis password - SET REAL VALUE"
    },
    @{
        Name = "secrets\prod\secret_key.txt"
        Content = "CHANGE_ME_64_CHARACTER_SECRET_KEY"
        Description = "Flask/Django secret - SET REAL VALUE"
    },
    @{
        Name = "secrets\prod\smtp_host.txt"
        Content = "smtp.sendgrid.net"
        Description = "SMTP server host"
    },
    @{
        Name = "secrets\prod\smtp_user.txt"
        Content = "apikey"
        Description = "SMTP username"
    },
    @{
        Name = "secrets\prod\smtp_password.txt"
        Content = "CHANGE_ME_SENDGRID_API_KEY"
        Description = "SendGrid API key - SET REAL VALUE"
    },
    @{
        Name = "secrets\prod\rapiapi_key.txt"
        Content = "CHANGE_ME_RAPIDAPI_KEY"
        Description = "RapidAPI key - SET REAL VALUE"
    },
    @{
        Name = "secrets\prod\tmdb_api_key.txt"
        Content = "CHANGE_ME_TMDB_API_KEY"
        Description = "TMDB API key - SET REAL VALUE"
    },
    @{
        Name = "secrets\prod\grafana_password.txt"
        Content = "CHANGE_ME_GRAPHANA_ADMIN_PASSWORD"
        Description = "Grafana admin password - SET REAL VALUE"
    }
)

foreach ($secret in $secrets) {
    $fileExists = Test-Path $secret.Name
    if (-not $fileExists) {
        $secret.Content | Out-File -FilePath $secret.Name -Encoding UTF8
        Write-Host "Created: $($secret.Name)" -ForegroundColor Green
        Write-Host "    $($secret.Description)" -ForegroundColor Cyan
    } else {
        Write-Host "Skip: $($secret.Name) (already exists)" -ForegroundColor Gray
    }
}

Write-Host "`n" -ForegroundColor Yellow

# Create production environment setup script
$envScript = @"
# Production Environment Setup
# Source this file or export these variables before running docker-compose.prod-secure.yml

export RAPIDAPI_KEY=`cat secrets/prod/rapiapi_key.txt`
export TMDB_API_KEY=`cat secrets/prod/tmdb_api_key.txt`
export REDIS_PASSWORD=`cat secrets/prod/redis_password.txt`
export SMTP_HOST=`cat secrets/prod/smtp_host.txt`
export SMTP_USER=`cat secrets/prod/smtp_user.txt`
export SMTP_PASSWORD=`cat secrets/prod/smtp_password.txt`
export TAG=production

# For Grafana
export GRAFANA_ADMIN_PASSWORD=`cat secrets/prod/grafana_password.txt`

echo "Production environment variables set for Me Feed"
"@

$envScript | Out-File -FilePath "setup-prod-env.ps1" -Encoding UTF8
Write-Host "Created: setup-prod-env.ps1" -ForegroundColor Green

Write-Host "`n" -ForegroundColor Yellow

# Create README for production setup
$readme = @"
# Production Secrets Setup

## SECURITY WARNING ⚠️

NEVER commit actual secret values to Git!

## Quick Setup

1. Run the setup script:
   ```powershell
   .\scripts\setup-production-secrets.ps1
   ```

2. Fill in actual values in all files in `secrets/prod/` directory
   - db_password.txt: Strong database password
   - redis_password.txt: Strong Redis password  
   - secret_key.txt: Strong 64-character secret
   - smtp_password.txt: SendGrid API key
   - rapidapi_key.txt: RapidAPI key
   - tmdb_api_key.txt: TMDB API key
   - grafana_password.txt: Grafana admin password

3. Set environment before deployment:
   ```powershell
   .\setup-prod-env.ps1
   ```

4. Deploy using secure version:
   ```powershell
   docker-compose -f docker-compose.prod-secure.yml up -d
   ```

## Files Is Already Configured
- JWT keys: Already in `secrets/` directory (development keys)
- Encryption key: Already in `secrets/com` directory (development key)
- For production, these should be regenerated using `scripts/generate_keys_simple.py`

## Security Notes
- All production secrets are gitignored
- Use external secrets management in production
- Consider using HashiCorp Vault, AWS Secrets Manager, or similar
- Rotate keys regularly (recommended: 90 days)
"@

$readme | Out-File -FilePath "PRODUCTION_SECRETS.md" -Encoding UTF8
Write-Host "Created: PRODUCTION_SECRETS.md" -ForegroundColor Green

Write-Host "`n" -ForegroundColor Green
Write-Host "🔒 Production secrets setup complete!" -ForegroundColor Yellow
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Fill in actual values in secrets/prod/ files" -ForegroundColor White
Write-Host "2. Run setup-prod-env.ps1 before deployment" -ForegroundColor White
Write-Host "3. Use docker-compose.prod-secure.yml for production" -ForegroundColor White
Write-Host "`nNEVER commit actual secrets to Git!`n" -ForegroundColor Red

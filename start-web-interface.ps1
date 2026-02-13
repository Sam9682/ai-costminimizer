# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# CostMinimizer Web Interface Startup Script for Windows

Write-Host "🚀 Starting CostMinimizer Web Interface..." -ForegroundColor Green

# Check if .env file exists
if (-not (Test-Path .env)) {
    Write-Host "📝 Creating .env file with default values..." -ForegroundColor Yellow
    
    # Generate random secret key
    $secretKey = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    
    @"
HTTP_PORT=6000
HTTPS_PORT=6001
SECRET_KEY=$secretKey
USER_ID=1
"@ | Out-File -FilePath .env -Encoding ASCII
    
    Write-Host "✅ .env file created" -ForegroundColor Green
}

# Load environment variables
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
    }
}

$USER_ID = $env:USER_ID
$HTTP_PORT = $env:HTTP_PORT
$HTTPS_PORT = $env:HTTPS_PORT

# Check if SSL certificates exist
if (-not (Test-Path ssl\privkey.pem) -or -not (Test-Path ssl\fullchain.pem)) {
    Write-Host "🔐 Generating self-signed SSL certificates..." -ForegroundColor Yellow
    
    if (-not (Test-Path ssl)) {
        New-Item -ItemType Directory -Path ssl | Out-Null
    }
    
    # Check if OpenSSL is available
    $opensslPath = Get-Command openssl -ErrorAction SilentlyContinue
    if ($opensslPath) {
        & openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
            -keyout ssl\privkey.pem -out ssl\fullchain.pem `
            -subj "/C=US/ST=State/L=City/O=CostMinimizer/CN=localhost" 2>$null
        Write-Host "✅ SSL certificates generated" -ForegroundColor Green
    } else {
        Write-Host "⚠️  OpenSSL not found. Please install OpenSSL or manually create SSL certificates." -ForegroundColor Yellow
        Write-Host "   You can download OpenSSL from: https://slproweb.com/products/Win32OpenSSL.html" -ForegroundColor Yellow
    }
}

# Build and start services
Write-Host "🐳 Building and starting Docker containers..." -ForegroundColor Yellow
docker-compose up -d --build

# Wait for services to be ready
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check if services are running
$costminimizerRunning = docker ps | Select-String "ai-costminimizer-$USER_ID"
$nginxRunning = docker ps | Select-String "ai-costminimizer-nginx-$USER_ID"

if ($costminimizerRunning) {
    Write-Host "✅ CostMinimizer web service is running" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start CostMinimizer web service" -ForegroundColor Red
    docker-compose logs
    exit 1
}

if ($nginxRunning) {
    Write-Host "✅ Nginx proxy is running" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start Nginx proxy" -ForegroundColor Red
    docker-compose logs nginx
    exit 1
}

Write-Host ""
Write-Host "🎉 CostMinimizer Web Interface is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Access URLs:" -ForegroundColor Cyan
Write-Host "   HTTP:  http://localhost:$HTTP_PORT" -ForegroundColor White
Write-Host "   HTTPS: https://localhost:$HTTPS_PORT" -ForegroundColor White
Write-Host ""
Write-Host "📊 View logs:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f" -ForegroundColor White
Write-Host ""
Write-Host "🛑 Stop services:" -ForegroundColor Cyan
Write-Host "   docker-compose down" -ForegroundColor White
Write-Host ""

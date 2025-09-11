# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Start CostMinimizer MCP Server for Amazon Q integration

Write-Host "Starting CostMinimizer MCP Server..." -ForegroundColor Green
Write-Host ""

# Check and preserve AWS credentials
Write-Host "Checking AWS credentials..." -ForegroundColor Yellow

if ($env:AWS_ACCESS_KEY_ID) {
    Write-Host "AWS_ACCESS_KEY_ID found" -ForegroundColor Green
} else {
    Write-Host "! AWS_ACCESS_KEY_ID not set" -ForegroundColor Yellow
}

if ($env:AWS_SECRET_ACCESS_KEY) {
    Write-Host "AWS_SECRET_ACCESS_KEY found" -ForegroundColor Green
} else {
    Write-Host "! AWS_SECRET_ACCESS_KEY not set" -ForegroundColor Yellow
}

if ($env:AWS_SESSION_TOKEN) {
    Write-Host "AWS_SESSION_TOKEN found" -ForegroundColor Green
} else {
    Write-Host "! AWS_SESSION_TOKEN not set" -ForegroundColor Yellow
}

if ($env:AWS_DEFAULT_REGION) {
    Write-Host "AWS_DEFAULT_REGION: $($env:AWS_DEFAULT_REGION)" -ForegroundColor Green
} else {
    Write-Host "! AWS_DEFAULT_REGION not set" -ForegroundColor Yellow
}

if ($env:AWS_PROFILE) {
    Write-Host "AWS_PROFILE: $($env:AWS_PROFILE)" -ForegroundColor Green
} else {
    Write-Host "! AWS_PROFILE not set" -ForegroundColor Yellow
}

Write-Host ""

# Activate virtual environment if it exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    & ".venv\Scripts\Activate.ps1"
}

# Set Python path
$env:PYTHONPATH = "src;$($env:PYTHONPATH)"

# Start the MCP server
Write-Host "Starting MCP server with AWS credentials..." -ForegroundColor Green
python costminimizer-mcp-server.py

Read-Host "Press Enter to continue..."
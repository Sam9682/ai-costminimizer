@echo off
REM Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
REM SPDX-License-Identifier: Apache-2.0

REM Start CostMinimizer MCP Server for Amazon Q integration

echo Starting CostMinimizer MCP Server...
echo.

REM Check and preserve AWS credentials
echo Checking AWS credentials...
if defined AWS_ACCESS_KEY_ID (
    echo ✓ AWS_ACCESS_KEY_ID found
) else (
    echo ⚠ AWS_ACCESS_KEY_ID not set
)

if defined AWS_SECRET_ACCESS_KEY (
    echo ✓ AWS_SECRET_ACCESS_KEY found
) else (
    echo ⚠ AWS_SECRET_ACCESS_KEY not set
)

if defined AWS_SESSION_TOKEN (
    echo ✓ AWS_SESSION_TOKEN found
) else (
    echo ⚠ AWS_SESSION_TOKEN not set
)

if defined AWS_DEFAULT_REGION (
    echo ✓ AWS_DEFAULT_REGION: %AWS_DEFAULT_REGION%
) else (
    echo ⚠ AWS_DEFAULT_REGION not set
)

if defined AWS_PROFILE (
    echo ✓ AWS_PROFILE: %AWS_PROFILE%
) else (
    echo ⚠ AWS_PROFILE not set
)

echo.

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Set Python path
set PYTHONPATH=src;%PYTHONPATH%

REM Start the MCP server
echo Starting MCP server with AWS credentials...
python costminimizer-mcp-server.py

pause
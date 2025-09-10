@echo off
REM Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
REM SPDX-License-Identifier: Apache-2.0

REM Start CostMinimizer MCP Server for Amazon Q integration

echo Starting CostMinimizer MCP Server...
echo.

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Set Python path
set PYTHONPATH=src;%PYTHONPATH%

REM Start the MCP server
echo Starting MCP server...
python costminimizer-mcp-server.py

pause
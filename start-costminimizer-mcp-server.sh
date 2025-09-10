#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Start CostMinimizer MCP Server for Amazon Q integration

echo "Starting CostMinimizer MCP Server..."
echo

# Check and preserve AWS credentials
echo "Checking AWS credentials..."
if [ -n "$AWS_ACCESS_KEY_ID" ]; then
    echo "✓ AWS_ACCESS_KEY_ID found"
else
    echo "⚠ AWS_ACCESS_KEY_ID not set"
fi

if [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "✓ AWS_SECRET_ACCESS_KEY found"
else
    echo "⚠ AWS_SECRET_ACCESS_KEY not set"
fi

if [ -n "$AWS_SESSION_TOKEN" ]; then
    echo "✓ AWS_SESSION_TOKEN found"
else
    echo "⚠ AWS_SESSION_TOKEN not set"
fi

if [ -n "$AWS_DEFAULT_REGION" ]; then
    echo "✓ AWS_DEFAULT_REGION: $AWS_DEFAULT_REGION"
else
    echo "⚠ AWS_DEFAULT_REGION not set"
fi

if [ -n "$AWS_PROFILE" ]; then
    echo "✓ AWS_PROFILE: $AWS_PROFILE"
else
    echo "⚠ AWS_PROFILE not set"
fi

echo

# Activate virtual environment if it exists
if [ -f ".venvBash/bin/activate" ]; then
    echo "Activating virtual environment..."
    source .venvBash/bin/activate
fi

# Set Python path
export PYTHONPATH="src:$PYTHONPATH"

# Explicitly export AWS credentials to ensure they're available to child processes
export AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY
export AWS_SESSION_TOKEN
export AWS_DEFAULT_REGION
export AWS_REGION
export AWS_PROFILE

# Start the MCP server
echo "Starting MCP server with AWS credentials..."
python costminimizer-mcp-server.py

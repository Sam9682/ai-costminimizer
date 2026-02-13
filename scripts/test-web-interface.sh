#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Test script for CostMinimizer Web Interface

set -e

echo "🧪 Testing CostMinimizer Web Interface..."

# Check if services are running
if ! docker ps | grep -q "ai-costminimizer"; then
    echo "❌ CostMinimizer service is not running"
    echo "   Please run: ./start-web-interface.sh"
    exit 1
fi

# Test health endpoint
echo "📡 Testing health endpoint..."
HTTP_PORT=${HTTP_PORT:-6000}
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${HTTP_PORT}/health)

if [ "$RESPONSE" = "200" ]; then
    echo "✅ Health check passed (HTTP $RESPONSE)"
else
    echo "❌ Health check failed (HTTP $RESPONSE)"
    exit 1
fi

# Test main page
echo "📄 Testing main page..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${HTTP_PORT}/)

if [ "$RESPONSE" = "200" ]; then
    echo "✅ Main page accessible (HTTP $RESPONSE)"
else
    echo "❌ Main page not accessible (HTTP $RESPONSE)"
    exit 1
fi

# Test API endpoint
echo "🔌 Testing API endpoint..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${HTTP_PORT}/api/available-reports)

if [ "$RESPONSE" = "200" ]; then
    echo "✅ API endpoint working (HTTP $RESPONSE)"
else
    echo "❌ API endpoint failed (HTTP $RESPONSE)"
    exit 1
fi

echo ""
echo "🎉 All tests passed!"
echo ""
echo "📍 Web interface is available at:"
echo "   http://localhost:${HTTP_PORT}"
echo ""

#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# CostMinimizer Web Interface Startup Script

set -e

echo "🚀 Starting CostMinimizer Web Interface..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file with default values..."
    cat > .env << EOF
HTTP_PORT=6000
HTTPS_PORT=6001
SECRET_KEY=$(openssl rand -hex 32)
USER_ID=1
EOF
    echo "✅ .env file created"
fi

# Source environment variables
source .env

# Check if SSL certificates exist
if [ ! -f ssl/privkey.pem ] || [ ! -f ssl/fullchain.pem ]; then
    echo "🔐 Generating self-signed SSL certificates..."
    mkdir -p ssl
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/privkey.pem -out ssl/fullchain.pem \
        -subj "/C=US/ST=State/L=City/O=CostMinimizer/CN=localhost" \
        2>/dev/null
    echo "✅ SSL certificates generated"
fi

# Build and start services
echo "🐳 Building and starting Docker containers..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# Check if services are running
if docker ps | grep -q "ai-costminimizer-${USER_ID}"; then
    echo "✅ CostMinimizer web service is running"
else
    echo "❌ Failed to start CostMinimizer web service"
    docker-compose logs
    exit 1
fi

if docker ps | grep -q "ai-costminimizer-nginx-${USER_ID}"; then
    echo "✅ Nginx proxy is running"
else
    echo "❌ Failed to start Nginx proxy"
    docker-compose logs nginx
    exit 1
fi

echo ""
echo "🎉 CostMinimizer Web Interface is ready!"
echo ""
echo "📍 Access URLs:"
echo "   HTTP:  http://localhost:${HTTP_PORT}"
echo "   HTTPS: https://localhost:${HTTPS_PORT}"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""

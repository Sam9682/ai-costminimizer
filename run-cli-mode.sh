#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# CostMinimizer CLI Mode Runner
# This script runs CostMinimizer in CLI mode using Docker

set -e

echo "🚀 CostMinimizer CLI Mode"
echo ""

# Check if AWS credentials are set
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "❌ AWS credentials not found in environment variables"
    echo ""
    echo "Please set your AWS credentials:"
    echo "  export AWS_ACCESS_KEY_ID=your-access-key"
    echo "  export AWS_SECRET_ACCESS_KEY=your-secret-key"
    echo "  export AWS_SESSION_TOKEN=your-session-token  # Optional"
    echo ""
    echo "Or use AWS CLI profile:"
    echo "  aws configure"
    echo ""
    exit 1
fi

# Default values
REPORTS="--ce --ta --co"
REGION="us-east-1"
INTERACTIVE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --ce|--ta|--co|--cur)
            if [ "$REPORTS" = "--ce --ta --co" ]; then
                REPORTS="$1"
            else
                REPORTS="$REPORTS $1"
            fi
            shift
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --interactive|-i)
            INTERACTIVE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --ce              Generate Cost Explorer reports"
            echo "  --ta              Generate Trusted Advisor reports"
            echo "  --co              Generate Compute Optimizer reports"
            echo "  --cur             Generate Cost & Usage reports"
            echo "  --region REGION   AWS region (default: us-east-1)"
            echo "  --interactive     Run in interactive mode (bash shell)"
            echo "  --help            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --ce --ta                    # Generate CE and TA reports"
            echo "  $0 --co --region us-west-2      # Generate CO reports in us-west-2"
            echo "  $0 --interactive                # Open interactive shell"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build Docker image if it doesn't exist
if ! docker images | grep -q "costminimizer"; then
    echo "📦 Building Docker image..."
    docker build -t costminimizer .
    echo "✅ Docker image built"
    echo ""
fi

# Create cow directory if it doesn't exist
mkdir -p ~/cow

# Run Docker container
if [ "$INTERACTIVE" = true ]; then
    echo "🐳 Starting interactive shell..."
    echo ""
    docker run -it \
        -v $HOME/.aws:/root/.aws \
        -v $HOME/cow:/root/cow \
        -e AWS_ACCESS_KEY_ID \
        -e AWS_SECRET_ACCESS_KEY \
        -e AWS_SESSION_TOKEN \
        --entrypoint /bin/bash \
        costminimizer
else
    echo "🐳 Running CostMinimizer with options: $REPORTS --region $REGION"
    echo ""
    docker run -it \
        -v $HOME/.aws:/root/.aws \
        -v $HOME/cow:/root/cow \
        -e AWS_ACCESS_KEY_ID \
        -e AWS_SECRET_ACCESS_KEY \
        -e AWS_SESSION_TOKEN \
        --entrypoint CostMinimizer \
        costminimizer $REPORTS --region $REGION
fi

echo ""
echo "✅ Done! Reports saved to ~/cow/"
echo ""

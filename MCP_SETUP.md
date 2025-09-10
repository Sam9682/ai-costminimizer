# CostMinimizer MCP Integration Setup

This guide explains how to set up CostMinimizer as an MCP (Model Context Protocol) server for use with Amazon Q Chat.

## Prerequisites

1. CostMinimizer already installed and configured
2. AWS credentials configured
3. Python 3.8+ with MCP library

## Installation

1. **Install MCP dependencies:**
   ```bash
   cd ~/CostMinimizer
   source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
   pip install -r requirements.txt
   ```

2. **Reinstall CostMinimizer with MCP support:**
   ```bash
   python setup.py develop
   ```

## Configuration for Amazon Q

1. **Copy the MCP configuration to Amazon Q's config directory:**
   
   For Windows:
   ```powershell
   # Create Amazon Q MCP config directory if it doesn't exist
   mkdir $env:APPDATA\amazonq\mcp -Force
   
   # Copy the MCP configuration
   copy costminimizer-mcp-config.json $env:APPDATA\amazonq\mcp\costminimizer.json
   ```
   
   For macOS/Linux:
   ```bash
   # Create Amazon Q MCP config directory if it doesn't exist
   mkdir -p ~/.amazonq/mcp
   
   # Copy the MCP configuration
   cp costminimizer-mcp-config.json ~/.amazonq/mcp/costminimizer.json
   ```

2. **Update the configuration file with your actual path:**
   Edit the copied configuration file and update the `cwd` path to match your CostMinimizer installation directory.

## Usage with Amazon Q Chat

Once configured, you can use these commands in Amazon Q Chat:

### 1. Get Cost Optimization Recommendations
```
Generate AWS cost optimization recommendations using Cost Explorer and Trusted Advisor
```

### 2. Ask Cost Questions
```
Based on my AWS costs, what are the top 3 areas where I can save money?
```

### 3. Get Cost Summary
```
Show me a summary of my AWS costs and optimization opportunities
```

### 4. List Available Reports
```
What cost optimization reports are available in CostMinimizer?
```

## Available MCP Tools

- **get_cost_optimization_recommendations**: Generate comprehensive reports
- **ask_cost_question**: AI-powered cost analysis questions
- **get_cost_summary**: Quick cost overview
- **list_available_reports**: Show available report types

## Troubleshooting

1. **MCP Server not starting:**
   - Verify Python path in configuration
   - Check AWS credentials are configured
   - Ensure CostMinimizer is properly installed

2. **Permission errors:**
   - Ensure the MCP server has access to AWS credentials
   - Check file permissions on the CostMinimizer directory

3. **Report generation fails:**
   - Verify AWS permissions for Cost Explorer, Trusted Advisor, etc.
   - Check CostMinimizer configuration with `CostMinimizer --configure --ls-conf`

## Manual Testing

You can test the MCP server manually:

```bash
cd ~/CostMinimizer
python costminimizer-mcp-server.py
```

The server will start and wait for MCP protocol messages on stdin/stdout.
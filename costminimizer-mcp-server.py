#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
MCP Server entry point for CostMinimizer.
This script starts the MCP server that exposes CostMinimizer functionality.
"""

__author__ = "Samuel Lepetre"
__license__ = "Apache-2.0"

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Log AWS credentials status
logger = logging.getLogger(__name__)
aws_creds = {
    'AWS_ACCESS_KEY_ID': os.environ.get('AWS_ACCESS_KEY_ID'),
    'AWS_SECRET_ACCESS_KEY': os.environ.get('AWS_SECRET_ACCESS_KEY'),
    'AWS_SESSION_TOKEN': os.environ.get('AWS_SESSION_TOKEN'),
    'AWS_DEFAULT_REGION': os.environ.get('AWS_DEFAULT_REGION'),
    'AWS_PROFILE': os.environ.get('AWS_PROFILE')
}
logger.info(f"AWS credentials available: {[k for k, v in aws_creds.items() if v is not None]}")

from mcp.server import Server
from mcp.types import Tool, TextContent
from CostMinimizer.mcp.tools import CostMinimizerTools

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create MCP server
server = Server("costminimizer")
tools = CostMinimizerTools()

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="get_cost_optimization_recommendations",
            description="Generate comprehensive AWS cost optimization recommendations using multiple AWS services",
            inputSchema={
                "type": "object",
                "properties": {
                    "reports": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["ce", "ta", "co", "cur"]},
                        "description": "Report types: ce (Cost Explorer), ta (Trusted Advisor), co (Compute Optimizer), cur (Cost & Usage Report)",
                        "default": ["ce", "ta"]
                    },
                    "region": {
                        "type": "string",
                        "description": "AWS region for Compute Optimizer reports",
                        "default": "us-east-1"
                    }
                }
            }
        ),
        Tool(
            name="ask_cost_question",
            description="Ask AI-powered questions about AWS cost optimization using existing reports",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Your cost optimization question"
                    },
                    "report_file": {
                        "type": "string",
                        "description": "Path to existing CostMinimizer Excel report (optional)"
                    }
                },
                "required": ["question"]
            }
        ),
        Tool(
            name="get_cost_summary",
            description="Get a quick AWS cost summary and top optimization opportunities",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_available_reports",
            description="List all available cost optimization report types and their descriptions",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle MCP tool calls with extended timeout handling."""
    logger.info(f"Starting tool execution: {name}")
    try:
        if name == "get_cost_optimization_recommendations":
            reports = arguments.get("reports", ["ce", "ta"])
            region = arguments.get("region", "us-east-1")
            
            logger.info(f"Generating reports: {reports} in region: {region}")
            
            # Validate reports
            valid_reports = tools.validate_report_types(reports)
            if not valid_reports:
                return [TextContent(
                    type="text", 
                    text="Error: No valid report types specified. Available: ce, ta, co, cur"
                )]
            
            # Execute reports with progress logging
            logger.info(f"Executing reports: {valid_reports}")
            
            # Return immediate response for long-running operations
            if len(valid_reports) > 1 or 'cur' in valid_reports:
                return [TextContent(
                    type="text", 
                    text=f"🚀 Starting cost optimization analysis...\n\n"
                         f"📊 Reports to generate: {', '.join(valid_reports)}\n"
                         f"🌍 Region: {region}\n\n"
                         f"⏱️ This may take several minutes. Reports will be saved to your output folder.\n"
                         f"💡 Use 'ask_cost_question' after completion to analyze results."
                )]
            
            result = await asyncio.get_event_loop().run_in_executor(
                None, tools.execute_reports, valid_reports, region
            )
            
            if result["success"]:
                response = f"✅ Cost optimization analysis completed!\n\n"
                response += f"📊 Reports generated: {', '.join(result['reports_generated'])}\n"
                response += f"📁 Output location: {result['output_folder']}\n\n"
                response += "📋 Reports include:\n"
                
                available_reports = tools.get_available_reports()
                for report in result['reports_generated']:
                    response += f"• {report.upper()}: {available_reports[report]}\n"
                
                response += "\n💡 Next steps:\n"
                response += "• Review the generated Excel reports for detailed recommendations\n"
                response += "• Use 'ask_cost_question' to get AI insights about specific findings\n"
                response += "• Implement high-impact, low-effort recommendations first\n"
                
                return [TextContent(type="text", text=response)]
            else:
                return [TextContent(
                    type="text", 
                    text=f"❌ Error generating reports: {result['error']}"
                )]
        
        elif name == "ask_cost_question":
            question = arguments.get("question")
            report_file = arguments.get("report_file")
            
            logger.info(f"Processing question: {question[:50]}...")
            result = await asyncio.get_event_loop().run_in_executor(
                None, tools.ask_question, question, report_file
            )
            
            if result["success"]:
                response = f"❓ Question: {result['question']}\n\n"
                response += f"💬 Answer: {result['answer']}\n"
                if result.get("report_file"):
                    response += f"\n📄 Based on report: {result['report_file']}"
                return [TextContent(type="text", text=response)]
            else:
                return [TextContent(
                    type="text", 
                    text=f"❌ Error processing question: {result['error']}"
                )]
        
        elif name == "get_cost_summary":
            logger.info("Generating cost summary")
            result = await asyncio.get_event_loop().run_in_executor(
                None, tools.get_cost_summary
            )
            
            if result["success"]:
                response = f"📈 AWS Cost Summary\n\n"
                response += f"✅ {result['message']}\n\n"
                response += "🎯 Key Recommendations:\n"
                for rec in result['recommendations']:
                    response += f"• {rec}\n"
                
                if result.get("output_folder"):
                    response += f"\n📁 Detailed reports saved to: {result['output_folder']}"
                
                return [TextContent(type="text", text=response)]
            else:
                return [TextContent(
                    type="text", 
                    text=f"❌ Error generating cost summary: {result['error']}"
                )]
        
        elif name == "list_available_reports":
            available_reports = tools.get_available_reports()
            response = "📊 Available Cost Optimization Reports:\n\n"
            
            for code, description in available_reports.items():
                response += f"• **{code.upper()}**: {description}\n"
            
            response += "\n💡 Usage tip: Use 'get_cost_optimization_recommendations' with the report codes you want to generate."
            
            return [TextContent(type="text", text=response)]
        
        else:
            return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]
            
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return [TextContent(type="text", text=f"❌ Unexpected error: {str(e)}")]

def test_aws_credentials():
    """Test AWS credentials before starting server."""
    try:
        import boto3
        session = boto3.Session()
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        logger.info(f"AWS credentials verified - Account: {identity.get('Account')}")
        return True
    except Exception as e:
        logger.error(f"AWS credentials test failed: {e}")
        return False

async def main():
    """Main entry point for the MCP server."""
    from mcp.server.stdio import stdio_server
    
    logger.info("Starting CostMinimizer MCP Server...")
    
    # Test AWS credentials
    if not test_aws_credentials():
        logger.warning("AWS credentials not available - some functions may fail")
    
    async with stdio_server() as (read_stream, write_stream):
        # Run server with extended timeout handling
        await server.run(
            read_stream, 
            write_stream, 
            server.create_initialization_options(),
            raise_exceptions=False  # Don't raise exceptions that could cause timeouts
        )

if __name__ == "__main__":
    asyncio.run(main())
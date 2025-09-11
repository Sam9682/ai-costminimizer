#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
MCP Server entry point for CostMinimizer.
This script starts the MCP server that exposes CostMinimizer functionality.
"""

__author__ = "Samuel Lepetre"
__license__ = "Apache-2.0"

import argparse
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

# Global execution mode
execution_mode = "sync"  # Default to sync

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
                        "default": ["ce", "ta", "co", "cur"]
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
        ),
        Tool(
            name="get_cost_optimization_ce_recommendations",
            description="Generate CE (Cost Explorer) comprehensive reports",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "AWS region",
                        "default": "us-east-1"
                    }
                }
            }
        ),
        Tool(
            name="get_cost_optimization_co_recommendations",
            description="Generate CO (Compute Optimizer) comprehensive reports",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "AWS region for Compute Optimizer reports",
                        "default": "us-east-1"
                    }
                }
            }
        ),
        Tool(
            name="get_cost_optimization_ta_recommendations",
            description="Generate TA (Trusted Advisor) comprehensive reports",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "AWS region",
                        "default": "us-east-1"
                    }
                }
            }
        ),
        Tool(
            name="get_cost_optimization_cur_recommendations",
            description="Generate CUR (Cost & Usage Report) comprehensive reports",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "AWS region",
                        "default": "us-east-1"
                    }
                }
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle MCP tool calls with extended timeout handling."""
    logger.info(f"Starting tool execution: {name}")
    try:
        if name == "get_cost_optimization_recommendations":
            reports = arguments.get("reports", ["ce", "ta", "co", "cur"])
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
            
            # Execute based on mode
            if execution_mode == "async":
                # Return immediate response for async mode
                return [TextContent(
                    type="text", 
                    text=f"🚀 Starting cost optimization analysis (async mode)...\n\n"
                         f"📊 Reports to generate: {', '.join(valid_reports)}\n"
                         f"🌍 Region: {region}\n\n"
                         f"⏱️ This may take several minutes. Reports will be saved to your output folder.\n"
                         f"💡 Use 'ask_cost_question' after completion to analyze results."
                )]
            else:
                # Sync mode - wait for completion
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
            if execution_mode == "sync":
                result = await asyncio.get_event_loop().run_in_executor(
                    None, tools.ask_question, question, report_file
                )
            else:
                result = tools.ask_question(question, report_file)
            
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
            if execution_mode == "sync":
                result = await asyncio.get_event_loop().run_in_executor(
                    None, tools.get_cost_summary
                )
            else:
                result = tools.get_cost_summary()
            
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
        
        elif name == "get_cost_optimization_ce_recommendations":
            region = arguments.get("region", "us-east-1")
            if execution_mode == "sync":
                result = await asyncio.get_event_loop().run_in_executor(
                    None, tools.execute_reports, ["ce"], region
                )
            else:
                result = tools.execute_reports(["ce"], region)
            
            if result["success"]:
                response = f"✅ Cost Explorer analysis completed!\n\n"
                response += f"📊 Report generated: CE (Cost Explorer)\n"
                response += f"📁 Output location: {result['output_folder']}\n\n"
                response += "📋 Report includes:\n"
                response += "• Cost Explorer - Analyze spending patterns, trends, and Reserved Instance utilization\n"
                return [TextContent(type="text", text=response)]
            else:
                return [TextContent(type="text", text=f"❌ Error generating CE report: {result['error']}")]
        
        elif name == "get_cost_optimization_co_recommendations":
            region = arguments.get("region", "us-east-1")
            if execution_mode == "sync":
                result = await asyncio.get_event_loop().run_in_executor(
                    None, tools.execute_reports, ["co"], region
                )
            else:
                result = tools.execute_reports(["co"], region)
            
            if result["success"]:
                response = f"✅ Compute Optimizer analysis completed!\n\n"
                response += f"📊 Report generated: CO (Compute Optimizer)\n"
                response += f"📁 Output location: {result['output_folder']}\n\n"
                response += "📋 Report includes:\n"
                response += "• Compute Optimizer - Get rightsizing recommendations for EC2, EBS, Lambda\n"
                return [TextContent(type="text", text=response)]
            else:
                return [TextContent(type="text", text=f"❌ Error generating CO report: {result['error']}")]
        
        elif name == "get_cost_optimization_ta_recommendations":
            region = arguments.get("region", "us-east-1")
            if execution_mode == "sync":
                result = await asyncio.get_event_loop().run_in_executor(
                    None, tools.execute_reports, ["ta"], region
                )
            else:
                result = tools.execute_reports(["ta"], region)
            
            if result["success"]:
                response = f"✅ Trusted Advisor analysis completed!\n\n"
                response += f"📊 Report generated: TA (Trusted Advisor)\n"
                response += f"📁 Output location: {result['output_folder']}\n\n"
                response += "📋 Report includes:\n"
                response += "• Trusted Advisor - Get AWS best practice recommendations for cost optimization\n"
                return [TextContent(type="text", text=response)]
            else:
                return [TextContent(type="text", text=f"❌ Error generating TA report: {result['error']}")]
        
        elif name == "get_cost_optimization_cur_recommendations":
            region = arguments.get("region", "us-east-1")
            if execution_mode == "sync":
                result = await asyncio.get_event_loop().run_in_executor(
                    None, tools.execute_reports, ["cur"], region
                )
            else:
                result = tools.execute_reports(["cur"], region)
            
            if result["success"]:
                response = f"✅ Cost & Usage Report analysis completed!\n\n"
                response += f"📊 Report generated: CUR (Cost & Usage Report)\n"
                response += f"📁 Output location: {result['output_folder']}\n\n"
                response += "📋 Report includes:\n"
                response += "• Cost & Usage Report - Detailed billing analysis with custom queries\n"
                return [TextContent(type="text", text=response)]
            else:
                return [TextContent(type="text", text=f"❌ Error generating CUR report: {result['error']}")]
        
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

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="CostMinimizer MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    execution_group = parser.add_mutually_exclusive_group()
    execution_group.add_argument(
        "--async",
        action="store_true",
        help="Run in asynchronous mode (non-blocking operations)"
    )
    execution_group.add_argument(
        "--sync",
        action="store_true",
        default=True,
        help="Run in synchronous mode (blocking operations) - default"
    )
    
    return parser.parse_args()

async def main():
    """Main entry point for the MCP server."""
    global execution_mode
    from mcp.server.stdio import stdio_server
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Set execution mode
    if getattr(args, 'async', False):
        execution_mode = "async"
    else:
        execution_mode = "sync"
    
    logger.info(f"Starting CostMinimizer MCP Server in {execution_mode} mode...")
    
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
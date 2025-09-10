# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
MCP Server implementation for CostMinimizer.
Exposes cost optimization functionality through Model Context Protocol.
"""

__author__ = "Samuel Lepetre"
__license__ = "Apache-2.0"

import json
import logging
import os
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from ..CostMinimizer import App
from ..config.config import Config

class CostMinimizerMCPServer:
    """MCP Server for CostMinimizer cost optimization tools."""
    
    def __init__(self):
        self.server = Server("costminimizer")
        self.logger = logging.getLogger(__name__)
        self._preserve_aws_credentials()
        self._setup_tools()
    
    def _preserve_aws_credentials(self):
        """Preserve AWS credentials from environment variables."""
        self.aws_credentials = {
            'AWS_ACCESS_KEY_ID': os.environ.get('AWS_ACCESS_KEY_ID'),
            'AWS_SECRET_ACCESS_KEY': os.environ.get('AWS_SECRET_ACCESS_KEY'),
            'AWS_SESSION_TOKEN': os.environ.get('AWS_SESSION_TOKEN'),
            'AWS_DEFAULT_REGION': os.environ.get('AWS_DEFAULT_REGION'),
            'AWS_REGION': os.environ.get('AWS_REGION'),
            'AWS_PROFILE': os.environ.get('AWS_PROFILE')
        }
        # Filter out None values
        self.aws_credentials = {k: v for k, v in self.aws_credentials.items() if v is not None}
        self.logger.info(f"Preserved AWS credentials: {list(self.aws_credentials.keys())}")
        
    def _setup_tools(self):
        """Register MCP tools for cost optimization."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="get_cost_optimization_recommendations",
                    description="Get comprehensive AWS cost optimization recommendations using Cost Explorer, Trusted Advisor, and Compute Optimizer",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "reports": {
                                "type": "array",
                                "items": {"type": "string", "enum": ["ce", "ta", "co", "cur"]},
                                "description": "Report types to generate: ce (Cost Explorer), ta (Trusted Advisor), co (Compute Optimizer), cur (Cost & Usage Report)"
                            },
                            "region": {
                                "type": "string",
                                "description": "AWS region for Compute Optimizer reports",
                                "default": "us-east-1"
                            }
                        },
                        "required": ["reports"]
                    }
                ),
                Tool(
                    name="ask_cost_question",
                    description="Ask AI-powered questions about AWS cost optimization based on existing reports",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "Cost optimization question to ask"
                            },
                            "report_file": {
                                "type": "string",
                                "description": "Path to existing CostMinimizer report file (Excel format)"
                            }
                        },
                        "required": ["question"]
                    }
                ),
                Tool(
                    name="get_cost_summary",
                    description="Get a quick cost summary and top optimization opportunities",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "account_id": {
                                "type": "string",
                                "description": "AWS account ID (optional, uses current credentials if not provided)"
                            }
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "get_cost_optimization_recommendations":
                    return await self._get_cost_recommendations(arguments)
                elif name == "ask_cost_question":
                    return await self._ask_cost_question(arguments)
                elif name == "get_cost_summary":
                    return await self._get_cost_summary(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                self.logger.error(f"Error executing tool {name}: {str(e)}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _get_cost_recommendations(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Generate cost optimization recommendations."""
        reports = arguments.get("reports", ["ce"])
        region = arguments.get("region", "us-east-1")
        
        # Build command line arguments
        cmd_args = []
        if "ce" in reports:
            cmd_args.append("--ce")
        if "ta" in reports:
            cmd_args.append("--ta")
        if "co" in reports:
            cmd_args.append("--co")
        if "cur" in reports:
            cmd_args.append("--cur")
        
        cmd_args.extend(["--region", region])
        
        # Execute CostMinimizer with preserved AWS credentials
        import sys
        original_argv = sys.argv
        original_env = dict(os.environ)
        try:
            # Set AWS credentials in environment
            for key, value in self.aws_credentials.items():
                os.environ[key] = value
            
            sys.argv = ["CostMinimizer"] + cmd_args
            app = App(mode='module')
            result = app.main()
            
            # Get the output folder path from config
            config = Config()
            output_folder = config.get_output_folder() if hasattr(config, 'get_output_folder') else "~/cow"
            
            response = f"Cost optimization reports generated successfully.\n"
            response += f"Reports saved to: {output_folder}\n"
            response += f"Generated reports: {', '.join(reports)}\n"
            
            if result:
                response += f"Additional details: {result}"
            
            return [TextContent(type="text", text=response)]
            
        finally:
            sys.argv = original_argv
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
    
    async def _ask_cost_question(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Ask AI-powered cost optimization questions."""
        question = arguments.get("question")
        report_file = arguments.get("report_file")
        
        # Build command line arguments for question mode
        cmd_args = ["-q", question]
        if report_file:
            cmd_args.extend(["-f", report_file])
        
        # Execute CostMinimizer question command with preserved AWS credentials
        import sys
        original_argv = sys.argv
        original_env = dict(os.environ)
        try:
            # Set AWS credentials in environment
            for key, value in self.aws_credentials.items():
                os.environ[key] = value
            
            sys.argv = ["CostMinimizer"] + cmd_args
            app = App(mode='module')
            result = app.main()
            
            if result:
                return [TextContent(type="text", text=str(result))]
            else:
                return [TextContent(type="text", text="No answer generated. Please check if the report file exists and the question is valid.")]
                
        finally:
            sys.argv = original_argv
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
    
    async def _get_cost_summary(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get a quick cost summary."""
        # Generate a basic Cost Explorer report for summary
        import sys
        original_argv = sys.argv
        original_env = dict(os.environ)
        try:
            # Set AWS credentials in environment
            for key, value in self.aws_credentials.items():
                os.environ[key] = value
            
            sys.argv = ["CostMinimizer", "--ce", "--region", "us-east-1"]
            app = App(mode='module')
            result = app.main()
            
            response = "Cost summary generated using Cost Explorer data.\n"
            response += "Key areas to review:\n"
            response += "• Service costs and trends\n"
            response += "• Reserved Instance utilization\n"
            response += "• Regional cost distribution\n"
            response += "• Account-level spending\n\n"
            response += "Run 'get_cost_optimization_recommendations' with ['ce', 'ta', 'co'] for detailed analysis."
            
            return [TextContent(type="text", text=response)]
            
        finally:
            sys.argv = original_argv
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)

def main():
    """Main entry point for MCP server."""
    import asyncio
    
    server = CostMinimizerMCPServer()
    
    async def run_server():
        from mcp.server.stdio import stdio_server
        async with stdio_server() as (read_stream, write_stream):
            await server.server.run(read_stream, write_stream, server.server.create_initialization_options())
    
    asyncio.run(run_server())

if __name__ == "__main__":
    main()
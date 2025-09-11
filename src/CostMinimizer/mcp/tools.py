# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
MCP Tools for CostMinimizer.
Defines individual tools that can be called through the MCP protocol.
"""

__author__ = "Samuel Lepetre"
__license__ = "Apache-2.0"

import json
import os
from typing import Dict, Any, List, Optional
from ..CostMinimizer import App
from ..config.config import Config

class CostMinimizerTools:
    """Collection of MCP tools for cost optimization."""
    
    def __init__(self):
        self.config = Config()
        self._preserve_aws_credentials()
    
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
    
    def get_available_reports(self) -> Dict[str, str]:
        """Get list of available report types."""
        return {
            "ce": "Cost Explorer - Analyze spending patterns, trends, and Reserved Instance utilization",
            "ta": "Trusted Advisor - Get AWS best practice recommendations for cost optimization",
            "co": "Compute Optimizer - Get rightsizing recommendations for EC2, EBS, Lambda",
            "cur": "Cost & Usage Report - Detailed billing analysis with custom queries"
        }
    
    def validate_report_types(self, reports: List[str]) -> List[str]:
        """Validate and filter report types."""
        available = self.get_available_reports().keys()
        return [r for r in reports if r in available]
    
    def execute_reports(self, reports: List[str], region: str = "us-east-1") -> Dict[str, Any]:
        """Execute cost optimization reports."""
        import sys
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Build command arguments
        cmd_args = []
        for report in reports:
            cmd_args.append(f"--{report}")

        # Add following arguments : --checks ALL
        cmd_args.append("--checks")
        cmd_args.append("ALL")

        if "co" in reports:
            cmd_args.extend(["--region", region])
        
        # Log the arguments being passed to CostMinimizer
        logger.info(f"[MCP Module Mode] Launching CostMinimizer with arguments: {cmd_args}")
        
        # Execute CostMinimizer with preserved AWS credentials
        original_argv = sys.argv
        original_env = dict(os.environ)
        try:
            # Set AWS credentials in environment
            for key, value in self.aws_credentials.items():
                os.environ[key] = value
            
            sys.argv = ["CostMinimizer"] + cmd_args
            logger.info(f"[MCP Module Mode] sys.argv set to: {sys.argv}")
            app = App(mode='module')
            result = app.main()
            
            return {
                "success": True,
                "reports_generated": reports,
                "output_folder": self._get_output_folder(),
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "reports_requested": reports
            }
        finally:
            sys.argv = original_argv
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
    
    def ask_question(self, question: str, report_file: Optional[str] = None) -> Dict[str, Any]:
        """Ask AI-powered cost optimization question."""
        import sys
        import logging
        
        logger = logging.getLogger(__name__)
        
        cmd_args = ["-q", question]
        if report_file and os.path.exists(report_file):
            cmd_args.extend(["-f", report_file])
        
        # Log the arguments being passed to CostMinimizer
        logger.info(f"[MCP Module Mode] Launching CostMinimizer for question with arguments: {cmd_args}")
        
        original_argv = sys.argv
        original_env = dict(os.environ)
        try:
            # Set AWS credentials in environment
            for key, value in self.aws_credentials.items():
                os.environ[key] = value
            
            sys.argv = ["CostMinimizer"] + cmd_args
            logger.info(f"[MCP Module Mode] sys.argv set to: {sys.argv}")
            app = App(mode='module')
            result = app.main()
            
            return {
                "success": True,
                "question": question,
                "answer": result,
                "report_file": report_file
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "question": question
            }
        finally:
            sys.argv = original_argv
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get basic cost summary using Cost Explorer."""
        result = self.execute_reports(["ce"])
        
        if result["success"]:
            return {
                "success": True,
                "message": "Cost summary generated successfully",
                "recommendations": [
                    "Review service-level costs in the generated report",
                    "Check Reserved Instance utilization",
                    "Analyze regional cost distribution",
                    "Consider running Trusted Advisor for additional recommendations"
                ],
                "output_folder": result.get("output_folder")
            }
        else:
            return result
    
    def _get_output_folder(self) -> str:
        """Get the output folder path from configuration."""
        try:
            # This would need to be implemented based on the actual Config class
            return self.config.get_output_folder() if hasattr(self.config, 'get_output_folder') else "~/cow"
        except:
            return "~/cow"
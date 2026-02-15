# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Flask web application for CostMinimizer.
Provides web interface for AWS credentials input and cost optimization analysis.
"""

__author__ = "Samuel Lepetre"
__license__ = "Apache-2.0"

import os
import json
import logging
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from CostMinimizer.CostMinimizer import App

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-in-production-please')
CORS(app)

@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html')

@app.route('/api/validate-credentials', methods=['POST'])
def validate_credentials():
    """Validate AWS credentials."""
    try:
        data = request.json
        access_key = data.get('access_key')
        secret_key = data.get('secret_key')
        session_token = data.get('session_token', '')
        region = data.get('region', 'us-east-1')
        
        if not access_key or not secret_key:
            return jsonify({'success': False, 'error': 'Access key and secret key are required'}), 400
        
        # Test credentials
        session_obj = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token if session_token else None,
            region_name=region
        )
        
        sts = session_obj.client('sts')
        identity = sts.get_caller_identity()
        
        # Store credentials in session
        session['aws_credentials'] = {
            'AWS_ACCESS_KEY_ID': access_key,
            'AWS_SECRET_ACCESS_KEY': secret_key,
            'AWS_SESSION_TOKEN': session_token,
            'AWS_DEFAULT_REGION': region
        }
        
        return jsonify({
            'success': True,
            'account_id': identity.get('Account'),
            'user_arn': identity.get('Arn')
        })
        
    except NoCredentialsError:
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    except ClientError as e:
        return jsonify({'success': False, 'error': str(e)}), 401
    except Exception as e:
        logger.error(f"Error validating credentials: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/run-reports', methods=['POST'])
def run_reports():
    """Execute CostMinimizer reports."""
    try:
        data = request.json
        reports = data.get('reports', [])
        region = data.get('region', 'us-east-1')
        
        # Get credentials from session
        aws_creds = session.get('aws_credentials')
        if not aws_creds:
            return jsonify({'success': False, 'error': 'No credentials found. Please validate credentials first.'}), 401
        
        # Build command arguments
        cmd_args = []
        for report in reports:
            cmd_args.append(f"--{report}")
        
        # Add following arguments : --checks ALL
        cmd_args.append("--checks")
        cmd_args.append("ALL")
        
        # Add auto-update-conf to skip interactive prompts
        cmd_args.append("--auto-update-conf")
        
        if "co" in reports:
            cmd_args.extend(["--region", region])
        
        # Set environment variables and execute
        original_env = dict(os.environ)
        original_argv = sys.argv
        try:
            # Set AWS credentials in environment
            for key, value in aws_creds.items():
                if value:
                    os.environ[key] = value
            
            # Set non-interactive mode to prevent input() prompts
            os.environ['COSTMINIMIZER_NON_INTERACTIVE'] = '1'
            
            # Set sys.argv for argument parsing
            sys.argv = ["CostMinimizer"] + cmd_args
            logger.info(f"Launching CostMinimizer with arguments: {cmd_args}")
            
            # Initialize and run App directly
            cost_app = App(mode='module')
            result = cost_app.main()
            
            return jsonify({
                'success': True,
                'reports_generated': reports,
                'output_folder': '~/cow',
                'result': result
            })
            
        finally:
            # Restore environment and argv
            sys.argv = original_argv
            os.environ.clear()
            os.environ.update(original_env)
        
    except Exception as e:
        logger.error(f"Error running reports: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages for cost optimization questions."""
    try:
        data = request.json
        message = data.get('message')
        report_file = data.get('report_file')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        # Get credentials from session
        aws_creds = session.get('aws_credentials')
        if not aws_creds:
            return jsonify({'success': False, 'error': 'No credentials found. Please validate credentials first.'}), 401
        
        # Build command arguments
        cmd_args = ["-q", message]
        if report_file and os.path.exists(report_file):
            cmd_args.extend(["-f", report_file])
        
        # Set environment variables and execute
        original_env = dict(os.environ)
        original_argv = sys.argv
        try:
            # Set AWS credentials in environment
            for key, value in aws_creds.items():
                if value:
                    os.environ[key] = value
            
            # Set non-interactive mode to prevent input() prompts
            os.environ['COSTMINIMIZER_NON_INTERACTIVE'] = '1'
            
            # Set sys.argv for argument parsing
            sys.argv = ["CostMinimizer"] + cmd_args
            logger.info(f"Launching CostMinimizer for question with arguments: {cmd_args}")
            
            # Initialize and run App directly
            cost_app = App(mode='module')
            result = cost_app.main()
            
            return jsonify({
                'success': True,
                'question': message,
                'answer': result,
                'report_file': report_file
            })
            
        finally:
            # Restore environment and argv
            sys.argv = original_argv
            os.environ.clear()
            os.environ.update(original_env)
        
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/available-reports', methods=['GET'])
def available_reports():
    """Get list of available report types."""
    try:
        reports = {
            "ce": "Cost Explorer - Analyze spending patterns, trends, and Reserved Instance utilization",
            "ta": "Trusted Advisor - Get AWS best practice recommendations for cost optimization",
            "co": "Compute Optimizer - Get rightsizing recommendations for EC2, EBS, Lambda",
            "cur": "Cost & Usage Report - Detailed billing analysis with custom queries"
        }
        return jsonify({'success': True, 'reports': reports})
        
    except Exception as e:
        logger.error(f"Error getting available reports: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/docker-command', methods=['POST'])
def docker_command():
    """Generate Docker command for running CostMinimizer."""
    try:
        data = request.json
        reports = data.get('reports', [])
        region = data.get('region', 'us-east-1')
        
        # Build command
        report_flags = ' '.join([f'--{r}' for r in reports])
        
        command = f"""docker run -it \\
  -v $HOME/.aws:/root/.aws \\
  -v $HOME/cow:/root/cow \\
  -e AWS_ACCESS_KEY_ID \\
  -e AWS_SECRET_ACCESS_KEY \\
  -e AWS_SESSION_TOKEN \\
  costminimizer {report_flags} --region {region}"""
        
        return jsonify({'success': True, 'command': command})
        
    except Exception as e:
        logger.error(f"Error generating docker command: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)

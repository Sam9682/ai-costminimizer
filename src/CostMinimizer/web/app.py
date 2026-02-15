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
import re
import queue
import threading
from flask import Flask, render_template, request, jsonify, session, Response, send_file
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

# Store for SSE log streaming
log_queues = {}

class SSELogHandler(logging.Handler):
    """Custom log handler that sends logs to SSE queue."""
    def __init__(self, queue_id):
        super().__init__()
        self.queue_id = queue_id
        
    def emit(self, record):
        try:
            msg = self.format(record)
            if self.queue_id in log_queues:
                log_queues[self.queue_id].put(msg)
        except Exception:
            self.handleError(record)

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
        
        # Generate unique session ID for this report run
        import uuid
        session_id = str(uuid.uuid4())
        
        # Store session ID in session for later retrieval
        session['last_report_session'] = session_id
        
        # Start report generation in background thread
        thread = threading.Thread(
            target=execute_reports_background,
            args=(session_id, reports, region, aws_creds)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Report generation started'
        })
        
    except Exception as e:
        logger.error(f"Error running reports: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def execute_reports_background(session_id, reports, region, aws_creds):
    """Execute reports in background and stream logs."""
    import io
    import contextlib
    from rich.console import Console
    
    # Create queue for this session
    log_queues[session_id] = queue.Queue()
    
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
    
    # Log the command that will be executed
    log_queues[session_id].put(f"INFO - Building CostMinimizer command with reports: {reports}")
    log_queues[session_id].put(f"INFO - Command arguments: {cmd_args}")
    
    # Set environment variables and execute
    original_env = dict(os.environ)
    original_argv = sys.argv
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    # Setup custom log handler
    sse_handler = SSELogHandler(session_id)
    sse_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Get root logger and add our handler
    root_logger = logging.getLogger()
    original_level = root_logger.level
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(sse_handler)
    
    # Create custom stdout/stderr that also sends to queue
    class TeeOutput(io.StringIO):
        def __init__(self, queue_id, original_stream, prefix=""):
            super().__init__()
            self.queue_id = queue_id
            self.original_stream = original_stream
            self.prefix = prefix
            self.buffer = ""
            
        def write(self, text):
            if text and text.strip():
                # Write to original stream
                self.original_stream.write(text)
                self.original_stream.flush()
                
                # Send to queue - strip ANSI codes for cleaner display
                if self.queue_id in log_queues:
                    # Remove ANSI escape sequences
                    import re
                    clean_text = re.sub(r'\x1b\[[0-9;]*m', '', text)
                    lines = clean_text.split('\n')
                    for line in lines:
                        if line.strip():
                            log_queues[self.queue_id].put(f"{self.prefix}{line}")
            return len(text)
        
        def flush(self):
            self.original_stream.flush()
    
    excel_file_path = None
    
    try:
        # Set AWS credentials in environment
        for key, value in aws_creds.items():
            if value:
                os.environ[key] = value
        
        # Set non-interactive mode to prevent input() prompts
        os.environ['COSTMINIMIZER_NON_INTERACTIVE'] = '1'
        
        # Redirect stdout and stderr
        tee_stdout = TeeOutput(session_id, original_stdout, "")
        tee_stderr = TeeOutput(session_id, original_stderr, "ERROR: ")
        sys.stdout = tee_stdout
        sys.stderr = tee_stderr
        
        # Set sys.argv for argument parsing
        sys.argv = ["CostMinimizer"] + cmd_args
        log_queues[session_id].put(f"INFO - sys.argv set to: {sys.argv}")
        log_queues[session_id].put(f"INFO - Starting report generation...")
        log_queues[session_id].put(f"INFO - This may take several minutes depending on the reports selected...")
        
        # Initialize and run App directly
        cost_app = App(mode='module')
        result = cost_app.main()
        
        log_queues[session_id].put(f"SUCCESS - Reports generated successfully: {', '.join(reports)}")
        if excel_file_path:
            log_queues[session_id].put(f"EXCEL_FILE - {excel_file_path}")
        log_queues[session_id].put("DONE")
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        log_queues[session_id].put(f"ERROR - {str(e)}")
        # Send traceback line by line
        for line in error_details.split('\n'):
            if line.strip():
                log_queues[session_id].put(f"ERROR - {line}")
        log_queues[session_id].put("DONE")
    finally:
        # Restore stdout/stderr
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        
        # Restore environment and argv
        sys.argv = original_argv
        os.environ.clear()
        os.environ.update(original_env)
        
        # Remove custom handler
        root_logger.removeHandler(sse_handler)
        root_logger.setLevel(original_level)

def find_excel_file_in_logs(session_id):
    """Extract Excel file path from log messages."""
    # This is a placeholder - in reality, we'd need to capture this from the actual logs
    # For now, we'll return None and let the log message itself contain the path
    return None

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

@app.route('/api/stream-logs/<session_id>')
def stream_logs(session_id):
    """Stream logs via SSE."""
    def generate():
        if session_id not in log_queues:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Invalid session ID'})}\n\n"
            return
        
        log_queue = log_queues[session_id]
        excel_file = None
        
        while True:
            try:
                # Wait for log message with timeout
                msg = log_queue.get(timeout=30)
                
                if msg == "DONE":
                    # Send completion message
                    yield f"data: {json.dumps({'type': 'done', 'excel_file': excel_file})}\n\n"
                    break
                elif msg.startswith("EXCEL_FILE - "):
                    excel_file = msg.replace("EXCEL_FILE - ", "")
                    yield f"data: {json.dumps({'type': 'excel', 'path': excel_file})}\n\n"
                elif msg.startswith("ERROR - "):
                    error_msg = msg.replace("ERROR - ", "")
                    yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                elif msg.startswith("SUCCESS - "):
                    success_msg = msg.replace("SUCCESS - ", "")
                    yield f"data: {json.dumps({'type': 'success', 'message': success_msg})}\n\n"
                else:
                    # Regular log message
                    # Extract Excel file path if present
                    if "Excel Report Output saved into:" in msg:
                        match = re.search(r'Excel Report Output saved into:\s*(.+\.xlsx)', msg)
                        if match:
                            excel_file = match.group(1)
                    
                    yield f"data: {json.dumps({'type': 'log', 'message': msg})}\n\n"
                    
            except queue.Empty:
                # Send keepalive
                yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
                continue
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                break
        
        # Cleanup
        if session_id in log_queues:
            del log_queues[session_id]
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/download-report/<path:filepath>')
def download_report(filepath):
    """Download generated Excel report."""
    try:
        # Security: ensure the file is within allowed directories
        if not filepath.endswith('.xlsx'):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
        
        # Check if file exists
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test-sse')
def test_sse():
    """Test SSE endpoint to verify streaming works."""
    def generate():
        import time
        for i in range(10):
            yield f"data: {json.dumps({'type': 'log', 'message': f'Test message {i}'})}\n\n"
            time.sleep(0.5)
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)

# CostMinimizer Web Interface

## Overview

The CostMinimizer web interface provides an intuitive way to interact with AWS cost optimization tools through your browser. It eliminates the need for command-line operations and provides a chat-based AI assistant for cost analysis.

## Features

### 1. AWS Credentials Management
- Secure credential input form
- Support for temporary credentials (session tokens)
- Real-time credential validation
- Multi-region support

### 2. Cost Optimization Reports
Interactive selection of report types:
- **Cost Explorer (CE)**: Analyze spending patterns and trends
- **Trusted Advisor (TA)**: AWS best practice recommendations
- **Compute Optimizer (CO)**: EC2, EBS, Lambda rightsizing
- **Cost & Usage Report (CUR)**: Detailed billing analysis

### 3. AI Chat Assistant
- Natural language queries about AWS costs
- Context-aware responses based on generated reports
- Real-time cost optimization recommendations
- Interactive conversation interface

### 4. Docker Command Generator
- Automatically generates Docker commands based on selected options
- One-click copy to clipboard
- Supports all CostMinimizer CLI options

## Quick Start

### Option 1: Docker Compose (Recommended)

1. **Set environment variables** (create `.env` file):
```bash
HTTP_PORT=6000
HTTPS_PORT=6001
SECRET_KEY=your-secret-key-here
USER_ID=1
```

2. **Generate SSL certificates** (for HTTPS):
```bash
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/privkey.pem -out ssl/fullchain.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

3. **Create Docker network**:
```bash
docker network create costminimizer-network-1
```

4. **Start services**:
```bash
docker-compose up -d
```

5. **Access the web interface**:
- HTTP: http://localhost:6000
- HTTPS: https://localhost:6001

### Option 2: Standalone Docker

```bash
# Build the image
docker build -t costminimizer .

# Run the web interface
docker run -p 8000:8000 -v $HOME/cow:/root/cow costminimizer

# Access at http://localhost:8000
```

### Option 3: Local Development

```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .

# Set Flask app
export FLASK_APP=src/CostMinimizer/web/app.py
export SECRET_KEY=your-secret-key

# Run development server
flask run --host=0.0.0.0 --port=8000
```

## Usage Guide

### Step 1: Enter AWS Credentials

1. Navigate to the web interface
2. Fill in the credentials form:
   - **AWS Access Key ID** (required)
   - **AWS Secret Access Key** (required)
   - **AWS Session Token** (optional, for temporary credentials)
   - **AWS Region** (select from dropdown)
3. Click "Validate Credentials"
4. Wait for validation confirmation

### Step 2: Generate Reports

1. Select desired report types (CE, TA, CO, CUR)
2. Click "Generate Reports"
3. Wait for report generation (may take several minutes)
4. Reports are saved to `/root/cow` (or `$HOME/cow` if mounted)

### Step 3: Use AI Chat Assistant

Ask questions like:
- "What are my top 5 AWS services by cost?"
- "How can I reduce my EC2 costs?"
- "Show me Reserved Instance recommendations"
- "What cost anomalies do you see?"
- "Analyze my spending trends"

### Step 4: Use Docker Command (Optional)

1. Copy the generated Docker command
2. Run it in your terminal for CLI-based execution
3. Useful for automation and scripting

## API Endpoints

### POST /api/validate-credentials
Validate AWS credentials and establish session.

**Request:**
```json
{
  "access_key": "AKIAIOSFODNN7EXAMPLE",
  "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
  "session_token": "optional-session-token",
  "region": "us-east-1"
}
```

**Response:**
```json
{
  "success": true,
  "account_id": "123456789012",
  "user_arn": "arn:aws:iam::123456789012:user/username"
}
```

### POST /api/run-reports
Execute cost optimization reports.

**Request:**
```json
{
  "reports": ["ce", "ta", "co"],
  "region": "us-east-1"
}
```

**Response:**
```json
{
  "success": true,
  "reports_generated": ["ce", "ta", "co"],
  "output_folder": "/root/cow/123456789012/123456789012-2024-01-15-10-30"
}
```

### POST /api/chat
Send chat message to AI assistant.

**Request:**
```json
{
  "message": "What are my top cost optimization opportunities?",
  "report_file": "/path/to/report.xlsx"
}
```

**Response:**
```json
{
  "success": true,
  "question": "What are my top cost optimization opportunities?",
  "answer": "Based on the analysis..."
}
```

### GET /api/available-reports
Get list of available report types.

**Response:**
```json
{
  "success": true,
  "reports": {
    "ce": "Cost Explorer - Analyze spending patterns...",
    "ta": "Trusted Advisor - Get AWS best practices...",
    "co": "Compute Optimizer - Get rightsizing...",
    "cur": "Cost & Usage Report - Detailed billing..."
  }
}
```

## Security Considerations

### Credentials Storage
- Credentials are stored in Flask session (server-side)
- Session data is encrypted using SECRET_KEY
- Credentials are NOT persisted to disk
- Session expires when browser is closed

### HTTPS Configuration
- Always use HTTPS in production
- SSL certificates required for nginx
- Self-signed certificates OK for development
- Use Let's Encrypt for production

### Environment Variables
Required environment variables:
```bash
SECRET_KEY=your-strong-secret-key-here  # Change in production!
FLASK_ENV=production                     # Never use 'development' in prod
```

### IAM Permissions
The provided credentials need these permissions:
- `ce:GetCostAndUsage`
- `ce:GetReservation*`
- `support:DescribeTrustedAdvisor*`
- `compute-optimizer:Get*`
- `athena:*` (for CUR)
- `s3:GetObject`, `s3:ListBucket` (for CUR)
- `sts:GetCallerIdentity`
- `bedrock:Converse` (for AI chat)

## Troubleshooting

### Issue: "Unable to locate credentials"
**Solution:** Ensure credentials are validated before running reports or using chat.

### Issue: "Connection refused"
**Solution:** 
- Check if container is running: `docker ps`
- Check logs: `docker logs ai-costminimizer-0`
- Verify port mapping: `-p 8000:8000`

### Issue: "SSL certificate error"
**Solution:** 
- Generate SSL certificates (see Quick Start)
- Or use HTTP port instead of HTTPS

### Issue: "Reports taking too long"
**Solution:** 
- This is normal for comprehensive reports
- CE reports: 2-5 minutes
- TA reports: 1-3 minutes
- CO reports: 3-10 minutes (region-dependent)
- CUR reports: 5-15 minutes (data-dependent)

### Issue: "Chat not responding"
**Solution:**
- Ensure AWS Bedrock is enabled in your account
- Check IAM permissions for Bedrock
- Verify credentials have `bedrock:Converse` permission
- Check application logs for errors

## Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────┐
│    Nginx    │ (Port 443/6001)
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐
│    Flask    │ (Port 8000/6000)
│  Web App    │
└──────┬──────┘
       │
       ├─────────────┐
       │             │
       ▼             ▼
┌─────────────┐ ┌─────────────┐
│ CostMinimizer│ │  MCP Tools  │
│    Core     │ │   (Chat)    │
└──────┬──────┘ └──────┬──────┘
       │               │
       └───────┬───────┘
               ▼
        ┌─────────────┐
        │  AWS APIs   │
        │ CE/TA/CO/CUR│
        └─────────────┘
```

## Development

### Project Structure
```
src/CostMinimizer/web/
├── __init__.py
├── app.py                 # Flask application
├── templates/
│   └── index.html        # Main HTML template
└── static/
    ├── css/
    │   └── style.css     # Styles
    └── js/
        └── app.js        # Frontend JavaScript
```

### Adding New Features

1. **New API Endpoint:**
```python
@app.route('/api/new-feature', methods=['POST'])
def new_feature():
    # Implementation
    return jsonify({'success': True})
```

2. **New Frontend Component:**
```javascript
// In static/js/app.js
async function handleNewFeature() {
    const response = await fetch('/api/new-feature', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({data: 'value'})
    });
    const result = await response.json();
}
```

## Production Deployment

### Recommended Setup
1. Use a reverse proxy (nginx) with SSL
2. Set strong SECRET_KEY
3. Use environment variables for configuration
4. Enable logging and monitoring
5. Set up regular backups of report data
6. Use AWS IAM roles instead of access keys when possible

### Docker Compose Production
```yaml
services:
  ai-costminimizer:
    image: your-registry/costminimizer:latest
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - /data/cow:/root/cow
    restart: always
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/aws-samples/sample-costminimizer/issues
- Documentation: See README.md and MCP_SETUP.md

## License

Apache-2.0 License - See LICENSE file for details

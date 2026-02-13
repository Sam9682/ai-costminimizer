# CostMinimizer Web Interface

This directory contains the web interface for CostMinimizer, providing a user-friendly way to interact with AWS cost optimization tools.

## Directory Structure

```
web/
├── __init__.py              # Package initialization
├── app.py                   # Flask application (main entry point)
├── templates/
│   └── index.html          # Main HTML template
└── static/
    ├── css/
    │   └── style.css       # Stylesheet
    └── js/
        └── app.js          # Frontend JavaScript
```

## Components

### app.py - Flask Application

The main Flask application that provides:
- API endpoints for credential validation, report generation, and chat
- Session management for secure credential storage
- Integration with CostMinimizer core and MCP tools

**Key Endpoints:**
- `GET /` - Main web interface
- `POST /api/validate-credentials` - Validate AWS credentials
- `POST /api/run-reports` - Execute cost optimization reports
- `POST /api/chat` - AI-powered chat assistant
- `GET /api/available-reports` - List available report types
- `POST /api/docker-command` - Generate Docker commands
- `GET /health` - Health check

### templates/index.html - HTML Template

The main HTML template that provides:
- AWS credentials input form
- Interactive report selection (CE, TA, CO, CUR)
- AI chat interface
- Docker command generator
- Responsive layout

### static/css/style.css - Stylesheet

Modern, responsive styling with:
- AWS-themed color scheme
- Mobile-friendly design
- Interactive elements
- Loading indicators
- Status messages

### static/js/app.js - Frontend JavaScript

Client-side logic for:
- Form validation and submission
- API communication
- Real-time UI updates
- Chat message handling
- Docker command generation

## Running the Web Interface

### Option 1: Docker Compose (Recommended)
```bash
# From repository root
./start-web-interface.sh
```

### Option 2: Standalone Docker
```bash
# From repository root
docker build -t costminimizer .
docker run -p 8000:8000 costminimizer
```

### Option 3: Local Development
```bash
# From repository root
export FLASK_APP=src/CostMinimizer/web/app.py
export SECRET_KEY=$(openssl rand -hex 32)
flask run --host=0.0.0.0 --port=8000
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FLASK_APP` | Yes | - | Path to Flask app |
| `SECRET_KEY` | Yes | - | Session encryption key |
| `FLASK_ENV` | No | production | Flask environment |

## API Usage Examples

### Validate Credentials
```bash
curl -X POST http://localhost:8000/api/validate-credentials \
  -H "Content-Type: application/json" \
  -d '{
    "access_key": "AKIAIOSFODNN7EXAMPLE",
    "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    "session_token": "",
    "region": "us-east-1"
  }'
```

### Run Reports
```bash
curl -X POST http://localhost:8000/api/run-reports \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{
    "reports": ["ce", "ta", "co"],
    "region": "us-east-1"
  }'
```

### Chat with AI
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{
    "message": "What are my top 5 AWS services by cost?"
  }'
```

## Security Considerations

### Credential Storage
- Credentials stored in Flask session (server-side)
- Session data encrypted using SECRET_KEY
- Credentials never written to disk
- Session expires when browser closes

### HTTPS
- Always use HTTPS in production
- SSL certificates required for nginx
- Self-signed certificates OK for development

### Input Validation
- All user inputs validated
- AWS credentials tested with STS
- Error messages sanitized

## Development

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

3. **New HTML Section:**
```html
<!-- In templates/index.html -->
<section id="new-section" class="card">
    <h2>New Feature</h2>
    <!-- Content -->
</section>
```

### Testing

```bash
# Run Flask in debug mode
export FLASK_ENV=development
flask run --debug

# Test API endpoints
./test-web-interface.sh
```

## Troubleshooting

### Issue: "Unable to locate credentials"
**Solution:** Ensure credentials are validated before running reports or using chat.

### Issue: "Connection refused"
**Solution:** Check if Flask app is running on port 8000.

### Issue: "Session expired"
**Solution:** Re-validate credentials in the web interface.

## Documentation

For more information, see:
- [WEB_INTERFACE.md](../../../WEB_INTERFACE.md) - Complete web interface guide
- [DEPLOYMENT_GUIDE.md](../../../DEPLOYMENT_GUIDE.md) - Deployment instructions
- [QUICK_START.md](../../../QUICK_START.md) - Quick start guide

## License

Apache-2.0 License - See LICENSE file for details

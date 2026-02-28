# Technology Stack

## Language & Runtime

- Python 3.8+ (tested on 3.13)
- Type hints enabled (py.typed marker present)

## Core Dependencies

### AWS Integration
- boto3, botocore - AWS SDK for Python
- pyathena - AWS Athena query execution

### Data Processing
- pandas - Data manipulation and analysis
- openpyxl, xlsxwriter - Excel file generation
- python-pptx - PowerPoint generation
- sqlparse - SQL parsing and formatting

### Web & API
- flask, flask-cors - Web interface backend
- bottle - Lightweight WSGI framework
- mcp - Model Context Protocol server
- requests - HTTP client

### CLI & UI
- click - Command-line interface creation
- simple-term-menu - Interactive terminal menus (Linux/Mac only)
- pick - Alternative menu system
- rich - Terminal formatting and output
- colorama - Cross-platform colored terminal text
- tabulate - Table formatting

### Security & Configuration
- pycryptodome - Encryption operations
- PyYAML - YAML configuration parsing
- jsonpickle - JSON serialization

### Testing
- pytest, pytest-cov, pytest-mock - Testing framework
- mock - Mocking library

### Utilities
- backoff - Retry logic with exponential backoff
- python-dateutil - Date/time utilities

## Build System

- setuptools - Package distribution
- setup.py - Package configuration with console_scripts entry point

## Code Quality Tools

- black - Code formatter (line length: 100)
- isort - Import sorting (black-compatible profile)
- mypy - Static type checking (check_untyped_defs enabled)

## Database

- SQLite - Local configuration and metadata storage
- Schema managed via database.schema.sql

## Common Commands

### Installation
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -r requirements.txt

# Install in development mode
python setup.py develop
```

### Running the Tool
```bash
# CLI mode
CostMinimizer --ce --ta --co --cur

# Web interface
./scripts/start-web-interface.sh  # Linux/Mac
.\scripts\start-web-interface.ps1  # Windows

# MCP server
./scripts/start-costminimizer-mcp-server.sh
```

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src/CostMinimizer

# Run specific test module
python scripts/test_costminimizer_module.py
```

### Configuration
```bash
# Configure tool
CostMinimizer --configure

# Auto-update configuration
CostMinimizer --configure --auto-update-conf

# List current configuration
CostMinimizer --configure --ls-conf
```

### Docker
```bash
# Build image
docker build -t costminimizer .

# Run container
docker run -it -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
  -v ~/cow:/root/cow costminimizer:latest --ce
```

## Deployment Options

- Local installation (Python virtual environment)
- Docker container (with ECR support)
- Windows EC2 instance (CloudFormation template provided)
- AWS Lambda (infrastructure code included)

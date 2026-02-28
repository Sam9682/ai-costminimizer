# Project Structure

## Root Directory Layout

```
.
├── src/CostMinimizer/          # Main application source code
├── scripts/                    # Utility and deployment scripts
├── conf/                       # Deployment configuration (nginx, etc.)
├── shared/                     # Shared documentation and context files
├── requirements.txt            # Python dependencies
├── setup.py                    # Package installation configuration
├── pyproject.toml             # Tool configuration (black, isort, mypy)
├── Dockerfile                 # Container build definition
├── docker-compose.yml         # Multi-container orchestration
└── README.md                  # Main documentation
```

## Source Code Organization (src/CostMinimizer/)

### Entry Point
- `CostMinimizer.py` - Main application class and entry point
- `constants.py` - Global constants and configuration values
- `__init__.py` - Package initialization

### Core Modules

#### Command Layer
- `arguments/` - CLI argument parsing using argparse
- `commands/` - Command implementations using Factory pattern
  - `factory.py` - CommandFactory for creating command objects
  - `run_tooling.py` - Main report execution command
  - `configure_tooling.py` - Configuration management
  - `question.py` - AI-powered query handling
  - `available_reports.py` - Report listing
  - `version.py` - Version information

#### Configuration & Setup
- `config/` - Application configuration and database management
  - `config.py` - Main Config class (singleton pattern)
  - `database.py` - SQLite database operations
  - `database.schema.sql` - Database schema definition
  - `*.sql` - Pricing and conversion data SQL scripts
- `conf/` - YAML configuration files
  - `configuration_manager.py` - Configuration file handling
  - `cm_internals.yaml` - Internal settings
  - `tooling.yaml` - Tool-specific configuration
  - `logger.yaml` - Logging configuration

#### Report Generation
- `report_providers/` - Report generation by AWS service
  - `ce_reports/` - Cost Explorer reports
  - `ta_reports/` - Trusted Advisor reports
  - `co_reports/` - Compute Optimizer reports
  - `cur_reports/` - Cost & Usage Report (Athena-based)
  - `report_providers.py` - Base provider interface
- `report_controller/` - Report orchestration
  - `report_controller.py` - Main controller
  - `account_discovery_controller.py` - AWS account discovery
  - `region_discovery_controller.py` - Region enumeration
  - `resource_discovery_controller.py` - Resource scanning
- `report_output_handler/` - Output formatting
  - `report_output_handler.py` - Main output handler
  - `report_output_pptx.py` - PowerPoint generation
  - `report_output_gen_ai.py` - AI-powered analysis
- `report_request_parser/` - Request parsing and validation

#### AI Integration
- `genai_providers/` - GenAI provider abstraction
  - `genai_provider_client_base.py` - Base provider interface
  - `bedrock.py` - AWS Bedrock implementation
  - `genai_providers.py` - Provider factory

#### MCP Server
- `mcp/` - Model Context Protocol server
  - `server.py` - MCP server implementation
  - `tools.py` - Tool definitions for AI assistants

#### Web Interface
- `web/` - Flask-based web application
  - `app.py` - Flask application
  - `static/` - CSS, JavaScript, images
  - `templates/` - HTML templates

#### Security & Authentication
- `security/` - Authentication and encryption
  - `cow_authentication.py` - AWS credential management
  - `cow_encryption.py` - Data encryption utilities

#### Utilities
- `utils/` - Helper functions
  - `cow_validations.py` - Input validation
  - `system_validations.py` - System checks
  - `term_menu.py` - Terminal UI helpers
  - `yaml_loader.py` - YAML file loading
- `service_helpers/` - AWS service helpers
  - `ec2.py` - EC2 operations
  - `pricing.py` - Pricing API helpers
- `error/` - Error handling
  - `error.py` - Custom exceptions
  - `alerts.py` - Alert management
- `metrics/` - Performance metrics collection
- `patterns/` - Design pattern implementations
  - `singleton.py` - Singleton pattern
- `version/` - Version management

#### Configuration Import/Export
- `gexport_conf/` - Configuration export functionality
- `gimport_conf/` - Configuration import functionality

## Architecture Patterns

### Design Patterns Used
- **Factory Pattern**: CommandFactory creates command objects based on CLI arguments
- **Singleton Pattern**: Config class ensures single instance across application
- **Command Pattern**: Each CLI operation is encapsulated as a command object
- **Strategy Pattern**: Multiple report providers implement common interface

### Module Organization Principles
- Separation of concerns: CLI, business logic, data access, and output are distinct layers
- Provider pattern: Report generation abstracted by AWS service type
- Controller pattern: Report orchestration separated from generation
- Configuration centralization: All settings managed through Config singleton

### Key Conventions
- All modules include Apache 2.0 license headers
- Type hints used throughout (py.typed marker)
- Logging via Python logging module
- Error handling through custom exception classes
- AWS service interactions via boto3 clients

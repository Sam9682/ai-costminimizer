# CostMinimizer: AI-Powered AWS Cost Optimization Tool

CostMinimizer is a comprehensive AWS cost analysis and optimization tool that leverages AWS Cost Explorer, Trusted Advisor, Compute Optimizer and Cost & Usage Report to provide actionable insights for optimizing your AWS infrastructure costs. CostMinimizer also provide actionable cost-saving recommendations powered by AI. It helps AWS users identify cost optimization opportunities, analyze spending patterns, and generate detailed reports with specific recommendations.

The tool combines data from multiple AWS cost management services to provide a holistic view of your AWS spending. It features automated report generation, AI-powered analysis using AWS Bedrock, and supports both CLI and module integration modes. Key features include:

- Comprehensive cost analysis across AWS accounts and services
- AI-powered recommendations for cost optimization
- Integration with AWS Cost Explorer, Trusted Advisor, and Compute Optimizer
- Automated report generation in Excel and PowerPoint formats
- Support for custom cost allocation tags and filtering
- Secure credential management and encryption capabilities
- Interactive CLI interface with configurable options
- Model Context Protocol (MCP) server integration for AI assistants

## Repository Structure
```

.
├── src/CostMinimizer/          # Main source code directory
│   ├── arguments/              # Command line argument parsing
│   ├── commands/               # CLI command implementations
│   ├── config/                 # Configuration management and database
│   ├── report_providers/       # Report generation providers
│   │   ├── ce_reports/         # Cost Explorer report implementations
│   │   ├── co_reports/         # Compute Optimizer report implementations
│   │   ├── cur_reports/        # Cost & Usage report implementations
│   │   └── ta_reports/         # Trusted Advisor report implementations
│   ├── report_output_handler/  # Report output formatting
│   └── security/               # Authentication and encryption
├── test/                       # Test files
├── requirements.txt            # Python dependencies
└── setup.py                    # python setup.py file
```

## Usage Instructions

### Web Interface (Recommended for New Users)

CostMinimizer now includes a user-friendly web interface that eliminates the need for command-line operations!

**Quick Start:**
```bash
# Clone and navigate to repository
git clone https://github.com/aws-samples/sample-costminimizer.git
cd sample-costminimizer

# Start web interface (creates SSL certs and Docker network automatically)
./start-web-interface.sh    # Linux/Mac
# or
.\start-web-interface.ps1   # Windows PowerShell

# Access at:
# HTTP:  http://localhost:6000
# HTTPS: https://localhost:6001
```

**Features:**
- 🔐 Secure AWS credentials input and validation
- 📊 Interactive report generation (CE, TA, CO, CUR)
- 💬 AI-powered chat assistant for cost optimization questions
- 🐳 Docker command generator
- 📱 Responsive design for mobile and desktop

For detailed web interface documentation, see [WEB_INTERFACE.md](WEB_INTERFACE.md)

### CLI Usage (Advanced Users)

### Prerequisites
- Python 3.8 or higher (tested on 3.13)
- AWS credentials configured with appropriate permissions
- Local SQLite database configuration (supported through config/database.py)
- The following AWS services enabled:
  - AWS Cost Explorer
  - AWS Cost and Usage Report CUR
  - AWS Trusted Advisor
  - AWS Compute Optimizer
  - AWS Organizations (optional)
  - AWS Bedrock (for AI-powered analysis)


### Installation and configuration
There are 3 options to install and configure the tool: Windows EC2 instance (recommended), automatic with Q CLI, and manual:

##### Option 1) Windows EC2 Instance (Recommended)

**Quick Setup**: Deploy a pre-configured Windows Server 2022 EC2 instance with CostMinimizer automatically installed.

**Prerequisites**:
- AWS account with EC2 permissions
- EC2 Key Pair created in your target region (for RDP access)
- CloudFormation deployment permissions

**Deployment Steps**:

1. **Create EC2 Key Pair** (if you don't have one):
   ```bash
   # Via AWS CLI
   aws ec2 create-key-pair --key-name keypaircostminimizer --query 'KeyMaterial' --output text > keypaircostminimizer.pem
   
   # Or via AWS Console: EC2 > Key Pairs > Create Key Pair
   ```

2. **Deploy CloudFormation Template**:
   ```bash
   # Clone repository
   git clone https://github.com/aws-samples/sample-costminimizer.git
   cd sample-costminimizer
   
   # Deploy the Windows workstation
   aws cloudformation create-stack \
     --stack-name costminimizer-windows-workstation \
     --template-body file://costminimizer-windows-workstation-readymade.yaml \
     --parameters ParameterKey=KeyPairName,ParameterValue=keypaircostminimizer \
     --capabilities CAPABILITY_IAM
   ```

3. **Access Your Windows Workstation**:
   ```bash
   # Get instance details
   aws cloudformation describe-stacks --stack-name costminimizer-windows-workstation
   
   # Get Windows password (replace INSTANCE-ID)
   aws ec2 get-password-data --instance-id INSTANCE-ID --priv-launch-key keypaircostminizer.pem
   
   # Connect via RDP using the decrypted password
   ```

**What's Included**:
- Windows Server 2022 with 50GB storage
- Python 3.x, Git, VS Code, AWS CLI pre-installed
- CostMinimizer automatically configured
- All required dependencies and tools
- IAM role with necessary AWS permissions
- Security group configured for RDP access

**Setup Time**: ~15 minutes after instance launch

**Monitoring Installation**: Check `C:\UserDataLog.txt` on the instance to monitor installation progress.

**Cost**: Approximately $0.17/hour for t3.xlarge instance (varies by region)

##### Option 2) Automatic with Q CLI 

**Credentials**: 

before launching the installation, AWS credentials have to be defined.  There are three ways to define credentials.

#1. As [AWS Environment Variables](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-envvars.html)
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_SESSION_TOKEN
```
#2. Create an [AWS CLI profile](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-files.html) and specify the profile with the --profile argument when running CostMinimizer.

#3. If running inside of an EC2 instance, the command will use the permissions in the [instance profile](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2_instance-profiles.html) assigned to the instance. 

**Install with Q CLI:**

Just execute this bash Q CLI command:

_Note: if you are using the --profile option, tell Q Chat to use --profile and the name of the profile._
```
q chat "can you install the tool CosMinimizer that is availble in the repository https://github.com/aws-samples/sample-costminimizer.git. 

Clone this repository, then follow the intallation and configuration instructions contained in ~/sample-costminimizer/README.md to proceed to the installation and configuration of the tool,
following instructions written in the section called Option 3) Bash 'command instructions, Manual option'."
```

#### Option 3) Bash command instructions, Manual option

#### 2.1 Clone the repository
```
git clone https://github.com/aws-samples/sample-costminimizer.git
cd sample-costminimizer
```

#### 2.2 Setup python environment
```
python -m venv .venv
source .venv/bin/activate (or .venv\Scripts\Activate.ps1 under Windows Powershell)
```

#### 2.3 Install dependencies (should be launched from the .venv environment)
```
pip install -r requirements.txt
```

#### 2.4 Setup a Develop version of CostMinimizer tooling on the local disk
```
python setup.py develop
```

#### 2.5 Configure the tool

There is a json configuration file named cm_autoconfig in the report output directory. The default location for this config file is $HOME/cow/cm_autoconfig.json.  

For example if you know your CUR database name, table name and bucket information, you may run the following commands: 

```
# Get the current AWS account number dynamically
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# next is the configuration json file to auto configure the tooling, this is the CUR definition for the workshop studio
cat > ~/cow/cm_autoconfig.json << EOF
{
  "cur_region": "us-east-1",
  "cur_db": "cur-database",
  "cur_table": "raw_cur_data",
  "aws_cow_s3_bucket": "s3://aws-athena-query-results-${AWS_ACCOUNT_ID}-us-east-1/",
  "cur_s3_bucket": "s3://aws-athena-query-results-${AWS_ACCOUNT_ID}-us-east-1/"
}
EOF

# execute automatic update of configuration based on cm_autoconfig.json and current credentials env
CostMinimizer --configure --auto-update-conf
```

This --auto-update-conf command will find most configuration parameters and configure them.  All unconfigured parameters will need to be manually configured.  Manual configuration is done by running the command below, which will bring up the menu driven configuration.

```
CostMinimizer --configure
```


#### 2.7 Last step, check the current configuration of the tool
```
CostMinimizer --configure --ls-conf
```

#### CostMinimizer Configuration Parameters
For information, the configuration has the following parameters :
```bash
+--------------------------------+------------------------------------+------------------------------------+
|           config_id            |          aws_cow_account           |                                    |
+--------------------------------+------------------------------------+------------------------------------+
|        aws_cow_account         |            123456789012            | Your main AWS Account Number (a '12-digit account number')|
|        aws_cow_profile         |           CostMinimizer            | The name of the AWS profile to be used (in '~/.aws/cow_config' file)|
|             cur_db             |      athenacurcfn_my_report1       | The CUR Database name, for the CUR checks/requests (like 'customer_cur_data')|
|           cur_table            |             myreport1              | The CUR Table name, for the CUR checks/requests|
|           cur_region           |             us-east-1              | The CUR region,for the CUR checks/requests|
|         cur_s3_bucket          |   s3://costminimizercurtesting/   | The S3 bucket name where the results are saved (like 's3://costminimizercurtesting/') (required with --cur option)|
|            ses_send            |                                    | The SES 'DESTINATION' email address, CostMinimizer results are sent to this email|
|            ses_from            |        user@amazon.com         | the SES 'SENDER' origin email address, CostMinimizer results are sent using this origin email (optional)|
|           ses_region           |             eu-west-1              | The SES region where the Simple Email Server is running|
|            ses_smtp            | email-smtp.eu-west-1.amazonaws.com | The SES email 'SMTP' server where the Simple Email Server is running|
|           ses_login            |   ses-smtp-user.20241011-151131    | The SES Email 'LOGIN' to access the Simple Email Server is running|
|          ses_password          |            Password1234            | The SES Email 'PASSWORD' to access the Simple Email Server is running|
|       costexplorer_tags        |                                    | The costexplorer tags, a list of Cost Tag Keys|
| costexplorer_tags_value_filter |                                    | The costexplorer tags values filter, provide tag value to filter e.g. Prod*|
|         graviton_tags          |                                    | The graviton tags, a list of Tag Keys (comma separated and optional)|
|   graviton_tags_value_filter   |                                    | The graviton tag value filter, provide tag value to filter e.g. Prod*|
|         current_month          |               FALSE                | The current month, true / false for if report includes current partial month|
|           day_month            |                                    | The day of the month, when to schedule a run. 6, for the 6th by default|
|        last_month_only         |               FALSE                | The last month only, Specify true if you wish to generate for only last month|
|         output_folder          |         /home/username/cow         | !!! DO NOT MODIFY|
|       installation_mode        |           local_install            | !!! DO NOT MODIFY|
|      container_mode_home       |             /root/.cow             | !!! DO NOT MODIFY|
+--------------------------------+------------------------------------+------------------------------------+

NOTE: --CUR requires Athena and needs an s3 bucket to be defined in 'cur_s3_bucket'.
```

#### Additional Credentials Information
1. (optional) Verify or Get your AWS credentials:
  ```
  aws sts get-caller-identity                     
  ```
_CostMinimizer is using the AWS credentials defined in environment variables, your aws cli profile or the EC2 instance profile (if running inside an instance)_

You can get specific STS credentials using assume-role:
```
$credentials = aws sts assume-role  --role-arn "arn:aws:iam::123456789012:role/Admin" --role-session-name "costminimizer-session" | ConvertFrom-Json
$env:AWS_ACCESS_KEY_ID = $credentials.Credentials.AccessKeyId
$env:AWS_SECRET_ACCESS_KEY = $credentials.Credentials.SecretAccessKey
$env:AWS_SESSION_TOKEN = $credentials.Credentials.SessionToken
```

2. Check the current configuration of the tool
```
CostMinimizer --configure --ls-conf
```

3. (optional) Update tool configuration with current credentials:
```
CostMinimizer --configure --auto-update-conf
```
You can automaticaly register the current AWS credentials into CostMinimizer configuration

=> As an example, all reports will be saved into a new folder based on 
```
$ACCOUNTID_CREDENTIALS and timestamp C:\Users\$USERNAME$\cow\$ACCOUNTID_CREDENTIALS\$ACCOUNTID_CREDENTIALS-2025-04-04-09-46\
```
#### Using CostMinimizer
1. Run a basic cost analysis:
Runs Cost Explorer, Trusted Advisor, Compute Optimizer reports, and CUR Cost and Usage Reports
```
CostMinimizer --ce --ta --co --cur              
```

2. Generate AI recommendations:
Generates AI recommendations based on report data
```
CostMinimizer -r --ce --cur   
```                  

3. Generate Cost Explorer reports only
```
CostMinimizer --ce
```

4. Generate Trusted Advisor reports only
```
CostMinimizer --ta
```

5. Generate CUR Cost and Usage Reports only
```
CostMinimizer --cur
```
6. Generate Compute Optimizer Reports only

_Note on Region Selection:_
- When using `--co` (Compute Optimizer) option, the application will prompt you to select a region.
- When using `--ce` (Cost Explorer) or `--ta` (Trusted Advisor) or `--cur` (Cost & Usage Report) options, no region selection is required, and the default region (us-east-1) will be used.
- You can bypass the region selection by specifying a region with the `--region` parameter.


```
CostMinimizer --co
```

7. Generate all reports and send the result by email using -s option
```
CostMinimizer --ce --ta --co --cur -s user@example.com
```

8. Generate CUR graviton reports for a specific CUR database and table (here AWS account 000065822619 for 2025 02)
```
CostMinimizer --cur --cur --cur-db customer_cur_data --cur-table cur_000065822619_202502 --checks cur_gravitoneccsavings cur_gravitonrdssavings cur_lambdaarmsavings --region us-east-1
```

9. Ask questions about cost data:
```bash
# Ask a specific question about costs
CostMinimizer -q "based on the CostMinimizer.xlsx results provided in attached file, in the Accounts tab of the excel sheets, what is the cost of my AWS service for the year 2024 for the account named slepe000@amazon.com ?" -f "C:\Users\slepe000\cow\000538328000\000538328000-2025-04-03-11-08\CostMinimizer.xlsx"
```

## MCP (Model Context Protocol) Integration

CostMinimizer now supports MCP server integration, allowing AI assistants like Claude Desktop to directly access AWS cost optimization tools and data.

### MCP Server Setup

1. **Create MCP Configuration File**
   Create a `costminimizer-mcp-config.json` file with your AWS credentials:
   ```json
   {
     "mcpServers": {
       "costminimizer": {
         "command": "/path/to/start-costminimizer-mcp-server.sh",
         "env": {
           "AWS_ACCESS_KEY_ID": "your-access-key",
           "AWS_SECRET_ACCESS_KEY": "your-secret-key",
           "AWS_SESSION_TOKEN": "your-session-token"
         },
         "disabled": false,
         "autoApprove": []
       }
     }
   }
   ```

2. **Start MCP Server**
   The MCP server provides the following tools to AI assistants:
   - **cost-explorer**: Retrieve AWS cost and usage data
   - **cost-optimization**: Get cost optimization recommendations
   - **compute-optimizer**: Access performance optimization recommendations
   - **budgets**: Monitor budget status and alerts
   - **cost-anomaly**: Detect unusual spending patterns
   - **aws-pricing**: Query AWS service pricing information
   - **storage-lens**: Analyze S3 storage metrics
   - **ri-performance**: Monitor Reserved Instance utilization
   - **sp-performance**: Track Savings Plans performance
   - **free-tier-usage**: Check Free Tier usage limits

3. **Integration with AI Assistants**
   Once configured, AI assistants can:
   - Query your AWS costs directly
   - Generate optimization recommendations
   - Analyze spending patterns
   - Provide budget alerts
   - Answer complex cost-related questions

### MCP Usage Examples

With MCP integration, you can ask AI assistants questions like:
- "What are my top 5 AWS services by cost this month?"
- "Show me cost optimization recommendations for EC2 instances"
- "Are there any cost anomalies in my account?"
- "What's my Reserved Instance utilization rate?"
- "How much of my Free Tier am I using?"

### MCP Benefits

- **Natural Language Queries**: Ask cost questions in plain English
- **Real-time Data**: Access live AWS cost and usage information
- **Automated Analysis**: Get AI-powered insights and recommendations
- **Interactive Exploration**: Drill down into cost data conversationally
- **Multi-tool Integration**: Combine data from multiple AWS cost services

**Note**: Ensure your AWS credentials have the required permissions listed in the IAM Permissions section below.


#### Troubleshooting
1. Authentication Issues
Error: "Unable to validate credentials"
  ```bash
  # Verify AWS credentials
  aws configure list
  aws sts get-caller-identity        # CostMinimizer is using the AWS credentials defined in environment variables or .aws/

  # Reconfigure CostMinimizer
  CostMinimizer --configure --auto-update-conf    # Auto update the values of the configuration of the tooling
                                                  # Retreives the credentials from the environment variables, and configure tooling with these values
  ```

2. Report Generation Failures
- Check log file at `~/cow/CostMinimizer.log`
- Verify required AWS permissions
- Ensure Cost Explorer API is enabled
- Ensure CUR parameters are correct
- Ensure Compute Optimizer is enabled

3. Database Issues
- Delete the SQLite database file and reconfigure:
  ```bash
  rm ~/cow/CostMinimizer.db
  CostMinimizer --configure
  ```

## Docker Deployment

CostMinimizer can be containerized and deployed using Docker with Amazon ECR.

### Build and Push Docker Image to ECR

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name costminimizer --region us-east-1
   ```

2. **Build Docker Image**
   ```bash
   # Navigate to project directory
   cd sample-costminimizer
   
   # Build the Docker image
   docker build -t costminimizer .
   ```

3. **Tag and Push to ECR**
   ```bash
   # Get ECR login token
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com
   
   # Tag the image
   docker tag costminimizer:latest <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/costminimizer:latest
   
   # Push to ECR
   docker push <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/costminimizer:latest
   ```

### Deploy on EC2 instance

1. **Run costminimizer container in linux env**
   ```bash
    token=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
    roleName=$(curl -H "X-aws-ec2-metadata-token: $token" "http://169.254.169.254/latest/meta-data/iam/security-credentials/")
    credentials=$(curl -H "X-aws-ec2-metadata-token: $token" "http://169.254.169.254/latest/meta-data/iam/security-credentials/$roleName")
    export AWS_ACCESS_KEY_ID=$(echo $credentials | jq -r '.AccessKeyId')
    export AWS_SECRET_ACCESS_KEY=$(echo $credentials | jq -r '.SecretAccessKey')
    export AWS_SESSION_TOKEN=$(echo $credentials | jq -r '.Token')
    docker run -it -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN -v ~/cow:/root/cow <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/aws-samples/costminimizer:latest --ce

   ```


## Data Flow
CostMinimizer processes AWS cost data through multiple stages to generate comprehensive cost optimization recommendations.

```ascii
[AWS Services] --> [Data Collection] --> [Processing] --> [Analysis] --> [Output]
   |                    |                    |              |            |
   |                    |                    |              |            |
Cost Explorer    Fetch Raw Data     Data Aggregation    AI Analysis   Reports
Trusted Advisor  API Queries        Normalization       Cost Insights  Excel
Compute Opt.    Authentication     Transformation      Recommendations PowerPoint
Organizations   Cache Management    Tag Processing     Pattern Detection
```

Key Components:
- Arguments Parser: Flexible CLI argument handling
- Configuration Manager: Manages application settings and state
- Authentication Manager: Secure AWS credential handling
- Command Factory: Implements command pattern for operations
- Report Request Parser: Processes and validates report requests
- Database Integration: Stores configurations and report metadata
- AI Integration: Processes natural language cost queries
- Multiple Output Formats: Supports Excel and PowerPoint reporting

## Infrastructure

The AWS infrastructure includes:

Python tooling:
- `Tool`: Generates and sends monthly cost reports
  - Memory: 512MB
  - Runtime: Python 3.8+

IAM Roles:
- `CostExplorerReportLambdaIAMRole`: Provides permissions for:
  - Cost Explorer API access
  - Compute optimizer access
  - Cost and Usage Report
  - Organizations API access
  - SES email sending
  - S3 bucket access

## Required IAM Permissions

To run all the boto3 calls in the CostMinimizer application, you'll need the following consolidated IAM policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "support:DescribeTrustedAdvisorChecks",
        "support:DescribeTrustedAdvisorCheckResult",
        "support:DescribeTrustedAdvisorCheckSummaries",
        "support:RefreshTrustedAdvisorCheck",
        "support:DescribeCases",
        "support:DescribeSeverityLevels",
        "support:DescribeCommunications",
        "support:DescribeServices",
        "ce:GetCostAndUsage",
        "ce:GetReservationCoverage",
        "ce:GetReservationUtilization",
        "ce:GetReservationPurchaseRecommendation",
        "ce:GetTags",
        "athena:StartQueryExecution",
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "athena:ListDataCatalogs",
        "athena:ListDatabases",
        "athena:ListTableMetadata",
        "athena:GetTableMetadata",
        "sts:GetCallerIdentity",
        "sts:GetSessionToken",
        "bedrock:Converse",
        "bedrock:InvokeModel",
        "ec2:Describe*",
        "ec2:List*",
        "compute-optimizer:Get*"
        "glue:GetDatabases",
        "glue:GetTables",
        "organizations:DescribeOrganization",
        "organizations:ListAccounts"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::${your-cur-s3-bucket}",
        "arn:aws:s3:::${your-cur-s3-bucket}/*",
        "arn:aws:s3:::${your-athena-results-bucket}",
        "arn:aws:s3:::${your-athena-results-bucket}/*"
      ]
    }
  ]
}
```

**Note:** Replace `${your-cur-s3-bucket}` with your actual CUR S3 bucket name and `${your-athena-results-bucket}` with your Athena query results bucket name.


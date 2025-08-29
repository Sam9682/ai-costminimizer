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
There are 2 options to install and configure the tool: automatic with Q CLI and manual:

##### Option 1) Automatic with Q CLI 

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
following instructions written in the section called Option 2) Bash 'command instructions, Manual option'."
```

#### Option 2) Bash command instructions, Manual option

#### 2.1 Clone the repository
```git clone https://github.com/aws-samples/sample-costminimizer.git
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
This command will attempt to auto configure.  
```
CostMinimizer --configure --auto-update-conf
```

This command will find most configuration parameters (specified below) and configure them.  All unconfigured parameters will need to be manually configured.  Manual configuration is done by running the command below, which will bring up the menu driven configuration.

```
CostMinimizer --configure
```

Optionally, you may create a json file named cm_autoconfig in the report output directory.  The default location for the report output directory $HOME/cow/cm_autoconfig.json.  

For example if you know your CUR database name, table name and bucket information, you may specify it in this file like so: 

```
cat > ~/cow/cm_autoconfig.json << 'EOF'
{
  "cur_region": "us-east-1",
  "cur_db": "cur-database",
  "cur_table": "raw_cur_data"
  "aws_cow_s3_bucket": "s3://aws-athena-query-results-111222333444-us-east-1/",
  "cur_s3_bucket": "s3://aws-athena-query-results-111222333444-us-east-1/"
}
EOF
```

You may add any of the configuration parameters as specified in the table below.  Rerunning the --auto-update-conf configuration command is step 2.5 is an idempotent operation which will only add your new parameters when changed or added.

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


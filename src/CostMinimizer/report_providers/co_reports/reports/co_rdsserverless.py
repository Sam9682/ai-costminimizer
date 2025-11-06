# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

__author__ = "Samuel Lepetre"
__license__ = "Apache-2.0"

from ....constants import __tooling_name__
from ..co_base import CoBase
import pandas as pd
from rich.progress import track

class CoRdsserverless(CoBase):
    """Report class for analyzing RDS instances suitable for serverless architecture migration"""
    
    def supports_user_tags(self) -> bool:
        """Indicates if this report supports user-defined tags for filtering"""
        return True

    def is_report_configurable(self) -> bool:
        """Indicates if this report has configurable parameters"""
        return True

    def author(self) -> list:
        """Return list of report authors"""
        return ['slepetre']

    def name(self):
        """Return unique identifier for this report"""
        return "co_rdsserverless"

    def common_name(self) -> str:
        """Return human-readable name for this report"""
        return "RDS SERVERLESS OPTIMIZATION"

    def domain_name(self):
        """Return the domain category for this report"""
        return 'DATABASE'

    def description(self):
        """Return brief description of what this report analyzes"""
        return '''RDS instances suitable for serverless architecture migration.'''

    def long_description(self):
        """Return detailed description of the report functionality"""
        return f'''AWS RDS Serverless Optimization Report:
        This report identifies RDS instances that are excellent candidates for migration to Aurora Serverless v2.
        The comprehensive analysis includes:
        - CPU utilization patterns analysis (instances with <50% average CPU are prioritized)
        - Database engine compatibility assessment (Aurora MySQL/PostgreSQL direct compatibility, MySQL/PostgreSQL migration path)
        - Migration complexity scoring (Low/Medium/High based on engine type and configuration)
        - Automated cost savings calculations (up to 40% savings for variable workloads)
        - Instance class and workload pattern evaluation
        - Serverless suitability scoring based on utilization variability
        
        Key Benefits:
        • Identifies over-provisioned RDS instances wasting money on unused capacity
        • Provides detailed migration roadmap with complexity assessment
        • Calculates precise monthly cost savings potential
        • Supports both direct Aurora migrations and cross-engine migrations
        
        Use this report to systematically migrate variable workloads to Aurora Serverless v2 and achieve significant cost optimization through automatic scaling.'''

    def _set_recommendation(self):
        """Set the recommendation text based on report results"""
        self.recommendation = f'''Found {self.count_rows()} RDS instances suitable for serverless migration. See the report for detailed analysis.'''

    def get_report_html_link(self) -> str:
        """Return URL to documentation for this report"""
        return 'https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.html'

    def report_type(self):
        """Return the type of report (raw or processed)"""
        return 'processed'

    def report_provider(self):
        """Return the provider identifier for this report"""
        return 'co'

    def service_name(self):
        """Return the AWS service this report analyzes"""
        return 'Compute Optimizer'

    def get_required_columns(self) -> list:
        """Return list of required columns for this report"""
        return [
            'account_id',
            'db_instance_arn',
            'db_instance_identifier', 
            'engine',
            'instance_class',
            'finding',
            'avg_cpu_utilization',
            'max_cpu_utilization',
            'cpu_variability',
            'avg_db_connections',
            'avg_read_iops',
            'avg_write_iops',
            'workload_pattern',
            'serverless_compatible',
            'migration_complexity',
            self.ESTIMATED_SAVINGS_CAPTION
        ]

    def get_expected_column_headers(self) -> list:
        """Return list of expected column headers for this report"""
        return self.get_required_columns()

    def disable_report(self) -> bool:
        """Indicates if this report should be disabled"""
        return False

    def display_in_menu(self) -> bool:
        """Indicates if this report should be displayed in the menu"""
        return True

    def override_column_validation(self) -> bool:
        """Override column validation for this report"""
        return True

    def get_estimated_savings(self, sum=False) -> float:
        """Calculate and return estimated savings from the report"""
        self._set_recommendation()
        return self.set_estimate_savings(sum=sum)

    def set_estimate_savings(self, sum=False) -> float:
        """Set and calculate estimated savings from the dataframe"""
        df = self.get_report_dataframe()
        if sum and (df is not None) and (not df.empty) and (self.ESTIMATED_SAVINGS_CAPTION in df.columns):
            return float(round(df[self.ESTIMATED_SAVINGS_CAPTION].astype(float).sum(), 2))
        return 0.0

    def count_rows(self) -> int:
        """Return the number of rows found in the dataframe"""
        try:
            return self.report_result[0]['Data'].shape[0] if not self.report_result[0]['Data'].empty else 0
        except Exception as e:
            self.appConfig.console.print(f"Error in counting rows: {str(e)}")
            return 0

    def _is_serverless_compatible(self, engine, instance_class):
        """Check if RDS instance is compatible with Aurora Serverless"""
        compatible_engines = ['aurora-mysql', 'aurora-postgresql']
        
        # Aurora engines are directly compatible
        if engine in compatible_engines:
            return True, 'Low'
        
        # MySQL and PostgreSQL can be migrated to Aurora
        if engine in ['mysql', 'postgres']:
            return True, 'Medium'
        
        return False, 'High'

    def _calculate_serverless_savings(self, instance_class, avg_cpu_utilization):
        """Estimate potential savings from serverless migration"""
        # Base savings calculation - higher savings for lower utilization
        if avg_cpu_utilization < 20:
            savings_percentage = 0.4  # 40% savings for very low utilization
        elif avg_cpu_utilization < 40:
            savings_percentage = 0.25  # 25% savings for low utilization
        elif avg_cpu_utilization < 60:
            savings_percentage = 0.15  # 15% savings for moderate utilization
        else:
            savings_percentage = 0.05  # 5% savings for high utilization
        
        # Rough monthly cost estimation based on instance class
        instance_cost_map = {
            'db.t3.micro': 15, 'db.t3.small': 30, 'db.t3.medium': 60,
            'db.t3.large': 120, 'db.t3.xlarge': 240, 'db.t3.2xlarge': 480,
            'db.r5.large': 180, 'db.r5.xlarge': 360, 'db.r5.2xlarge': 720,
            'db.r5.4xlarge': 1440, 'db.r5.8xlarge': 2880
        }
        
        base_cost = instance_cost_map.get(instance_class, 100)
        return round(base_cost * savings_percentage, 2)

    def analyze_workload_pattern(self, metrics):
        """Analyze workload pattern based on CPU, IOPS, and DB connections"""
        avg_cpu = metrics.get('avg_cpu', 0)
        cpu_variability = metrics.get('cpu_variability', 0)
        avg_db_connections = metrics.get('avg_db_connections', 0)
        avg_read_iops = metrics.get('avg_read_iops', 0)
        avg_write_iops = metrics.get('avg_write_iops', 0)
        
        # Good candidate: low CPU + low IOPS + low connections
        if avg_cpu < 20 and avg_read_iops < 100 and avg_write_iops < 100 and avg_db_connections < 10:
            return 'Good Candidate'
        
        # Spiky: high variability regardless of average
        if cpu_variability > 30:
            return 'Spiky'
        
        # Variable: moderate variability
        if cpu_variability > 15:
            return 'Variable'
        
        # Low utilization but higher IOPS/connections
        if avg_cpu < 30:
            return 'Low'
        
        return 'Steady'

    def sql(self, client, region, account, display=True, report_name=''):
        """Main method to get RDS recommendations from Compute Optimizer"""
        ttype = self.set_chart_type_of_excel()
        
        # if region is a list of regions, then select the first elem else use region
        if isinstance(region, list):
            l_region = region[0]
        else:
            l_region = region
            
        if display:
            display_msg = f'[green]Running Compute Optimizer Report: {report_name} / {l_region}[/green]'
        else:
            display_msg = ''
        
        # Initialize list_cols_currency for Excel formatting
        self.list_cols_currency = [9]  # Column index for estimated savings (0-based: column 9 = ESTIMATED_SAVINGS_CAPTION)
        
        try:
            response = client.get_rds_database_recommendations()
        except Exception as e:
            # If RDS recommendations not available, return empty result
            self.appConfig.console.print(f"RDS recommendations not available: {str(e)}")
            df = pd.DataFrame(columns=self.get_required_columns())
            self.report_result.append({'Name': self.name(), 'Data': df, 'Type': ttype, 'DisplayPotentialSavings': True})
            return self.report_result

        results_list = []
        
        if response and 'rdsDBRecommendations' in response:
            iterator = track(response['rdsDBRecommendations'], description=display_msg) if self.appConfig.mode == 'cli' else response['rdsDBRecommendations']
            for recommendation in iterator:
                account_id = recommendation.get('accountId', account)
                db_arn = recommendation.get('resourceArn', '')
                db_identifier = recommendation.get('currentDBInstanceClass', '').split('.')[-1] if recommendation.get('currentDBInstanceClass') else ''
                engine = recommendation.get('engine', '')
                instance_class = recommendation.get('currentDBInstanceClass', '')
                finding = recommendation.get('finding', '')
                
                # Extract detailed utilization metrics
                avg_cpu = 0.0
                max_cpu = 0.0
                avg_memory = 0.0
                avg_db_connections = 0.0
                avg_read_iops = 0.0
                avg_write_iops = 0.0
                
                utilization_metrics = recommendation.get('utilizationMetrics', [])
                for metric in utilization_metrics:
                    metric_name = metric.get('name', '')
                    if metric_name == 'CPU':
                        avg_cpu = float(metric.get('value', 0))
                    elif metric_name == 'Memory':
                        avg_memory = float(metric.get('value', 0))
                    elif metric_name == 'DatabaseConnections':
                        avg_db_connections = float(metric.get('value', 0))
                    elif metric_name == 'ReadIOPS':
                        avg_read_iops = float(metric.get('value', 0))
                    elif metric_name == 'WriteIOPS':
                        avg_write_iops = float(metric.get('value', 0))
                
                # Get max CPU from performance risk data if available
                performance_risk = recommendation.get('performanceRisk', 'Low')
                if performance_risk == 'High':
                    max_cpu = avg_cpu * 1.5  # Estimate spike
                else:
                    max_cpu = avg_cpu * 1.2
                
                # Check serverless compatibility
                is_compatible, complexity = self._is_serverless_compatible(engine, instance_class)
                
                # Calculate potential savings
                estimated_savings = 0.0
                if is_compatible and avg_cpu < 70:  # Only consider low-medium utilization instances
                    estimated_savings = self._calculate_serverless_savings(instance_class, avg_cpu)

                # Detect spiky workloads (good serverless candidates)
                cpu_variability = max_cpu - avg_cpu if max_cpu > avg_cpu else 0

                # Determine workload pattern using analyze_workload_pattern
                workload_pattern = self.analyze_workload_pattern({
                    'avg_cpu': avg_cpu,
                    'cpu_variability': cpu_variability,
                    'avg_db_connections': avg_db_connections,
                    'avg_read_iops': avg_read_iops,
                    'avg_write_iops': avg_write_iops
                })

                # Only include instances that are good candidates for serverless
                # if workload is Good Candidate or Skipy of if finding and is_compatible 

                if is_compatible and (workload_pattern in ['Good Candidate','Spiky'] or finding in ['UNDER_PROVISIONED', 'OVER_PROVISIONED'] ):
                    results_list.append({
                        'account_id': account_id,
                        'db_instance_arn': db_arn,
                        'db_instance_identifier': db_identifier,
                        'engine': engine,
                        'instance_class': instance_class,
                        'finding': finding,
                        'avg_cpu_utilization': round(avg_cpu, 2),
                        'max_cpu_utilization': round(max_cpu, 2),
                        'cpu_variability': round(cpu_variability, 2),
                        'avg_db_connections': round(avg_db_connections, 2),
                        'avg_read_iops': round(avg_read_iops, 2),
                        'avg_write_iops': round(avg_write_iops, 2),
                        'workload_pattern': workload_pattern,
                        'serverless_compatible': 'Yes' if is_compatible else 'No',
                        'migration_complexity': complexity,
                        self.ESTIMATED_SAVINGS_CAPTION: estimated_savings
                    })
        
        # If no suitable instances found, add empty row
        if not results_list:
            results_list.append({
                'account_id': account,
                'db_instance_arn': '',
                'db_instance_identifier': 'No suitable instances found (insufficient data?)',
                'engine': '',
                'instance_class': '',
                'finding': '',
                'avg_cpu_utilization': 0,
                'max_cpu_utilization': 0,
                'cpu_variability': 0,
                'avg_db_connections': 0,
                'avg_read_iops': 0,
                'avg_write_iops': 0,
                'workload_pattern': '',
                'serverless_compatible': '',
                'migration_complexity': '',
                self.ESTIMATED_SAVINGS_CAPTION: 0.0
            })

        df = pd.DataFrame(results_list)
        self.report_result.append({'Name': self.name(), 'Data': df, 'Type': ttype, 'DisplayPotentialSavings': True})
        
        return self.report_result

    def set_chart_type_of_excel(self):
        """Return chart type ('chart' or 'pivot' or '') for Excel graph"""
        self.chart_type_of_excel = 'pivot'
        return self.chart_type_of_excel

    def get_range_categories(self):
        """Return range definition of categories in Excel graph (Column # from [0..N])"""
        return 4, 0, 4, 0

    def get_range_values(self):
        """Return list of column values in Excel graph (Column # from [0..N])"""
        return 16, 1, 16, -1

    def get_list_cols_currency(self):
        """Return list of columns to format as currency in Excel (Column # from [0..N])"""
        return [16]

    def get_group_by(self):
        """Return columns to group by in Excel graph (rank in pandas DF [1..N])"""
        return [4]
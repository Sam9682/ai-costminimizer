# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

__author__ = "Samuel Lepetre"
__license__ = "Apache-2.0"

from ....constants import __tooling_name__
from ..co_base import CoBase
import pandas as pd
import boto3

class CoRdsserverless(CoBase):
    def supports_user_tags(self) -> bool:
        return True

    def is_report_configurable(self) -> bool:
        return True

    def author(self) -> list:
        return ['slepetre']

    def name(self):
        return "co_rdsserverless"

    def common_name(self) -> str:
        return "RDS SERVERLESS OPTIMIZATION"

    def domain_name(self):
        return 'DATABASE'

    def description(self):
        return '''RDS instances suitable for serverless architecture migration.'''

    def long_description(self):
        return f'''AWS RDS Serverless Optimization Report:
        This report identifies RDS instances that could benefit from migration to Aurora Serverless v2.
        The analysis considers:
        - CPU utilization patterns (low average utilization indicates serverless suitability)
        - Database engine compatibility (Aurora MySQL/PostgreSQL)
        - Instance size and usage patterns
        - Potential cost savings from serverless architecture
        Use this report to identify databases with variable workloads that could benefit from serverless scaling.'''

    def _set_recommendation(self):
        self.recommendation = f'''Found {self.count_rows()} RDS instances suitable for serverless migration. See the report for detailed analysis.'''

    def get_report_html_link(self) -> str:
        return 'https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.html'

    def report_type(self):
        return 'processed'

    def report_provider(self):
        return 'co'

    def service_name(self):
        return 'RDS'

    def get_required_columns(self) -> list:
        return [
            'account_id',
            'db_instance_arn',
            'db_instance_identifier', 
            'engine',
            'instance_class',
            'finding',
            'avg_cpu_utilization',
            'serverless_compatible',
            'migration_complexity',
            self.ESTIMATED_SAVINGS_CAPTION
        ]

    def get_expected_column_headers(self) -> list:
        return self.get_required_columns()

    def disable_report(self) -> bool:
        return False

    def display_in_menu(self) -> bool:
        return True

    def override_column_validation(self) -> bool:
        return True

    def get_estimated_savings(self, sum=False) -> float:
        self._set_recommendation()
        return self.set_estimate_savings(sum=sum)

    def set_estimate_savings(self, sum=False) -> float:
        df = self.get_report_dataframe()
        if sum and (df is not None) and (not df.empty) and (self.ESTIMATED_SAVINGS_CAPTION in df.columns):
            return float(round(df[self.ESTIMATED_SAVINGS_CAPTION].astype(float).sum(), 2))
        return 0.0

    def count_rows(self) -> int:
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

    def sql(self, client, region, account, display=True, report_name=''):
        """Get RDS recommendations from Compute Optimizer"""
        ttype = 'chart'
        
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
        
        if response and 'databaseRecommendations' in response:
            for recommendation in response['databaseRecommendations']:
                account_id = recommendation.get('accountId', account)
                db_arn = recommendation.get('resourceArn', '')
                db_identifier = recommendation.get('currentDBInstanceClass', '').split('.')[-1] if recommendation.get('currentDBInstanceClass') else ''
                engine = recommendation.get('engine', '')
                instance_class = recommendation.get('currentDBInstanceClass', '')
                finding = recommendation.get('finding', '')
                
                # Extract CPU utilization from utilization metrics
                avg_cpu = 0.0
                utilization_metrics = recommendation.get('utilizationMetrics', [])
                for metric in utilization_metrics:
                    if metric.get('name') == 'CPU':
                        avg_cpu = float(metric.get('value', 0))
                        break
                
                # Check serverless compatibility
                is_compatible, complexity = self._is_serverless_compatible(engine, instance_class)
                
                # Calculate potential savings
                estimated_savings = 0.0
                if is_compatible and avg_cpu < 70:  # Only consider low-medium utilization instances
                    estimated_savings = self._calculate_serverless_savings(instance_class, avg_cpu)
                
                # Only include instances that are good candidates for serverless
                if is_compatible and (finding in ['UNDER_PROVISIONED', 'OVER_PROVISIONED'] or avg_cpu < 50):
                    results_list.append({
                        'account_id': account_id,
                        'db_instance_arn': db_arn,
                        'db_instance_identifier': db_identifier,
                        'engine': engine,
                        'instance_class': instance_class,
                        'finding': finding,
                        'avg_cpu_utilization': round(avg_cpu, 2),
                        'serverless_compatible': 'Yes' if is_compatible else 'No',
                        'migration_complexity': complexity,
                        self.ESTIMATED_SAVINGS_CAPTION: estimated_savings
                    })
        
        # If no suitable instances found, add empty row
        if not results_list:
            results_list.append({
                'account_id': account,
                'db_instance_arn': '',
                'db_instance_identifier': 'No suitable instances found',
                'engine': '',
                'instance_class': '',
                'finding': '',
                'avg_cpu_utilization': 0,
                'serverless_compatible': '',
                'migration_complexity': '',
                self.ESTIMATED_SAVINGS_CAPTION: 0.0
            })

        df = pd.DataFrame(results_list)
        self.report_result.append({'Name': self.name(), 'Data': df, 'Type': ttype, 'DisplayPotentialSavings': True})
        
        return self.report_result

    def set_chart_type_of_excel(self):
        self.chart_type_of_excel = 'column'
        return self.chart_type_of_excel

    def get_range_categories(self):
        return 2, 0, 2, 0

    def get_range_values(self):
        return 9, 1, 9, -1

    def get_list_cols_currency(self):
        return [9]

    def get_group_by(self):
        return [2]
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

__author__ = "Samuel Lepetre"
__license__ = "Apache-2.0"

from ....constants import __tooling_name__

from ..co_base import CoBase

import pandas as pd
from rich.progress import track

class CoInstancesreport(CoBase):
    """Report class for analyzing EC2 instance optimization recommendations from Compute Optimizer"""

    def get_report_parameters(self) -> dict:
        """Return configurable parameters for the Compute Optimizer report"""
        #{report_name:[{'parameter_name':'value','current_value':'value','allowed_values':['val','val','val']} ]}
        return {'Compute Optimizer View':[{'parameter_name':'lookback_period','current_value':30,'allowed_values':['1','2','3','4','5']} ]}

    def set_report_parameters(self,params)    -> None:
        """Set the parameters to values pulled from DB"""
        param_dict = self.get_parameter_list(params)
        self.lookback_period = int(param_dict['Compute Optimizer View'][0]['current_value'])

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
        return 'co_instancesreport'

    def common_name(self) -> str:
        """Return human-readable name for this report"""
        return 'COMPUTE OPTIMIZER view'

    def service_name(self):
        """Return the AWS service this report analyzes"""
        return 'Compute Optimizer'

    def domain_name(self):
        """Return the domain category for this report"""
        return 'COMPUTE'

    def description(self):
        """Return brief description of what this report analyzes"""
        return '''Compute Optimizer recommendations.'''

    def long_description(self):
        """Return detailed description of the report functionality"""
        return f'''AWS Compute Optimizer Main View:
        This report provides an overview of AWS Compute Optimizer recommendations for your resources.
        Compute Optimizer uses machine learning to analyze your resource utilization metrics and identify optimal AWS Compute resources.
        The report includes:
        - Recommendations for EC2 instances, EBS volumes, Lambda functions, and ECS services
        - Potential performance improvements and cost savings
        Use this view to identify opportunities for rightsizing your resources, improving performance, and reducing costs across your AWS infrastructure.'''

    def _set_recommendation(self):
        """Set the recommendation text based on report results"""
        self.recommendation = f'''Returned {self.count_rows()} rows summarizing compute optimizer. See the report for more details.'''

    def get_report_html_link(self) -> str:
        """Return URL to documentation for this report"""
        return '#'

    def report_type(self):
        """Return the type of report (raw or processed)"""
        return 'processed'

    def report_provider(self):
        """Return the provider identifier for this report"""
        return 'co'

    def savings_plan_enabled(self) -> bool:
        """Check if savings plan data is available in the report"""
        if 'savings_plan_savings_plan_a_r_n' in self.columns:
            return True

        return False

    def reservations_enabled(self) -> bool:
        """Check if reservation data is available in the report"""
        if 'reservation_reservation_a_r_n' in self.columns:
            return True

        return False

    def get_required_columns(self) -> list:
        """Return list of required columns for this report"""
        return ['accountId', 'region', 'instanceName', 'finding', 'recommendation', 'migrationEffort', 'platformDifferences', 'platformDetails', self.ESTIMATED_SAVINGS_CAPTION]

    def get_expected_column_headers(self) -> list:
        """Return list of expected column headers for this report"""
        return ['accountId', 'region', 'instanceName', 'finding', 'recommendation', 'migrationEffort', 'platformDifferences', 'platformDetails', self.ESTIMATED_SAVINGS_CAPTION]

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

        return self.set_estimate_savings()

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

    def calculate_savings(self):
        """Calculate total savings for this report"""
        return 0.0

    def enable_comparison(self) -> bool:
        """Indicates if this report supports comparison functionality"""
        return False

    def get_comparison_definition(self) -> dict:
        """Return dictionary of values required for comparison engine to function"""
        return { 
            'CSV_ID' : self.name(),
            'CSV_TITLE' : self.common_name(),
            'CSV_COLUMNS' : self.get_expected_column_headers(),
            'CSV_COLUMN_SAVINGS' : None,
            'CSV_GROUP_BY' : [],
            'CSV_COLUMNS_XLS' : [],
            'CSV_FILENAME' : self.name() + '.csv'
        }             

    def sql(self, client, region, account, display = False, report_name = ''):
        """Main method to fetch and process EC2 instance recommendations from Compute Optimizer"""
        # Create boto3 client
        client = self.appConfig.get_client('compute-optimizer', region_name=region)
        ttype = self.set_chart_type_of_excel()
        results = []

        response = client.get_ec2_instance_recommendations()

        #print(response)
        recommendation_list = response['instanceRecommendations']
        data_list = []
        
        # Create EC2 client to get instance details
        # Create boto3 EC2 client 
        # if region is a list of regions, then select the first elem else use region
        if isinstance(region, list):
            l_region = region[0]
        else:
            l_region = region
        ec2_client = self.appConfig.get_client('ec2', region_name=l_region)

        if display:
            display_msg = f'[green]Running Compute Optimizer Report: {report_name} / {l_region}[/green]'
        else:
            display_msg = ''

        iterator = track(recommendation_list, description=display_msg) if self.appConfig.mode == 'cli' else recommendation_list
        for recommendation in iterator:
                data_dict = {}
                data_dict['accountId'] = recommendation['accountId']
                data_dict['region'] = recommendation['instanceArn'].split(':')[3]
                data_dict['instanceName'] = recommendation['instanceName']
                data_dict['currentInstanceType'] = recommendation['currentInstanceType']
                data_dict['finding'] = recommendation['finding']
                
                # Get instance ID from ARN
                instance_id = recommendation['instanceArn'].split('/')[-1]
                
                try:
                    # Get instance details from EC2
                    instance_response = ec2_client.describe_instances(InstanceIds=[instance_id])
                    if instance_response['Reservations']:
                        instance = instance_response['Reservations'][0]['Instances'][0]
                        # Check platform details
                        if 'PlatformDetails' in instance:
                            data_dict['PlatformDetails'] = instance['PlatformDetails']  # Will be 'windows' if Windows
                        else:
                            data_dict['PlatformDetails'] = 'Unknown'  # If platform is not specified, it's Unknown
                    else:
                        data_dict['PlatformDetails'] = 'N/A'
                except Exception as e:
                    print(f"Error getting platform details for instance {instance_id}: {str(e)}")
                    data_dict['PlatformDetails'] = 'N/A'

                # Add migration effort if available
                if 'recommendationOptions' in recommendation and 'migrationEffort' in recommendation['recommendationOptions'][0] and recommendation['recommendationOptions'][0]['migrationEffort']:
                    data_dict['migrationEffort'] = recommendation['recommendationOptions'][0]['migrationEffort']
                else:
                    data_dict['migrationEffort'] = 'N/A'
                options = recommendation['recommendationOptions']
                for option in options:

                    data_dict['recommendation'] = option['instanceType']
                    if "savingsOpportunity" in option:
                        opp = option['savingsOpportunity']
                        if opp is not None and int(option['rank']) == 1:           
                            data_dict[self.ESTIMATED_SAVINGS_CAPTION] = option['savingsOpportunity']['estimatedMonthlySavings']['value']
                            break
                        else:
                            data_dict[self.ESTIMATED_SAVINGS_CAPTION] = 0.0
                    else:
                        data_dict[self.ESTIMATED_SAVINGS_CAPTION] = ''
                data_list.append(data_dict)
                data_dict={}

        df = pd.DataFrame(data_list)
        # get default temp folder to save export
        l_folder_ouput = self.appConfig.report_output_directory if self.appConfig.report_output_directory else './'

        #df.to_excel(l_folder_ouput+'/compute_optimizer.xlsx', sheet_name='EC2 Rightsizing', index=False)

        self.report_result.append({'Name':self.name(),'Data':df, 'Type':type, 'DisplayPotentialSavings':False})
        return self.report_result

    def set_chart_type_of_excel(self):
        """Return chart type ('chart' or 'pivot' or '') for Excel graph"""
        self.chart_type_of_excel = 'pivot'
        return self.chart_type_of_excel

    def get_range_categories(self):
        """Return range definition of categories in Excel graph (Column # from [0..N])"""
        # X1,Y1 to X2,Y2
        return 1, 4, 1, 4

    def get_range_values(self):
        """Return list of column values in Excel graph (Column # from [0..N])"""
        # X1,Y1 to X2,Y2
        return 9,1,9,-1

    def get_list_cols_currency(self):
        """Return list of columns to format as currency in Excel (Column # from [0..N])"""
        # [ColX1, ColX2,...]
        return [9]

    def get_group_by(self):
        """Return columns to group by in Excel graph (rank in pandas DF [1..N])"""
        # [ColX1, ColX2,...]
        return [1]
    
    def require_user_provided_region(self)-> bool:
        """Determine if report needs to have region provided by user"""
        return True
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

__author__ = "Samuel Lepetre"
__license__ = "Apache-2.0"

from ....constants import __tooling_name__
from ....report_providers.co_reports.co_base import CoBase
import pandas as pd
from rich.progress import track

class CoInstancesebsreport(CoBase):
    """Report class for analyzing EC2 EBS volume cost optimization recommendations from Compute Optimizer"""

    def get_report_parameters(self) -> dict:
        """Return configurable parameters for the EBS cost report"""
        #{report_name:[{'parameter_name':'value','current_value':'value','allowed_values':['val','val','val']} ]}
        return {'Ec2 Ebs Costs Details View':[{'parameter_name':'lookback_period','current_value':30,'allowed_values':['1','2','3','4','5']} ]}

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
        return 'co_instancesebsreport'

    def common_name(self) -> str:
        """Return human-readable name for this report"""
        return 'EC2 EBS COSTS view'
    
    def service_name(self):
        """Return the AWS service this report analyzes"""
        return 'Compute Optimizer'
    
    def domain_name(self):
        """Return the domain category for this report"""
        return 'STORAGE'

    def description(self):
        """Return brief description of what this report analyzes"""
        return '''EC2 EBS Costs recommendations.'''
    
    def long_description(self):
        """Return detailed description of the report functionality"""
        return f''' '''
    
    def _set_recommendation(self):
        """Set the recommendation text based on report results"""
        self.recommendation = f'''Returned {self.count_rows()} rows summarizing Ec2 Ebs Costs. See the report for more details.'''
    
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
        return ['account_id', 'volume_arn', 'current_volume_type', 'current_volume_size', 'root_volume', 'finding', 'number_of_recommendations', self.ESTIMATED_SAVINGS_CAPTION]

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

        return self.set_estimate_savings(sum)

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
        return self.get_estimated_savings()

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
        """
        Main method to fetch and process EBS volume recommendations from Compute Optimizer.
        
        This function returns data from the Compute Optimizer get_ebs_volume_recommendations method.
        The estimated savings returned are the savings that are ranked #1.
        """

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

        try:
            response = client.get_ebs_volume_recommendations()
        except:
            raise
        
        results_list = []
        if response and 'volumeRecommendations' in response:
            iterator = track(response['volumeRecommendations'], description=display_msg) if self.appConfig.mode == 'cli' else response['volumeRecommendations']
            for recommendation in iterator:
                account = recommendation['accountId']
                volume_arn = recommendation['volumeArn']
                current_volume_type = recommendation['currentConfiguration']['volumeType']
                current_volume_size = recommendation['currentConfiguration']['volumeSize']
                root_volume = recommendation['currentConfiguration']['rootVolume']
                finding = recommendation['finding']

                number_of_recommendations = len(recommendation['volumeRecommendationOptions'])
                
                if number_of_recommendations == 0:
                    estimated_savings = 0.0
                elif number_of_recommendations == 1:
                    estimated_savings = recommendation['volumeRecommendationOptions'][0]['savingsOpportunity']['estimatedMonthlySavings']['value']
                elif number_of_recommendations > 1:
                    for option in recommendation['volumeRecommendationOptions']:
                        if option['rank'] == 1:
                            estimated_savings = option['savingsOpportunity']['estimatedMonthlySavings']['value']
                
                results_list.append({
                    'account_id': account,
                    'volume_arn': volume_arn,
                    'current_volume_type': current_volume_type,
                    'current_volume_size': current_volume_size,
                    'root_volume': root_volume,
                    'finding': finding,
                    'number_of_recommendations': number_of_recommendations,
                    self.ESTIMATED_SAVINGS_CAPTION: estimated_savings
                })
        else:
            results_list.append({
                'account_id': account,
                'volume_arn': '',
                'current_volume_type': '',
                'current_volume_size': '',
                'root_volume': '',
                'finding': '',
                'number_of_recommendations': 0,
                self.ESTIMATED_SAVINGS_CAPTION: ''
            })

        df = pd.DataFrame(results_list)
        self.report_result.append({'Name':self.name(),'Data':df, 'Type':ttype, 'DisplayPotentialSavings':False})

        return self.report_result

    def set_chart_type_of_excel(self):
        """Return chart type ('chart' or 'pivot' or '') for Excel graph"""
        self.chart_type_of_excel = 'pivot'
        return self.chart_type_of_excel

    def get_range_categories(self):
        """Return range definition of categories in Excel graph (Column # from [0..N])"""
        # X1,Y1 to X2,Y2
        return 10, 0, 11, 0

    def get_range_values(self):
        """Return list of column values in Excel graph (Column # from [0..N])"""
        # X1,Y1 to X2,Y2
        return 17, 1, 17, -1

    def get_list_cols_currency(self):
        """Return list of columns to format as currency in Excel (Column # from [0..N])"""
        # [ColX1, ColX2,...]
        return [8]

    def get_group_by(self):
        """Return columns to group by in Excel graph (rank in pandas DF [1..N])"""
        # [ColX1, ColX2,...]
        return [0,1]
    
    def require_user_provided_region(self)-> bool:
        """Determine if report needs to have region provided by user"""
        return True
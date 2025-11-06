# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

__author__ = "Samuel Lepetre"
__license__ = "Apache-2.0"

from ....constants import __tooling_name__
from ..co_base import CoBase
import pandas as pd
from rich.progress import track

class CoGraviton(CoBase):
    """Report class for analyzing Graviton ARM64 migration opportunities from Compute Optimizer"""
    
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
        return "co_graviton"

    def common_name(self) -> str:
        """Return human-readable name for this report"""
        return "GRAVITON view"

    def domain_name(self):
        """Return the domain category for this report"""
        return 'COMPUTE'

    def description(self):
        """Return brief description of what this report analyzes"""
        return '''Compute Optimizer recommendations for Graviton ARM64.'''

    def long_description(self):
        """Return detailed description of the report functionality"""
        return f'''AWS Compute Optimizer Main View:
        This report provides an overview of AWS Compute Optimizer recommendations for your resources.
        Compute Optimizer uses machine learning to analyze your resource utilization metrics and identify optimal AWS Compute resources.
        The report includes:
        - Recommendations for EC2 instances that may be cost optimized with a migration to Graviton ARM64
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

    def service_name(self):
        """Return the AWS service this report analyzes"""
        return 'Compute Optimizer'

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
        return [
            'account_id', 
            'instance_arn', 
            'instance_name', 
            'current_instance_type', 
            'finding', 
            'number_of_recommendations', 
            'recommended_instance_type',
            self.ESTIMATED_SAVINGS_CAPTION]

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

    def description(self):
        """Return brief description of what this report analyzes"""
        return "AWS Compute Optimizer report for Graviton optimization opportunities"

    def long_description(self):
        """Return detailed description of the report functionality"""
        return """This report analyzes AWS Compute Optimizer recommendations to identify 
        potential cost savings through migration to Graviton-based instances. It considers 
        Windows workload exclusions and existing Graviton usage."""

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

    def calculate_savings(self):
        """Calculate potential savings from Graviton migration
        Formula: [$ EC2 total] - [$ EC2 Windows] - [$ EC2 Graviton Already] = [$EC2 Eligible Graviton]
        Then: [$ EC2 Eligible] * [%Price Delta + %Perf Delta] = $ Saving
        """
        try:
            df = self.get_report_dataframe()

            # if df is empty then return 0.0
            if df.empty:
                return 0.0
            else:
                return float(df[self.ESTIMATED_SAVINGS_CAPTION].sum())

        except Exception as e:
            raise RuntimeError(f"Error calculating Graviton savings: {str(e)}") from e

    def sql(self, client, region, account, display = True, report_name = ''):
        """
        Main method to fetch and process Graviton migration recommendations from Compute Optimizer.
        
        This function returns data from the Compute Optimizer get_ec2_instance_recommendations method.
        We filter for only recommendations with AWS_ARM64.
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

        recommendationPreferences={
            'cpuVendorArchitectures': [ 'AWS_ARM64' ]
            }

        try:
            response = client.get_ec2_instance_recommendations(recommendationPreferences=recommendationPreferences)
        except:
            raise
        
        results_list = []
        if response and 'instanceRecommendations' in response:
            iterator = track(response['instanceRecommendations'], description=display_msg) if self.appConfig.mode == 'cli' else response['instanceRecommendations']
            for recommendation in iterator:
                account = recommendation['accountId']
                instance_arn = recommendation['instanceArn']
                instance_name = recommendation['instanceName']
                current_instance_type = recommendation['currentInstanceType']
                finding = recommendation['finding']

                number_of_recommendations = len(recommendation['recommendationOptions'])

                if number_of_recommendations == 0:
                    recommended_instance_type = ''
                    estimated_savings = 0.0
                elif number_of_recommendations == 1:
                    recommended_instance_type = recommendation['recommendationOptions'][0]['instanceType']
                    estimated_savings = recommendation['recommendationOptions'][0]['savingsOpportunity']['estimatedMonthlySavings']['value']
                elif number_of_recommendations > 1:
                    for option in recommendation['recommendationOptions']:
                        if option['rank'] == 1:
                            recommended_instance_type = option['instanceType']
                            estimated_savings = option['savingsOpportunity']['estimatedMonthlySavings']['value']
                
                results_list.append({
                    'account_id': account,
                    'instance_arn': instance_arn,
                    'instance_name': instance_name,
                    'current_instance_type': current_instance_type,
                    'finding': finding,
                    'number_of_recommendations': number_of_recommendations,
                    'recommended_instance_type': recommended_instance_type,
                    self.ESTIMATED_SAVINGS_CAPTION: estimated_savings
                })
        else:
            results_list.append({
                'account_id': account,
                'instance_arn': '',
                'instance_name': '',
                'current_instance_type': '',
                'finding': '',
                'number_of_recommendations': 0,
                'recommended_instance_type': '',
                self.ESTIMATED_SAVINGS_CAPTION: ''
            })

        df = pd.DataFrame(results_list)
        self.report_result.append({'Name':self.name(),'Data':df, 'Type':ttype, 'DisplayPotentialSavings':False})

        return self.report_result

    def set_chart_type_of_excel(self):
        """Return chart type ('chart' or 'pivot' or '') for Excel graph"""
        self.chart_type_of_excel = 'chart'
        return self.chart_type_of_excel

    def get_range_categories(self):
        """Return range definition of categories in Excel graph (Column # from [0..N])"""
        # Col1, Lig1 to Col2, Lig2
        return 1, 0, 1, 0

    def get_range_values(self):
        """Return list of column values in Excel graph (Column # from [0..N])"""
        # Col1, Lig1 to Col2, Lig2
        return 10, 1, 10, -1

    def get_list_cols_currency(self):
        """Return list of columns to format as currency in Excel (Column # from [0..N])"""
        # [ColX1, ColX2,...]
        return [8]

    def get_group_by(self):
        """Return columns to group by in Excel graph (rank in pandas DF [1..N])"""
        # [ColX1, ColX2,...]
        return [1,2]
    
    def require_user_provided_region(self)-> bool:
        """Determine if report needs to have region provided by user"""
        return True
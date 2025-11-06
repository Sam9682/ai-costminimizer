# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

__author__ = "Samuel Lepetre"
__license__ = "Apache-2.0"

from ....constants import __tooling_name__
from ..co_base import CoBase
import pandas as pd
import boto3
from datetime import datetime, timedelta
from statistics import stdev, mean
from rich.progress import track

class CoRdscloudwatchanalysis(CoBase):
    """Report class for analyzing RDS instances using CloudWatch metrics for serverless migration opportunities"""
    
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
        return "co_rdscloudwatchanalysis"

    def common_name(self) -> str:
        """Return human-readable name for this report"""
        return "RDS CLOUDWATCH SPIKE ANALYSIS"

    def domain_name(self):
        """Return the domain category for this report"""
        return 'DATABASE'

    def description(self):
        """Return brief description of what this report analyzes"""
        return '''Detailed RDS spike analysis using CloudWatch metrics for serverless migration.'''

    def long_description(self):
        """Return detailed description of the report functionality"""
        return f'''AWS RDS CloudWatch Spike Analysis Report:
        This advanced report performs deep statistical analysis of RDS instances using 14 days of CloudWatch metrics to identify optimal serverless migration candidates.
        
        Comprehensive Metrics Analysis:
        • Hourly CPU utilization patterns with statistical variance calculations
        • Spike frequency analysis (instances with >2x average CPU spikes)
        • Workload variability coefficient and standard deviation analysis
        • IOPS patterns, memory usage, and database connection metrics
        • Advanced serverless suitability scoring (0-100 scale)
        
        Workload Pattern Classification:
        • Highly Spiky (>60 score): Excellent serverless candidates with up to 50% savings
        • Moderately Spiky (40-60 score): Good candidates with 35% potential savings
        • Low Utilization (<20% avg CPU): Good candidates regardless of spikes
        • Variable Workloads: Fair candidates with 20% savings potential
        • Steady Workloads: Poor serverless candidates
        
        This report provides the most detailed analysis available for RDS serverless migration decisions, using real CloudWatch data to predict serverless performance and cost benefits with high accuracy.'''

    def _set_recommendation(self):
        """Set the recommendation text based on report results"""
        self.recommendation = f'''Found {self.count_rows()} RDS instances with detailed CloudWatch analysis. See the report for spike patterns.'''

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
        return 'CloudWatch'

    def get_required_columns(self) -> list:
        """Return list of required columns for this report"""
        return [
            'account_id',
            'db_identifier',
            'engine',
            'instance_class',
            'workload_pattern',
            'spike_score',
            'serverless_suitability',
            'avg_cpu',
            'max_cpu',
            'cpu_std_dev',
            'spike_frequency_pct',
            'aurora_compatible',
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
    
    def get_rds_instances(self, region):
        """Get all RDS instances in the region"""
        try:
            # if region is a list of regions, then select the first elem else use region
            if isinstance(region, list):
                l_region = region[0]
            else:
                l_region = region
            rds = boto3.client('rds', region_name=l_region)
            response = rds.describe_db_instances()
            return response.get('DBInstances', [])
        except Exception as e:
            self.appConfig.console.print(f"Error getting RDS instances: {e}")
            return []
    
    def get_cloudwatch_metrics(self, db_identifier, region, days=14):
        """Get detailed CloudWatch metrics for spike analysis"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        # if region is a list of regions, then select the first elem else use region
        if isinstance(region, list):
            l_region = region[0]
        else:
            l_region = region
        cloudwatch = boto3.client('cloudwatch', region_name=l_region)
        metrics = {}
        metric_queries = [
            ('CPUUtilization', 'Percent'),
            ('DatabaseConnections', 'Count'),
            ('ReadIOPS', 'Count/Second'),
            ('WriteIOPS', 'Count/Second'),
            ('FreeableMemory', 'Bytes')
        ]
        
        for metric_name, unit in metric_queries:
            try:
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/RDS',
                    MetricName=metric_name,
                    Dimensions=[
                        {'Name': 'DBInstanceIdentifier', 'Value': db_identifier}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 1 hour intervals
                    Statistics=['Average', 'Maximum', 'Minimum']
                )
                
                datapoints = response.get('Datapoints', [])
                if datapoints:
                    metrics[metric_name] = {
                        'values': [dp['Average'] for dp in datapoints],
                        'max_values': [dp['Maximum'] for dp in datapoints],
                        'min_values': [dp['Minimum'] for dp in datapoints]
                    }
            except Exception as e:
                self.appConfig.console.print(f"Error getting {metric_name} for {db_identifier}: {e}")
                
        return metrics
    
    def analyze_workload_pattern(self, metrics):
        """Analyze if workload is spiky and suitable for serverless"""
        if not metrics or 'CPUUtilization' not in metrics:
            return {
                'pattern': 'Unknown',
                'spike_score': 0,
                'serverless_suitability': 'Low'
            }
        
        cpu_values = metrics['CPUUtilization']['values']
        cpu_max_values = metrics['CPUUtilization']['max_values']
        
        if len(cpu_values) < 10:  # Need sufficient data
            return {
                'pattern': 'Insufficient Data',
                'spike_score': 0,
                'serverless_suitability': 'Unknown'
            }
        
        # Calculate CPU spike characteristics
        avg_cpu = mean(cpu_values)
        max_cpu = max(cpu_max_values)
        cpu_std_dev = stdev(cpu_values)
        
        # Calculate spike frequency (how often CPU > 2x average)
        spike_threshold = avg_cpu * 2
        spike_count = sum(1 for val in cpu_max_values if val > spike_threshold)
        spike_frequency = spike_count / len(cpu_max_values)
        
        # Calculate variability coefficient
        variability_coefficient = cpu_std_dev / avg_cpu if avg_cpu > 0 else 0
        
        # Analyze additional metrics
        additional_score = 0
        
        # ReadIOPS analysis
        if 'ReadIOPS' in metrics and metrics['ReadIOPS']['values']:
            read_iops_values = metrics['ReadIOPS']['values']
            read_iops_max = metrics['ReadIOPS']['max_values']
            avg_read_iops = mean(read_iops_values)
            if avg_read_iops > 0:
                read_iops_variability = stdev(read_iops_values) / avg_read_iops
                read_spike_count = sum(1 for val in read_iops_max if val > avg_read_iops * 2)
                read_spike_freq = read_spike_count / len(read_iops_max)
                additional_score += (read_iops_variability * 5) + (read_spike_freq * 10)
        
        # WriteIOPS analysis
        if 'WriteIOPS' in metrics and metrics['WriteIOPS']['values']:
            write_iops_values = metrics['WriteIOPS']['values']
            write_iops_max = metrics['WriteIOPS']['max_values']
            avg_write_iops = mean(write_iops_values)
            if avg_write_iops > 0:
                write_iops_variability = stdev(write_iops_values) / avg_write_iops
                write_spike_count = sum(1 for val in write_iops_max if val > avg_write_iops * 2)
                write_spike_freq = write_spike_count / len(write_iops_max)
                additional_score += (write_iops_variability * 5) + (write_spike_freq * 10)
        
        # DatabaseConnections analysis
        if 'DatabaseConnections' in metrics and metrics['DatabaseConnections']['values']:
            conn_values = metrics['DatabaseConnections']['values']
            conn_max = metrics['DatabaseConnections']['max_values']
            avg_connections = mean(conn_values)
            if avg_connections > 0:
                conn_variability = stdev(conn_values) / avg_connections
                conn_spike_count = sum(1 for val in conn_max if val > avg_connections * 2)
                conn_spike_freq = conn_spike_count / len(conn_max)
                additional_score += (conn_variability * 5) + (conn_spike_freq * 10)
        
        # FreeableMemory analysis (inverse - low memory indicates high usage spikes)
        if 'FreeableMemory' in metrics and metrics['FreeableMemory']['values']:
            memory_values = metrics['FreeableMemory']['min_values']  # Use min values for memory pressure
            if memory_values:
                avg_free_memory = mean(memory_values)
                min_free_memory = min(memory_values)
                if avg_free_memory > 0:
                    memory_pressure = (avg_free_memory - min_free_memory) / avg_free_memory
                    additional_score += memory_pressure * 10
        
        # Determine spike score (0-100)
        spike_score = min(100, (
            (variability_coefficient * 30) +  # High variability
            (spike_frequency * 40) +          # Frequent spikes
            (max(0, (max_cpu - avg_cpu) / 10)) + # Spike magnitude
            additional_score                   # Additional metrics score
        ))
        
        # Calculate average activity levels
        avg_read_iops = mean(metrics['ReadIOPS']['values']) if 'ReadIOPS' in metrics and metrics['ReadIOPS']['values'] else 0
        avg_write_iops = mean(metrics['WriteIOPS']['values']) if 'WriteIOPS' in metrics and metrics['WriteIOPS']['values'] else 0
        avg_connections = mean(metrics['DatabaseConnections']['values']) if 'DatabaseConnections' in metrics and metrics['DatabaseConnections']['values'] else 0
        
        # Determine pattern
        if spike_score > 60:
            pattern = 'Highly Spiky'
            suitability = 'Excellent'
        elif spike_score > 40:
            pattern = 'Moderately Spiky'
            suitability = 'Good'
        elif avg_cpu < 20 and avg_read_iops < 100 and avg_write_iops < 50 and avg_connections < 10:
            pattern = 'Low Activity'
            suitability = 'Excellent'
        elif variability_coefficient > 0.5:
            pattern = 'Variable'
            suitability = 'Fair'
        else:
            pattern = 'Steady'
            suitability = 'Poor'
        
        return {
            'pattern': pattern,
            'spike_score': round(spike_score, 2),
            'serverless_suitability': suitability,
            'avg_cpu': round(avg_cpu, 2),
            'max_cpu': round(max_cpu, 2),
            'cpu_std_dev': round(cpu_std_dev, 2),
            'spike_frequency': round(spike_frequency * 100, 2),  # As percentage
            'variability_coefficient': round(variability_coefficient, 2),
            'avg_read_iops': round(avg_read_iops, 2),
            'avg_write_iops': round(avg_write_iops, 2),
            'avg_connections': round(avg_connections, 2)
        }
    
    def estimate_serverless_savings(self, instance_class, pattern_analysis):
        """Estimate potential cost savings from serverless migration"""
        # Base monthly costs (approximate)
        cost_map = {
            'db.t3.micro': 15, 'db.t3.small': 30, 'db.t3.medium': 60,
            'db.t3.large': 120, 'db.t3.xlarge': 240, 'db.t3.2xlarge': 480,
            'db.r5.large': 180, 'db.r5.xlarge': 360, 'db.r5.2xlarge': 720,
            'db.r5.4xlarge': 1440, 'db.r5.8xlarge': 2880
        }
        
        base_cost = cost_map.get(instance_class, 100)
        
        # Savings based on pattern analysis
        suitability = pattern_analysis.get('serverless_suitability', 'Poor')
        avg_cpu = pattern_analysis.get('avg_cpu', 50)
        
        if suitability == 'Excellent':
            savings_rate = 0.5  # 50% savings
        elif suitability == 'Good':
            savings_rate = 0.35  # 35% savings
        elif suitability == 'Fair':
            savings_rate = 0.2   # 20% savings
        else:
            savings_rate = 0.05  # 5% savings
        
        # Additional savings for very low utilization
        if avg_cpu < 15:
            savings_rate += 0.1
        
        return round(base_cost * savings_rate, 2)
    
    def sql(self, client, region, account, display=True, report_name=''):
        """Main method to analyze RDS instances using CloudWatch metrics"""
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
        self.list_cols_currency = [12]  # Column index for estimated savings
        
        instances = self.get_rds_instances(region)
        results_list = []

        iterator = track(instances, description=display_msg) if self.appConfig.mode == 'cli' else instances
        for instance in iterator:
            db_identifier = instance['DBInstanceIdentifier']
            engine = instance['Engine']
            instance_class = instance['DBInstanceClass']
            
            self.appConfig.logger.info(f"Analyzing {db_identifier}...")
            
            # Get CloudWatch metrics
            metrics = self.get_cloudwatch_metrics(db_identifier, region)
            
            # Analyze workload pattern
            pattern_analysis = self.analyze_workload_pattern(metrics)
            
            # Check Aurora compatibility
            is_aurora_compatible = engine in ['aurora-mysql', 'aurora-postgresql']
            is_migratable = engine in ['mysql', 'postgres', 'aurora-mysql', 'aurora-postgresql']
            
            if is_migratable and pattern_analysis['serverless_suitability'] != 'Poor':
                # Calculate potential savings
                estimated_savings = self.estimate_serverless_savings(instance_class, pattern_analysis)
                
                results_list.append({
                    'account_id': account,
                    'db_identifier': db_identifier,
                    'engine': engine,
                    'instance_class': instance_class,
                    'workload_pattern': pattern_analysis['pattern'],
                    'spike_score': pattern_analysis['spike_score'],
                    'serverless_suitability': pattern_analysis['serverless_suitability'],
                    'avg_cpu': pattern_analysis.get('avg_cpu', 0),
                    'max_cpu': pattern_analysis.get('max_cpu', 0),
                    'cpu_std_dev': pattern_analysis.get('cpu_std_dev', 0),
                    'spike_frequency_pct': pattern_analysis.get('spike_frequency', 0),
                    'avg_read_iops': pattern_analysis.get('avg_read_iops', 0),
                    'avg_write_iops': pattern_analysis.get('avg_write_iops', 0),
                    'avg_connections': pattern_analysis.get('avg_connections', 0),
                    'aurora_compatible': 'Yes' if is_aurora_compatible else 'No',
                    self.ESTIMATED_SAVINGS_CAPTION: estimated_savings
                })
        
        # If no suitable instances found, add empty row
        if not results_list:
            results_list.append({
                'account_id': account,
                'db_identifier': 'No suitable instances found',
                'engine': '',
                'instance_class': '',
                'workload_pattern': '',
                'spike_score': 0,
                'serverless_suitability': '',
                'avg_cpu': 0,
                'max_cpu': 0,
                'cpu_std_dev': 0,
                'spike_frequency_pct': 0,
                'avg_read_iops': 0,
                'avg_write_iops': 0,
                'avg_connections': 0,
                'aurora_compatible': '',
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
        # Col1, Lig1 to Col2, Lig2
        return 3, 0, 3, 0

    def get_range_values(self):
        """Return range definition of values in Excel graph (Column # from [0..N])"""
        # Col1, Lig1 to Col2, Lig2
        return 16, 1, 16, -1

    def get_list_cols_currency(self):
        """Return list of columns to format as currency in Excel (Column # from [0..N])"""
        return [16]

    def get_group_by(self):
        """Return columns to group by in Excel graph (rank in pandas DF [1..N])"""
        return [3,7]
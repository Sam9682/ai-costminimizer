# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

__author__ = "Samuel Lepetre"
__license__ = "Apache-2.0"

from ....constants import __tooling_name__
from ..co_base import CoBase
import pandas as pd

class CoManualsnapshots(CoBase):
    """Report to identify EBS and RDS snapshots created outside of AWS Backup"""

    def supports_user_tags(self) -> bool:
        return True

    def is_report_configurable(self) -> bool:
        return True

    def author(self) -> list:
        return ['slepetre']

    def name(self):
        return "co_manualsnapshots"

    def common_name(self) -> str:
        return "MANUAL SNAPSHOTS ANALYSIS"

    def domain_name(self):
        return 'STORAGE'

    def description(self):
        return '''EBS and RDS snapshots created outside of AWS Backup service.'''

    def long_description(self):
        return f'''AWS Manual Snapshots Analysis Report:
        This report identifies EBS and RDS snapshots created outside of AWS Backup service.
        The analysis includes:
        - EBS snapshots not managed by AWS Backup
        - RDS manual snapshots
        - Cost analysis for manual snapshot storage
        - Age and size analysis for cleanup recommendations
        Use this report to identify manual snapshots that could be managed through AWS Backup for better governance.'''

    def _set_recommendation(self):
        self.recommendation = f'''Found {self.count_rows()} manual snapshots not managed by AWS Backup. Consider migrating to AWS Backup for better governance.'''

    def get_report_html_link(self) -> str:
        return 'https://docs.aws.amazon.com/aws-backup/latest/devguide/whatisbackup.html'

    def report_type(self):
        return 'processed'

    def report_provider(self):
        return 'co'

    def service_name(self):
        return 'EC2/RDS'

    def get_required_columns(self) -> list:
        return [
            'account_id',
            'snapshot_id',
            'snapshot_type',
            'resource_id',
            'creation_date',
            'size_gb',
            'age_days',
            'created_by',
            'description',
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

    def sql(self, client, region, account, display=True, report_name=''):
        """Identify manual snapshots (non-AWS Backup)"""
        ttype = 'chart'
        results_list = []
        
        try:
            # Get EBS snapshots
            ec2_client = self.appConfig.session.client('ec2', region_name=region)
            ebs_snapshots = ec2_client.describe_snapshots(OwnerIds=['self'])
            
            for snapshot in ebs_snapshots['Snapshots']:
                is_aws_backup = self._is_aws_backup_snapshot(snapshot.get('Tags', []))
                
                if not is_aws_backup:
                    age_days = (pd.Timestamp.now() - pd.to_datetime(snapshot['StartTime'])).days
                    size_gb = snapshot['VolumeSize']
                    monthly_cost = size_gb * 0.05  # Approximate cost per GB/month
                    
                    results_list.append({
                        'account_id': account,
                        'snapshot_id': snapshot['SnapshotId'],
                        'snapshot_type': 'EBS',
                        'resource_id': snapshot['VolumeId'],
                        'creation_date': snapshot['StartTime'].strftime('%Y-%m-%d'),
                        'size_gb': size_gb,
                        'age_days': age_days,
                        'created_by': self._get_created_by(snapshot.get('Tags', [])),
                        'description': snapshot.get('Description', ''),
                        self.ESTIMATED_SAVINGS_CAPTION: round(monthly_cost, 2)
                    })
            
            # Get RDS snapshots
            rds_client = self.appConfig.session.client('rds', region_name=region)
            rds_snapshots = rds_client.describe_db_snapshots()
            
            for snapshot in rds_snapshots['DBSnapshots']:
                if snapshot['SnapshotType'] == 'manual':
                    # Get tags for RDS snapshot
                    try:
                        tags_response = rds_client.list_tags_for_resource(
                            ResourceName=snapshot['DBSnapshotArn']
                        )
                        tags = tags_response.get('TagList', [])
                    except:
                        tags = []
                    
                    is_aws_backup = self._is_aws_backup_snapshot_rds(tags)
                    
                    if not is_aws_backup:
                        age_days = (pd.Timestamp.now() - pd.to_datetime(snapshot['SnapshotCreateTime'])).days
                        size_gb = snapshot.get('AllocatedStorage', 0)
                        monthly_cost = size_gb * 0.095  # Approximate RDS snapshot cost
                        
                        results_list.append({
                            'account_id': account,
                            'snapshot_id': snapshot['DBSnapshotIdentifier'],
                            'snapshot_type': 'RDS',
                            'resource_id': snapshot['DBInstanceIdentifier'],
                            'creation_date': snapshot['SnapshotCreateTime'].strftime('%Y-%m-%d'),
                            'size_gb': size_gb,
                            'age_days': age_days,
                            'created_by': self._get_created_by_rds(tags),
                            'description': 'Manual RDS snapshot',
                            self.ESTIMATED_SAVINGS_CAPTION: round(monthly_cost, 2)
                        })
                        
        except Exception as e:
            self.appConfig.console.print(f"Error fetching snapshots: {str(e)}")
        
        if not results_list:
            results_list.append({
                'account_id': account,
                'snapshot_id': 'No manual snapshots found',
                'snapshot_type': '',
                'resource_id': '',
                'creation_date': '',
                'size_gb': 0,
                'age_days': 0,
                'created_by': '',
                'description': '',
                self.ESTIMATED_SAVINGS_CAPTION: 0.0
            })

        df = pd.DataFrame(results_list)
        self.report_result.append({'Name': self.name(), 'Data': df, 'Type': ttype})
        return self.report_result

    def _is_aws_backup_snapshot(self, tags):
        """Check if EBS snapshot was created by AWS Backup"""
        for tag in tags:
            if tag['Key'] in ['aws:backup:source-resource', 'CreatedBy']:
                if tag['Key'] == 'CreatedBy' and 'backup' in tag['Value'].lower():
                    return True
                elif tag['Key'] == 'aws:backup:source-resource':
                    return True
        return False

    def _is_aws_backup_snapshot_rds(self, tags):
        """Check if RDS snapshot was created by AWS Backup"""
        for tag in tags:
            if tag['Key'] in ['aws:backup:source-resource', 'CreatedBy']:
                if tag['Key'] == 'CreatedBy' and 'backup' in tag['Value'].lower():
                    return True
                elif tag['Key'] == 'aws:backup:source-resource':
                    return True
        return False

    def _get_created_by(self, tags):
        """Extract who created the snapshot from tags"""
        for tag in tags:
            if tag['Key'] == 'CreatedBy':
                return tag['Value']
        return 'Manual/Unknown'

    def _get_created_by_rds(self, tags):
        """Extract who created the RDS snapshot from tags"""
        for tag in tags:
            if tag['Key'] == 'CreatedBy':
                return tag['Value']
        return 'Manual/Unknown'
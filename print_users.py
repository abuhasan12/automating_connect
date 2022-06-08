import boto3
from automation_functions import *

aws_profile = input("Enter the AWS Profile Name for the AWS Account of the Connect Instance:\n")

set_up_profile_session(boto3, botocore, aws_profile)
connect = boto3.client('connect')

from_connect_id = input("\nEnter the Connect Instance ID:\n")

paginator = connect.get_paginator('list_users').paginate(InstanceId=from_connect_id)

for page in paginator:
    for agent_info in page['UserSummaryList']:
        print(f"{agent_info['Username']},{agent_info['Arn']},{agent_info['Id']}")
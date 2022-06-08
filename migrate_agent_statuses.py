import boto3
from automation_functions import *

#Ask user for aws profile to start from
first_aws_profile = input("Enter the AWS Profile Name for the AWS Account of the Connect Instance:\n")

# Set Boto3 session for AWS account we are copying from
set_up_profile_session(boto3, botocore, first_aws_profile)
connect = boto3.client('connect')

from_connect_id = input("\nEnter the Connect Instance ID you want to migrate from:\n")

paginator = connect.get_paginator('list_agent_statuses').paginate(InstanceId=from_connect_id)

agent_statuses = []

for i in paginator:
    for j in i['AgentStatusSummaryList']:
        described_status = connect.describe_agent_status(InstanceId=from_connect_id,
                                      AgentStatusId=j['Id'])
        status = {}
        status['Name'] = described_status['AgentStatus']['Name']
        status['State'] = described_status['AgentStatus']['State']
        agent_statuses.append(status)

print(agent_statuses)

second_aws_profile = input("\nPlease now enter the second AWS Profile Name:\n")

# Set Boto3 session for AWS account we are copying from
set_up_profile_session(boto3, botocore, second_aws_profile)
connect = boto3.client('connect')

to_connect_id = input("\nEnter the Connect Instance ID you want to migrate to:\n")

for status in agent_statuses:
    try:
        connect.create_agent_status(
            InstanceId=to_connect_id,
            Name=status['Name'],
            State=status['State']
        )
        print("Created ", status['Name'])
    except connect.exceptions.DuplicateResourceException:
        print(status['Name'], " already exists")
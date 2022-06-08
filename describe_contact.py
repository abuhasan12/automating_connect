import boto3
from automation_functions import *

aws_profile = input("Enter the AWS Profile Name for the AWS Account of the Connect Instance:\n")

set_up_profile_session(boto3, botocore, aws_profile)
connect = boto3.client('connect')
lamb = boto3.client('lambda')

from_connect_id = input("\nEnter the Connect Instance ID:\n")

response = connect.describe_contact(
    InstanceId=from_connect_id,
    ContactId="cb73621f-8ba3-4bc6-9c1a-6db0ad2d6e14"
)

print(response)
import sys
import boto3
import botocore.exceptions
from automation_functions import *
import json

aws_profile = input("Enter the AWS Profile Name for the AWS Account of the Connect Instance:\n")

set_up_profile_session(boto3, botocore, aws_profile)
connect = boto3.client('connect')

from_connect_id = input("\nEnter the Connect Instance ID:\n")

search_prefix = input("\nRetrieving a list of flows can take a lot of time."
                      "\nIf you'd like to only retrieve flows beginning with a certain prefix, please enter it now."
                      "\nIf not, leave blank:\n")


print("\nRetrieving flows. Please be patient.")
from_flows, search_prefix = describe_flows(connect, from_connect_id, prefix=search_prefix)

for flow in from_flows:
    if 'Content' in flow.keys():
        content, flow_meta, blocks, meta_and_blocks = get_content(flow)
        content = json.dumps(json.loads(content))
        print(content)
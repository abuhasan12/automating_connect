import sys
import boto3
import botocore.exceptions
from automation_functions import *
import json

#Ask user for aws profile to start from
first_aws_profile = input("Enter the AWS Profile Name for the AWS Account of the Connect Instance:\n")

# Set Boto3 session for AWS account we are copying from
set_up_profile_session(boto3, botocore, first_aws_profile)
connect = boto3.client('connect')
lamb = boto3.client('lambda')

from_connect_id = input("\nEnter the Connect Instance ID you want to migrate from:\n")

from_flows, search_prefix = describe_flows(connect, from_connect_id, prefix='sa')

# Ask if user is migrating between environments
prev_env = input("\nAre you migrating between environments? If so, enter the environment you are migrating from."
                 "If not, leave blank:"
                 "(dev/uat/prod)\n")
# If so, which environment are they migrating to
if prev_env:
    new_env = input("Which environment are you migrating to? (dev/uat/prod)\n")
    from_flows = change_references(from_flows, prev_env, new_env)

if prev_env and new_env:
    lambdas_needed = lambdas_from_flows(from_flows, old_env=prev_env, new_env=new_env)
else:
    lambdas_needed = lambdas_from_flows(from_flows)

print(lambdas_needed)

# Ask user for aws profile going to
second_aws_profile = input("\nPlease now enter the second AWS Profile Name:\n")

# Set Boto3 session for AWS account we are copying to
set_up_profile_session(boto3, botocore, second_aws_profile)
connect = boto3.client('connect')
lamb = boto3.client('lambda')

to_connect_id = input("\nEnter the Connect Instance ID you want to migrate to:\n")

to_flows = describe_flows(connect, to_connect_id)

to_list_of_lists = make_lists(connect, lamb, to_connect_id)

# Check if any lambdas are missing
if prev_env and new_env:
    check_lambdas, lambdas_action = check_resources(lambdas_needed, to_list_of_lists['Connect_Lambdas'], 'Lambdas', association_list=to_list_of_lists['Lambdas'], old_env=prev_env, new_env=new_env)
else:
    check_lambdas, lambdas_action = check_resources(lambdas_needed, to_list_of_lists['Connect_Lambdas'], 'Lambdas',
                                               association_list=to_list_of_lists['Lambdas'])
if lambdas_action == 'ASSOCIATE':
    associate_lambdas(connect, to_connect_id, check_lambdas, to_list_of_lists['Lambdas'])
    to_list_of_lists['Connect_Lambdas'] = get_list(connect, "list_lambda_functions", InstanceId=to_connect_id)
    if prev_env and new_env:
        missing_lambdas = check_resources(lambdas_needed, to_list_of_lists['Connect_Lambdas'], 'Lambdas', association_list=to_list_of_lists['Lambdas'], old_env=prev_env, new_env=new_env)
    else:
        missing_lambdas = check_resources(lambdas_needed, to_list_of_lists['Connect_Lambdas'], 'Lambdas',
                                          association_list=to_list_of_lists['Lambdas'])
place_dummys = False
if lambdas_action == 'PLACE_DUMMYS':
    place_dummys = True
    dummy_lambdas = check_lambdas
break_point = input("\nIf you would like to exit, enter 'n' now, otherwise leave blank:\n")
if break_point.replace(' ', '').lower() == 'n':
    sys.exit()

for flow in from_flows:
    if 'Content' in flow.keys():
        content, flow_meta, blocks, meta_and_blocks = get_content(flow)
        for i in meta_and_blocks:
            block_id, block_meta, block = extract_meta_and_blocks(i)
            arn = check_arn_status(block_meta, block)
            if block['Type'] == 'ConnectParticipantWithLexBot':
                print(block['Parameters']['LexBot']['Name'], "in", flow['Name'])
            if arn:
                blocks_list = assign_list(block, to_list_of_lists)
                if blocks_list == 'No List':
                    print("no list for", block['Type'])
                    print(block)
                    print(flow)
                if prev_env and new_env:
                    if place_dummys:
                        content = update_block_content(content, arn, block_meta, block, blocks_list,
                                                       old_env=prev_env, new_env=new_env,
                                                       dummys=dummy_lambdas, flow_details=flow)
                    else:
                        content = update_block_content(content, arn, block_meta, block, blocks_list,
                                                       old_env=prev_env, new_env=new_env)
                else:
                    if place_dummys:
                        content = update_block_content(content, arn, block_meta, block, blocks_list,
                                                       dummys=dummy_lambdas, flow_details=flow)
                    else:
                        content = update_block_content(content, arn, block_meta, block, blocks_list)
    if 'Description' in flow.keys():
        flow_description = flow['Description']
    else:
        flow_description = flow['Name']
    for to_flow in to_flows:
        if to_flow['Name'] == flow['Name']:
            connect.update_contact_flow_content(
                InstanceId=to_connect_id,
                ContactFlowId=to_flow['Id'],
                Content=content)
            print("Success")
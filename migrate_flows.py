import sys
import boto3
import botocore.exceptions
from automation_functions import *
import json

# Eventually, start with getting a list of accounts and asking migrating from and to

#Ask user for aws profile to start from
first_aws_profile = input("Enter the AWS Profile Name for the AWS Account of the Connect Instance:\n")

# Set Boto3 session for AWS account we are copying from
set_up_profile_session(boto3, botocore, first_aws_profile)
connect = boto3.client('connect')
lamb = boto3.client('lambda')

from_connect_id = input("\nEnter the Connect Instance ID you want to migrate from:\n")

# Give option to only retrieve certain flows
search_prefix = input("\nRetrieving a list of flows can take a lot of time."
                      "\nIf you'd like to only retrieve flows beginning with a certain prefix, please enter it now."
                      "\nIf not, leave blank:\n")

# Receive a list of flow names, arns, ids, types, descriptions, content
# Why dont i list here first?
print("\nRetrieving flows. Please be patient.")
from_flows, search_prefix = describe_flows(connect, from_connect_id, prefix=search_prefix)

# Give list of flows to choose from
print_flow_names(from_flows)

# Ask which flows would need migrating
selected_flows = input("\nPlease enter the names of all the flows you'd like to migrate over, separated by a comma."
                       "\nOr, if you'd like to migrate all flows with a certain prefix, enter that instead."
                       "\nOr, if you'd like to migrate all flows retrieved, leave blank:"
                       "\n(Duplicate named flows will be skipped)\n").replace(' ', '').split(',')

# Filter for only those flows
if selected_flows:
    from_flows = filter_list(from_flows, selected_flows)
    # Give filtered list of flows
    print_flow_names(from_flows)

# Option to change prefixes
from_flows = prefix_change(from_flows)

# Ask if user is migrating between environments
prev_env = input("\nAre you migrating between environments? If so, enter the environment you are migrating from."
                 "If not, leave blank:"
                 "(dev/uat/prod)\n")
# If so, which environment are they migrating to
if prev_env:
    new_env = input("Which environment are you migrating to? (dev/uat/prod)\n")
    from_flows = change_references(from_flows, prev_env, new_env)

print("\nRetrieving info from first account.")
from_described_lists = make_described_lists(connect, from_connect_id, prefix=search_prefix)
lex_bots_needed = lex_bots_from_flows(from_flows)
prompts_needed = prompts_from_flows(from_flows)
hours_needed = hours_from_flows(connect, from_connect_id, from_flows)
queues_needed = queues_from_flows(from_flows)
if prev_env and new_env:
    lambdas_needed = lambdas_from_flows(from_flows, old_env=prev_env, new_env=new_env)
else:
    lambdas_needed = lambdas_from_flows(from_flows)
print("Success")

# Ask user for aws profile going to
second_aws_profile = input("\nPlease now enter the second AWS Profile Name:\n")

# Set Boto3 session for AWS account we are copying to
set_up_profile_session(boto3, botocore, second_aws_profile)
connect = boto3.client('connect')
lamb = boto3.client('lambda')

to_connect_id = input("\nEnter the Connect Instance ID you want to migrate to:\n")

print("\nRetrieving info from second account.")
to_list_of_lists = make_lists(connect, lamb, to_connect_id)
print("Success")

# Check if any prompts are missing
check_resources(prompts_needed, to_list_of_lists['Prompts'], 'Prompts')
break_point = input("\nIf you would like to exit, enter 'n' now, otherwise leave blank:\n")
if break_point.replace(' ', '').lower() == 'n':
    sys.exit()

# Check if any hours are missing
missing_hours = check_resources(hours_needed, to_list_of_lists['Hours'], 'Hours')
if missing_hours:
    make_hours(connect, to_connect_id, missing_hours, from_described_lists['Hours'])
    to_list_of_lists['Hours'] = get_list(connect, "list_hours_of_operations", InstanceId=to_connect_id)
break_point = input("\nIf you would like to exit, enter 'n' now, otherwise leave blank:\n")
if break_point.replace(' ', '').lower() == 'n':
    sys.exit()

# Check if any queues are missing
missing_queues = check_resources(queues_needed, to_list_of_lists['Queues'], 'Queues')
if missing_queues:
    both_hours_ids = get_hours_ids(from_described_lists['Hours'], to_list_of_lists['Hours'])
    make_queues(connect, to_connect_id, missing_queues, from_described_lists['Queues'], both_hours_ids)
    to_list_of_lists['Queues'] = get_list(connect, "list_queues", InstanceId=to_connect_id)
break_point = input("\nIf you would like to exit, enter 'n' now, otherwise leave blank:\n")
if break_point.replace(' ', '').lower() == 'n':
    sys.exit()

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

# NEED TO ASSOCIATE LAMBDAS AND LEX BOTS
# NEED TO CHECK IF CONTENT WITH NEW ENV WORKS

# Creating a check for each flow.
for flow in from_flows:
    flow['Status'] = 'Unchecked'

# Start build job
print("Beginning to build flows.")
build_flows = True
while build_flows:
    one_created = False
    for flow in from_flows:
        flow_checked, from_flows = check_flow_created_or_exists(flow, to_list_of_lists['Flows'], from_flows)
        if flow_checked:
            continue
        if 'Content' in flow.keys():
            content, flow_meta, blocks, meta_and_blocks = get_content(flow)
            blocker = check_skip(meta_and_blocks, to_list_of_lists['Flows'])
            make_empty_flow = False
            if blocker:
                codependency = False
                for any_flow in from_flows:
                    if any_flow['Name'] == blocker and any_flow['Status'] == 'Skipped' and any_flow['Skipped_dependence'] == flow['Name']:
                        codependency = True
                if codependency:
                    make_empty_flow = True
                    content = empty_flow_maker()
                else:
                    print("Skipping", flow['Name'], "because it's dependent on", blocker, "which doesn't exist yet.")
                    flow['Status'] = 'Skipped'
                    flow['Skipped_dependence'] = blocker
                    continue
            if not make_empty_flow:
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
                                                               old_env=prev_env, new_env=new_env, dummys=dummy_lambdas, flow_details=flow)
                            else:
                                content = update_block_content(content, arn, block_meta, block, blocks_list, old_env=prev_env, new_env=new_env)
                        else:
                            if place_dummys:
                                content = update_block_content(content, arn, block_meta, block, blocks_list, dummys=dummy_lambdas, flow_details=flow)
                            else:
                                content = update_block_content(content, arn, block_meta, block, blocks_list)
        if 'Description' in flow.keys():
            flow_description = flow['Description']
        else:
            flow_description = flow['Name']
        try:
        # also failed first time (like queues) because queue list doesnt get updated after making queues but should be easy fix
            connect.create_contact_flow(InstanceId=to_connect_id,
                                        Name=flow['Name'],
                                        Description=flow_description,
                                        Type=flow['Type'],
                                        Content=content,
                                        Tags=flow['Tags'])
            print("\nSuccessfully created", flow['Name'])
        except connect.exceptions.InvalidContactFlowException as e:
            print(str(e))
            print(flow['Name'])
            print(flow_description)
            print(flow['Type'])
            print(content)
            print(flow['Tags'])
            sys.exit()
        # DEAL WITH UPPER AND LOWER CASE INPUTS
        one_created = True
        flow['Status'] = 'Created'
        to_list_of_lists['Flows'] = get_list(connect, 'list_contact_flows', InstanceId=to_connect_id)
    if not one_created:
        print("\nCould not create any flows.")
        for flow in from_flows:
            print(flow['Name'], ":", flow['Status'])
        # make this only if theres skipped flows it asks
        make_blank_flows = input("Would you like me to create blank flows for all those that have skipped, and then update them? (y/n")
        if make_blank_flows.replace(" ", "").lower() == 'y':
            for flow in from_flows:
                if flow['Status'] == 'Skipped':
                    if 'Content' in flow.keys():
                        content = empty_flow_maker()
                    if 'Description' in flow.keys():
                        flow_description = flow['Description']
                    else:
                        flow_description = flow['Name']
                    try:
                        connect.create_contact_flow(InstanceId=to_connect_id,
                                                    Name=flow['Name'],
                                                    Description=flow_description,
                                                    Type=flow['Type'],
                                                    Content=content,
                                                    Tags=flow['Tags'])
                        print("\nSuccessfully created", flow['Name'])
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
                    except connect.exceptions.InvalidContactFlowException as e:
                        print(str(e))
                        print(flow['Name'])
                        print(flow_description)
                        print(flow['Type'])
                        print(content)
                        print(flow['Tags'])
                        sys.exit()
        print("Ending job code: 2")
        build_flows = False
        break
    elif not any(flow['Status'] == 'Skipped' or flow['Status'] == 'Unchecked' for flow in from_flows):
        if any(flow['Status'] == 'Created' for flow in from_flows):
            print("\nJob done! Flows have been created!")
        else:
            print("\nAll flows already exist.")
        for flow in from_flows:
            print(flow['Name'], flow['Status'])
        print("Ending job code: 1")
        build_flows = False
        break
    elif not build_flows:
        print("Ending job code: 3")
        break
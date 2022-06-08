import json
import sys
import botocore

def set_up_profile_session(boto3, botocore, search_name):
    validate_profile = True
    while validate_profile:
        try:
            boto3.setup_default_session(profile_name=search_name)
            validate_profile = False
        except botocore.exceptions.ProfileNotFound:
            print("ERROR: There is no profile by that name.\n")
            search_name = input("Enter the correct AWS Profile Name:\n")

def validate_connect_instance_id(connect, instance_id):
    validate_id = True
    while validate_id:
        connect.list_instance_attributes(InstanceId=instance_id)
        validate_id = False
    return instance_id

def get_list(client, call, **kwargs):
    if 'InstanceId' in kwargs:
        try:
            paginator_list = client.get_paginator(call).paginate(InstanceId=kwargs['InstanceId'])
        except:
            print("Could not get paginator list.")
            sys.exit()
    else:
        try:
            paginator_list = client.get_paginator(call).paginate()
        except:
            print("Could not get paginator list 2.")
            sys.exit()
    list_maker = []
    if 'prefix' in kwargs:
        for i in paginator_list:
            if 'InstanceId' in kwargs:
                for j in i[list(i.keys())[1]]:
                    if 'Name' in j.keys() and j['Name'].startswith(kwargs['prefix']):
                        list_maker.append(j)
            else:
                for j in i[list(i.keys())[-1]]:
                    if 'Name' in j.keys() and j['Name'].startswith(kwargs['prefix']):
                        list_maker.append(j)
        list_maker, search_prefix = validate_list_maker(paginator_list, list_maker, kwargs['prefix'])
        return list_maker, search_prefix
    else:
        while True:
            try:
                for i in paginator_list:
                    if 'InstanceId' in kwargs:
                        for j in i[list(i.keys())[1]]:
                            list_maker.append(j)
                    else:
                        for j in i[list(i.keys())[-1]]:
                            list_maker.append(j)
            except botocore.exceptions.ClientError as err:
                response = err.response
                if (response and response.get("Error", {}).get("Code") ==
                        "TooManyRequestsException"):
                    print("Continue for TooManyRequestsException exception.")
                    continue
            break
        return list_maker

def validate_list_maker(paginator_list, list_maker, search_prefix):
    while not list_maker:
        search_prefix = input("Could not find anything with that prefix. Please enter a new one:\n")
        print("\nRetrieving flows. Please be patient.")
        for i in paginator_list:
            for j in i[list(i.keys())[1]]:
                if j['Name'].startswith(search_prefix):
                    list_maker.append(j)
    return list_maker, search_prefix

def describe_flows_from_list(connect, instance_id, flows_list):
    for flow in flows_list:
        try:
            described = connect.describe_contact_flow(InstanceId=instance_id, ContactFlowId=flow['Id'])
            for key in described[list(described.keys())[1]].keys():
                flow[key] = described[list(described.keys())[1]][key]
        except connect.exceptions.ContactFlowNotPublishedException:
            print("\nWARNING:", flow['Name'], "is not published.")
    return flows_list

def describe_flows(connect, instance_id, **kwargs):
    if 'prefix' in kwargs:
        flows_list, search_prefix = get_list(connect, "list_contact_flows", InstanceId=instance_id, prefix=kwargs['prefix'])
        flows_list = describe_flows_from_list(connect, instance_id, flows_list)
        return flows_list, search_prefix
    else:
        flows_list = get_list(connect, "list_contact_flows", InstanceId=instance_id)
        flows_list = describe_flows_from_list(connect, instance_id, flows_list)
        return flows_list

def describe_hours_from_list(connect, instance_id, hours_list):
    for hours in hours_list:
        described = connect.describe_hours_of_operation(InstanceId=instance_id, HoursOfOperationId=hours['Id'])
        for key in described[list(described.keys())[1]].keys():
            hours[key] = described[list(described.keys())[1]][key]
    return hours_list

def describe_hours(connect, instance_id):
    hours_list = get_list(connect, "list_hours_of_operations", InstanceId=instance_id)
    hours_list = describe_hours_from_list(connect, instance_id, hours_list)
    return hours_list

def describe_queues_from_list(connect, instance_id, queues_list):
    for queue in queues_list:
        if queue['QueueType'] == 'STANDARD':
            while True:
                try:
                    described = connect.describe_queue(InstanceId=instance_id, QueueId=queue['Id'])
                except botocore.exceptions.ClientError as err:
                    response = err.response
                    if (response and response.get("Error", {}).get("Code") ==
                            "TooManyRequestsException"):
                        print("Continue for TooManyRequestsException exception.")
                        continue
                break
            for key in described[list(described.keys())[1]].keys():
                queue[key] = described[list(described.keys())[1]][key]
    return queues_list

def describe_queues(connect, instance_id, **kwargs):
    if 'prefix' in kwargs:
        queues_list, search_prefix = get_list(connect, "list_queues", InstanceId=instance_id, prefix=kwargs['prefix'])
        queues_list = describe_queues_from_list(connect, instance_id, queues_list)
        return queues_list, search_prefix
    else:
        queues_list = get_list(connect, "list_queues", InstanceId=instance_id)
        queues_list = describe_queues_from_list(connect, instance_id, queues_list)
        return queues_list

def make_lists(connect, lamb, instance_id):
    prompts_list = get_list(connect, "list_prompts", InstanceId=instance_id)
    hours_list = get_list(connect, "list_hours_of_operations", InstanceId=instance_id)
    queues_list = get_list(connect, "list_queues", InstanceId=instance_id)
    flows_list = get_list(connect, "list_contact_flows", InstanceId=instance_id)
    connect_lambdas_list = get_list(connect, "list_lambda_functions", InstanceId=instance_id)
    lambdas_list = get_list(lamb, "list_functions")
    list_of_lists = {'Flows': flows_list,
                     'Queues': queues_list,
                     'Hours': hours_list,
                     'Prompts': prompts_list,
                     'Connect_Lambdas': connect_lambdas_list,
                     'Lambdas': lambdas_list}
    return list_of_lists

def make_described_lists(connect, instance_id, **kwargs):
    hours_list = describe_hours(connect, instance_id)
    queues_list = describe_queues(connect, instance_id)
    if 'prefix' in kwargs:
        flows_list = describe_flows(connect, instance_id, prefix=kwargs['prefix'])
    else:
        flows_list = describe_flows(connect, instance_id)
    described_lists = {'Flows': flows_list,
                       'Hours': hours_list,
                       'Queues': queues_list}
    return described_lists

def print_flow_names(flows_list):
    flow_names = []
    for flow in flows_list:
        flow_names.append(flow['Name'])
    print("\nFlows:", ', '.join(flow_names))

def filter_list(list, selections):
    selected_list = []
    for res in list:
        for selection in selections:
            if res['Name'].startswith(selection):
                selected_list.append(res)
    selected_list = validate_selected_list(list, selected_list)
    return selected_list

def validate_selected_list(list, selected_list):
    while not selected_list:
        print("Could not find any resources from your search.")
        for res in list:
            print(res['Name'])
        new_selections = input("\nPlease enter the names of all the resources you'd like to migrate over, separated by a comma."
                               "\nOr, if you'd like to migrate all resources with a certain prefix, enter that instead."
                               "\nOr, if you'd like to migrate all resources retrieved, leave blank:"
                               "\n(Duplicate named resources cannot be made)\n").replace(' ', '').split(',')
        for res in list:
            for selection in new_selections:
                if res['Name'].startswith(selection):
                    selected_list.append(res)
    return selected_list

def validate_prefixes(prefixes, flows_list):
    validate_all_prefixes = True
    while validate_all_prefixes:
        for prefix in prefixes:
            validated_prefix = False
            if any(flow['Name'].startswith(prefix) for flow in flows_list):
                validated_prefix = True
            if not validated_prefix:
                print("The prefix", prefix, "does not exist for any of the selected flows.")
                prefixes = input(
                    "\nPlease try re-entering any prefixes you would like to change, separated by a comma.\n").replace(
                    ' ', '').split(',')
                break
        if validated_prefix:
            validate_all_prefixes = False
    return prefixes

def change_references(flows_list, old_ref, new_ref):
    for flow in flows_list:
        if 'Name' in flow.keys() and old_ref in flow['Name']:
            flow['Name'] = flow['Name'].replace(old_ref, new_ref)
        if 'Content' in flow.keys():
            flow['Content'] = flow['Content'].replace(old_ref, new_ref)
        if 'Description' in flow.keys() and old_ref in flow['Description']:
            flow['Description'] = flow['Description'].replace(old_ref, new_ref)
    return flows_list

def prefix_change(flows_list):
    old_prefixes = input("\nWould you like to change any prefixes? If so, enter them now separated by a comma."
                         "\nIf not, leave blank:\n")
    if old_prefixes:
        old_prefixes = old_prefixes.replace(' ', '').split(',')
        old_prefixes = validate_prefixes(old_prefixes, flows_list)
        prefixes = []
        for old_prefix in old_prefixes:
            print("Prefix:", old_prefix)
            new_prefix = input("What would you like to change this prefix to?\n")
            prefixes.append({'Old_Prefix': old_prefix, 'New_Prefix': new_prefix})
        for prefix_change in prefixes:
            flows_list = change_references(flows_list, prefix_change['Old_Prefix'], prefix_change['New_Prefix'])
            print(prefix_change)
    return flows_list

def get_content(flow):
    content = flow['Content']
    loaded_content = json.loads(content)
    blocks_meta = loaded_content['Metadata']['ActionMetadata']
    blocks = loaded_content['Actions']
    meta_and_blocks = []
    for block in blocks:
        for block_meta_id in blocks_meta:
            if block_meta_id == block['Identifier']:
                block_meta = blocks_meta[block_meta_id]
                meta_and_blocks.append({"Block_ID": block['Identifier'], "Block_Meta": block_meta, "Block": block})
    return content, blocks_meta, blocks, meta_and_blocks

def extract_meta_and_blocks(block_meta_and_block):
    block_id = block_meta_and_block['Block_ID']
    block_meta = block_meta_and_block['Block_Meta']
    block = block_meta_and_block['Block']
    return block_id, block_meta, block

def identify_queues(block, block_meta):
    if block['Type'] == 'UpdateContactTargetQueue' or block['Type'] == 'DequeueContactAndTransferToQueue':
        if 'queue' in block_meta.keys():
            if isinstance(block_meta['queue'], dict) and 'id' in block_meta['queue'].keys():
                if 'queue' in block_meta['queue']['id']:
                    return True

def prompts_from_flows(flows_list):
    list_of_prompts = []
    for flow in flows_list:
        if 'Content' in flow.keys():
            content, flow_meta, blocks, meta_and_blocks = get_content(flow)
            for i in meta_and_blocks:
                block_id, block_meta, block = extract_meta_and_blocks(i)
                if 'audio' in block_meta.keys():
                    for prompt in block_meta['audio']:
                        if 'text' in prompt.keys() and prompt['text'] not in list_of_prompts:
                            list_of_prompts.append(prompt['text'])
                elif block['Type'] == 'MessageParticipant' and 'promptName' in block_meta.keys() and block_meta[
                    'promptName'] not in list_of_prompts:
                    list_of_prompts.append(block_meta['promptName'])
    return list_of_prompts

def hours_from_flows(connect, instance_id, flows_list):
    list_of_hours = []
    for flow in flows_list:
        if 'Content' in flow.keys():
            content, flow_meta, blocks, meta_and_blocks = get_content(flow)
            for i in meta_and_blocks:
                block_id, block_meta, block = extract_meta_and_blocks(i)
                if block['Type'] == 'CheckHoursOfOperation' and 'Hours' in block_meta.keys():
                    if block_meta['Hours']['text'] not in list_of_hours:
                        list_of_hours.append(block_meta['Hours']['text'])
                elif identify_queues(block, block_meta):
                    queue_hours_id = connect.describe_queue(InstanceId=instance_id, QueueId=block_meta['queue']['id'])['Queue']['HoursOfOperationId']
                    queue_hours_name = connect.describe_hours_of_operation(InstanceId=instance_id, HoursOfOperationId=queue_hours_id)['HoursOfOperation']['Name']
                    if queue_hours_name not in list_of_hours:
                        list_of_hours.append(queue_hours_name)
    return list_of_hours

def get_hours_ids(from_hours_list, to_hours_list):
    both_hours_ids = []
    for hours in from_hours_list:
        both_hours_ids.append({'Name': hours['Name'], 'Old_ID': hours['Id']})
    for i in both_hours_ids:
        for hours in to_hours_list:
            if i['Name'] == hours['Name']:
                i['New_ID'] = hours['Id']
    return both_hours_ids

def queues_from_flows(flows_list):
    list_of_queues = []
    for flow in flows_list:
        if 'Content' in flow.keys():
            content, flow_meta, blocks, meta_and_blocks = get_content(flow)
            for i in meta_and_blocks:
                block_id, block_meta, block = extract_meta_and_blocks(i)
                if identify_queues(block, block_meta) == True:
                    if block_meta['queue']['text'] not in list_of_queues:
                        list_of_queues.append(block_meta['queue']['text'])
    return list_of_queues

def lambdas_from_flows(flows_list, **kwargs):
    list_of_lambdas = []
    for flow in flows_list:
        if 'Content' in flow.keys():
            content, flow_meta, blocks, meta_and_blocks = get_content(flow)
            for i in meta_and_blocks:
                block_id, block_meta, block = extract_meta_and_blocks(i)
                if block['Type'] == 'InvokeLambdaFunction':
                    lambda_arn = block['Parameters'][list(block['Parameters'].keys())[0]]
                    function_index = lambda_arn.find(':function:')
                    lambda_name = lambda_arn[function_index + 10:]
                    if 'old_env' in kwargs and 'new_env' in kwargs and kwargs['old_env'] in lambda_name:
                        lambda_name = lambda_name.replace(kwargs['old_env'], kwargs['new_env'])
                    if lambda_name not in list_of_lambdas:
                        list_of_lambdas.append(lambda_name)
    return list_of_lambdas

def lex_bots_from_flows(flows_list):
    # list_of_lex_bots = []
    for flow in flows_list:
        if 'Content' in flow.keys():
            content, flow_meta, blocks, meta_and_blocks = get_content(flow)
            for i in meta_and_blocks:
                block_id, block_meta, block = extract_meta_and_blocks(i)
                if block['Type'] == 'ConnectParticipantWithLexBot':
                    print(block['Parameters']['LexBot']['Name'])
                    print(block)
                    print(block_meta)
    # sys.exit()

def check_resources(resources_needed, resource_list, resources, **kwargs):
    print("\nChecking to see if any", resources.lower(), "are needed in the second account before migration.")
    resources_have = []
    print(resource_list)
    for resource in resource_list:
        if isinstance(resource, dict) and 'Name' in resource.keys() and resource['Name'] not in resources_have: # if name because of agent queues
            resources_have.append(resource['Name'])
        elif isinstance(resource, str) and resource.startswith('arn:aws:lambda'):
            lambda_arn = resource
            function_index = lambda_arn.find(':function:')
            lambda_name = lambda_arn[function_index + 10:]
            if lambda_name not in resources_have:
                resources_have.append(lambda_name)
    print("needed:", resources_needed)
    print("have:", resources_have)
    resources_need_associating = []
    resources_missing = []
    for resource in resources_needed:
        if resource not in resources_have:
            if 'association_list' in kwargs:
                print(kwargs)
                if 'old_env' in kwargs and 'new_env' in kwargs and resource.replace(kwargs['new_env'], kwargs['old_env']) not in resources_have: # before env change
                    if any('FunctionName' in association.keys() and resource.replace(kwargs['new_env'], kwargs['old_env']) == association['FunctionName'] for association in kwargs['association_list']):
                        resources_need_associating.append(resource.replace(kwargs['new_env'], kwargs['old_env']))
                    else:
                        resources_missing.append(resource)
                else:
                    if any('FunctionName' in association.keys() and resource == association['FunctionName'] for association in kwargs['association_list']):
                        resources_need_associating.append(resource)
                    else:
                        resources_missing.append(resource)
            else:
                resources_missing.append(resource)
    if resources_need_associating:
        print(resources_need_associating, "all exist in the aws account but need associating with the Connect Instance.")
        associate_resources = input("Would you like me to do this for you (y/n)\n")
        if associate_resources.replace(' ', '').lower() == 'y':
            return resources_need_associating, 'ASSOCIATE'
        else:
            print("Please associate the following", resources.lower(), "to the Connect Instance first.")
            print(resources_need_associating)
            sys.exit()
    if resources_missing:
        print("You are missing the following", resources.lower())
        print(resources_missing)
        if resources != 'Prompts' and 'association_list' not in kwargs:
            resources_make = input("Would you like me to make these for you? (y/n)\n")
            if resources_make.replace(' ', '').lower() == 'y':
                return resources_missing
            else:
                print("Please make the following", resources.lower(), "first")
                print(resources_missing)
                sys.exit()
        elif 'association_list' in kwargs:
            dummy_lambdas = input("Would you like me replace these with dummy lambdas? (api-call) for now? (y/n)\n")
            if dummy_lambdas.replace(' ', '').lower() == 'y':
                return resources_missing, 'PLACE_DUMMYS'
            else:
                print("Please make the following", resources.lower(), "first")
                print(resources_missing)
                sys.exit()
        else:
            print("Please make the following", resources.lower(), "first")
            print(resources_missing)
            sys.exit()

    else:
        print("You have all the", resources.lower(), "that are required.")
        return None, None

def make_hours(connect, instance_id, missing_hours, from_hours_list):
    for missing in missing_hours:
        for hours in from_hours_list:
            if hours['Name'] == missing:
                if 'Description' in hours.keys() and len(hours['Description']) != 0:
                    hours_description = hours['Description']
                else:
                    hours_description = hours['Name']
                connect.create_hours_of_operation(InstanceId=instance_id,
                                                  Name=hours['Name'],
                                                  Description=hours_description,
                                                  TimeZone=hours['TimeZone'],
                                                  Config=hours['Config'],
                                                  Tags=hours['Tags'])

def make_queues(connect, instance_id, missing_queues, from_queues_list, hours_ids):
    for missing in missing_queues:
        for queue in from_queues_list:
            if 'Name' in queue.keys() and queue['Name'] == missing:
                if 'Description' in queue.keys():
                    queue_description = queue['Description']
                else:
                    queue_description = queue['Name']
                for i in hours_ids:
                    if queue['HoursOfOperationId'] == i['Old_ID']:
                        queue_hours_id = i['New_ID'] #cant find on same try of running script because it uses old list of hours.
                connect.create_queue(InstanceId=instance_id,
                                     Name=queue['Name'],
                                     Description=queue_description,
                                     HoursOfOperationId=queue_hours_id,
                                     Tags=queue['Tags'])

def associate_lambdas(connect, instance_id, need_associating_lambdas, to_lambdas_list):
    for lambda_associating in need_associating_lambdas:
        for lambda_ in to_lambdas_list:
            if lambda_associating == lambda_['FunctionName']:
                connect.associate_lambda_function(InstanceId=instance_id, FunctionArn=lambda_['FunctionArn'])
                
def check_flow_created_or_exists(flow, to_flows_list, from_flows_list):
    if any(from_flow['Name'] == flow['Name'] and from_flow['Status'] == 'Created' for from_flow in from_flows_list):
        return True, from_flows_list
    elif any(from_flow['Name'] == flow['Name'] and from_flow['Status'] == 'Exists' for from_flow in from_flows_list):
        return True, from_flows_list
    elif any(to_flow['Name'] == flow['Name'] for to_flow in to_flows_list):
        for from_flow in from_flows_list:
            if from_flow['Name'] == flow['Name']:
                from_flow['Status'] = 'Exists'
        return True, from_flows_list
    return False, from_flows_list

def check_skip(meta_and_blocks, to_flows_list):
    for i in meta_and_blocks:
        block_id, block_meta, block = extract_meta_and_blocks(i)
        if 'ContactFlow' in block_meta.keys() and 'text' in block_meta['ContactFlow'].keys():
            # wont find if actual name does not match in the flow despite arn matching
            if not any(to_flow['Name'] == block_meta['ContactFlow']['text'] for to_flow in to_flows_list):
                return block_meta['ContactFlow']['text']
        elif 'contactFlow' in block_meta.keys() and 'text' in block_meta['contactFlow'].keys():
            if not any(to_flow['Name'] == block_meta['contactFlow']['text'] for to_flow in to_flows_list):
                return block_meta['contactFlow']['text']

def assign_list(block, list_of_lists):
    if block['Type'] == 'TransferToFlow' or block['Type'] == 'UpdateContactEventHooks':
        blocks_list = list_of_lists['Flows']
    elif block['Type'] == 'InvokeLambdaFunction':
        blocks_list = list_of_lists['Lambdas']
    elif block['Type'] == 'CheckHoursOfOperation':
        blocks_list = list_of_lists['Hours']
    elif block['Type'] == 'MessageParticipant' or block['Type'] == 'MessageParticipantIteratively' or (block['Type'] == 'GetParticipantInput' and 'PromptId' in block['Parameters'].keys()):
        blocks_list = list_of_lists['Prompts']
    elif block['Type'] == 'UpdateContactTargetQueue' or block['Type'] == 'DequeueContactAndTransferToQueue':
        blocks_list = list_of_lists['Queues']
    else:
        blocks_list = 'No List'
    return blocks_list

def check_arn_status(block_meta, block):
    if 'audio' in block_meta.keys():
        for i in block_meta['audio']:
            if 'text' in i.keys():
                return i['id']
    if 'Parameters' in block.keys() and block['Parameters']:
        if isinstance(block['Parameters'][list(block['Parameters'].keys())[0]], str) and \
                block['Parameters'][list(block['Parameters'].keys())[0]].startswith("arn"):
            return block['Parameters'][list(block['Parameters'].keys())[0]]
        elif isinstance(block['Parameters'][list(block['Parameters'].keys())[0]], dict) and isinstance(
                block['Parameters'][list(block['Parameters'].keys())[0]][
                    list(block['Parameters'][list(block['Parameters'].keys())[0]].keys())[0]], str) and \
                block['Parameters'][list(block['Parameters'].keys())[0]][
                    list(block['Parameters'][list(block['Parameters'].keys())[0]].keys())[0]].startswith("arn"):
            return block['Parameters'][list(block['Parameters'].keys())[0]][list(block['Parameters'][list(block['Parameters'].keys())[0]].keys())[0]]
    elif isinstance(block_meta[list(block_meta.keys())[-1]], dict) and 'id' in block_meta[list(block_meta.keys())[-1]].keys() and block_meta[list(block_meta.keys())[-1]]['id']:
        return block_meta[list(block_meta.keys())[-1]]['id']

def update_block_content(content, old_arn, block_meta, block, blocks_list, **kwargs):
    if 'old_env' in kwargs and 'new_env' in kwargs:
        old_arn = old_arn.replace(kwargs['old_env'], kwargs['new_env'])
    if isinstance(block_meta[list(block_meta.keys())[-1]], dict) and 'text' in block_meta[list(block_meta.keys())[-1]].keys():
        block_name = block_meta[list(block_meta.keys())[-1]]['text']
    elif 'contactFlow' in block_meta.keys() and 'text' in block_meta['contactFlow'].keys():
        block_name = block_meta['contactFlow']['text']
    elif 'promptName' in block_meta.keys():
        block_name = block_meta['promptName']
    elif block['Type'] == 'InvokeLambdaFunction':
        function_index = old_arn.find(':function:')
        block_name = old_arn[function_index + 10:]
    elif 'audio' in block_meta.keys():
        for i in block_meta['audio']:
            if 'text' in i.keys():
                block_name = i['text']
    if 'old_env' in kwargs and 'new_env' in kwargs:
        if 'dummys' in kwargs and 'flow_details' in kwargs:
            content = update_arn(content, old_arn, block_name, blocks_list, old_env=kwargs['old_env'],
                                 new_env=kwargs['new_env'], dummys=kwargs['dummys'], flow_details=kwargs['flow_details'])
        else:
            content = update_arn(content, old_arn, block_name, blocks_list, old_env=kwargs['old_env'], new_env=kwargs['new_env'])
    else:
        if 'dummys' in kwargs and 'flow_details' in kwargs:
            content = update_arn(content, old_arn, block_name, blocks_list, dummys=kwargs['dummys'], flow_details=kwargs['flow_details'])
        else:
            content = update_arn(content, old_arn, block_name, blocks_list)
    return content

def update_arn(content, old_arn, block_name, blocks_list, **kwargs):
    if 'old_env' in kwargs and 'new_env' in kwargs:
        old_env = kwargs['old_env']
        new_env = kwargs['new_env']
    for i in blocks_list:
        if isinstance(i, str):
            print("Could not update ARN")
            sys.exit()
        if 'FunctionName' in i.keys() and ((i['FunctionName'] == block_name) or ('old_env' in kwargs and 'new_env' in kwargs and i['FunctionName'] == block_name.replace(new_env, old_env))):
            new_arn = i['FunctionArn']
            content = content.replace(old_arn, new_arn)
            if 'old_env' in kwargs and 'new_env' in kwargs:
                content = content.replace(old_arn.replace(new_env, old_env), new_arn)
            return content
        elif 'FunctionName' in i.keys() and 'dummys' in kwargs and 'flow_details' in kwargs and 'api-call' in i['FunctionName']:
            for dummy in kwargs['dummys']:
                if dummy in block_name:
                    dummy_arn = i['FunctionArn']
                    content = content.replace(old_arn, dummy_arn)
                    if 'old_env' in kwargs and 'new_env' in kwargs:
                        content = content.replace(old_arn.replace(new_env, old_env), dummy_arn)
                    print("Dummy lambda placed in place of", dummy, "in", kwargs['flow_details']['Name'])
                    return content
        elif 'Name' in i.keys() and i['Name'] == block_name:
            new_arn = i['Arn']
            content = content.replace(old_arn, new_arn)
            return content
    return content

def find_test(flows_list):
    for flow in flows_list:
        if 'Content' in flow.keys():
            content, flow_meta, blocks, meta_and_blocks = get_content(flow)
            for i in meta_and_blocks:
                block_id, block_meta, block = extract_meta_and_blocks(i)

def empty_flow_maker():
    empty_flow = '{"Version":"2019-10-30","StartAction":"87e91263-1984-40ed-9cef-ef5327d18cc7","Metadata":{"entryPointPosition":{"x":20,"y":20},"snapToGrid":false,"ActionMetadata":{"87e91263-1984-40ed-9cef-ef5327d18cc7":{"position":{"x":223,"y":19}}}},"Actions":[{"Identifier":"87e91263-1984-40ed-9cef-ef5327d18cc7","Type":"DisconnectParticipant","Parameters":{},"Transitions":{}}]}'
    return empty_flow
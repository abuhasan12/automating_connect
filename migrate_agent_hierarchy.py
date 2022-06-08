import boto3
from automation_functions import *

def update_hierarchys(client, conn_id, hiers):
    paginator = client.get_paginator('list_user_hierarchy_groups').paginate(InstanceId=conn_id)
    for i in paginator:
        for j in i['UserHierarchyGroupSummaryList']:
            for hierarchy in hiers:
                if j['Name'] == hierarchy['Name']:
                    hierarchy['NewId'] = j['Id']
                for arch in hiers:
                    if 'Parent_Name' in arch.keys() and arch['Parent_Name'] == j['Name']:
                        arch['Parent_Id'] = j['Id']
    return hiers

#Ask user for aws profile to start from
first_aws_profile = input("Enter the AWS Profile Name for the AWS Account of the Connect Instance:\n")

# Set Boto3 session for AWS account we are copying from
set_up_profile_session(boto3, botocore, first_aws_profile)
connect = boto3.client('connect')

from_connect_id = input("\nEnter the Connect Instance ID you want to migrate from:\n")

paginator = connect.get_paginator('list_user_hierarchy_groups').paginate(InstanceId=from_connect_id)

hierarchys = []

for i in paginator:
    for j in i['UserHierarchyGroupSummaryList']:
        print(j)
        described_hierarchy = connect.describe_user_hierarchy_group(InstanceId=from_connect_id,
                                                                    HierarchyGroupId=j['Id'])
        print(described_hierarchy)
        print("\n")
        hierarchy = {}
        hierarchy['Name'] = described_hierarchy['HierarchyGroup']['Name']
        hierarchy['Level'] = described_hierarchy['HierarchyGroup']['LevelId']
        if described_hierarchy['HierarchyGroup']['LevelId'] == '2':
            hierarchy['Parent_Name'] = described_hierarchy['HierarchyGroup']['HierarchyPath']['LevelOne']['Name']
        elif described_hierarchy['HierarchyGroup']['LevelId'] == '3':
            hierarchy['Parent_Name'] = described_hierarchy['HierarchyGroup']['HierarchyPath']['LevelTwo']['Name']
        elif described_hierarchy['HierarchyGroup']['LevelId'] == '4':
            hierarchy['Parent_Name'] = described_hierarchy['HierarchyGroup']['HierarchyPath']['LevelThree']['Name']
        elif described_hierarchy['HierarchyGroup']['LevelId'] == '5':
            hierarchy['Parent_Name'] = described_hierarchy['HierarchyGroup']['HierarchyPath']['LevelFour']['Name']
        hierarchys.append(hierarchy)

second_aws_profile = input("\nPlease now enter the second AWS Profile Name:\n")

# Set Boto3 session for AWS account we are copying from
set_up_profile_session(boto3, botocore, second_aws_profile)
connect = boto3.client('connect')

to_connect_id = input("\nEnter the Connect Instance ID you want to migrate to:\n")

for hierarchy in hierarchys:
    if hierarchy['Level'] == '1':
        connect.create_user_hierarchy_group(Name=hierarchy['Name'],
                                            InstanceId=to_connect_id)

hierarchys = update_hierarchys(connect, to_connect_id, hierarchys)

for hierarchy in hierarchys:
    if hierarchy['Level'] == '2':
        connect.create_user_hierarchy_group(Name= hierarchy['Name'],
                                            ParentGroupId= hierarchy['Parent_Id'],
                                            InstanceId= to_connect_id)

hierarchys = update_hierarchys(connect, to_connect_id, hierarchys)

for hierarchy in hierarchys:
    if hierarchy['Level'] == '3':
        connect.create_user_hierarchy_group(Name= hierarchy['Name'],
                                            ParentGroupId= hierarchy['Parent_Id'],
                                            InstanceId= to_connect_id)

hierarchys = update_hierarchys(connect, to_connect_id, hierarchys)

for hierarchy in hierarchys:
    if hierarchy['Level'] == '4':
        connect.create_user_hierarchy_group(Name= hierarchy['Name'],
                                            ParentGroupId= hierarchy['Parent_Id'],
                                            InstanceId= to_connect_id)

hierarchys = update_hierarchys(connect, to_connect_id, hierarchys)

for hierarchy in hierarchys:
    if hierarchy['Level'] == '5':
        connect.create_user_hierarchy_group(Name= hierarchy['Name'],
                                            ParentGroupId= hierarchy['Parent_Id'],
                                            InstanceId= to_connect_id)

hierarchys = update_hierarchys(connect, to_connect_id, hierarchys)
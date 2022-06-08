import boto3
from automation_functions import *

#Ask user for aws profile to start from
first_aws_profile = input("Enter the AWS Profile Name for the AWS Account of the Connect Instance:\n")

# Set Boto3 session for AWS account we are copying from
set_up_profile_session(boto3, botocore, first_aws_profile)
connect = boto3.client('connect')

from_connect_id = input("\nEnter the Connect Instance ID you want to migrate from:\n")

# Give option to only retrieve certain flows, mostly being sa ones.
search_prefix = input("\nDo you have a list of flows that begin with the same prefix? If so, please enter it."
                      "\nIf not, leave blank:\n")

print("\nRetrieving Queues. Please be patient.")

from_queues, search_prefix = describe_queues(connect, from_connect_id, prefix=search_prefix)

for queue in from_queues:
    print(queue['Name'])

# Ask which queues would need migrating
selected_queues = input("\nPlease enter the names of all the queues you'd like to migrate over, separated by a comma."
                        "\nOr, if you'd like to migrate all queues with a certain prefix, enter that instead."
                        "\nOr, if you'd like to migrate all queues retrieved, leave blank:"
                        "\n(Duplicate named queues will be skipped)\n").replace(' ', '').split(',')

# Filter for only those flows
if selected_queues:
    from_queues = filter_list(from_queues, selected_queues)
    # Give filtered list of flows
    for queue in from_queues:
        print(queue['Name'])

queues_needed = []
for queue in from_queues:
    queues_needed.append(queue['Name'])

from_hours = describe_hours(connect, from_connect_id)

second_aws_profile = input("\nPlease now enter the second AWS Profile Name:\n")

# Set Boto3 session for AWS account we are copying from
set_up_profile_session(boto3, botocore, second_aws_profile)
connect = boto3.client('connect')

to_connect_id = input("\nEnter the Connect Instance ID you want to migrate to:\n")

to_hours_list = get_list(connect, "list_hours_of_operations", InstanceId=to_connect_id)
to_queues_list = get_list(connect, "list_queues", InstanceId=to_connect_id)

# Check if any queues are missing
missing_queues = check_resources(queues_needed, to_queues_list, 'Queues')
print(missing_queues)
if missing_queues:
    both_hours_ids = get_hours_ids(from_hours, to_hours_list)
    make_queues(connect, to_connect_id, missing_queues, from_queues, both_hours_ids)
    to_queues_list = get_list(connect, "list_queues", InstanceId=to_connect_id)

print(to_queues_list)
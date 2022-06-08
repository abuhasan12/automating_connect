# Migrating Amazon Connect Flows

main file - migrate_flows.py

## Note to Reader

This project was an early attempt at programming in my career. The python code is not up to par, but it did the job that was needed. The project was started out of curiousity and turned in to a result. For an update on how my proficiency on python programming, see my Data-Collection-Pipeline repo.

## Background

This is the result from a personal project undertaken as part of my job as a CX Engineer. My work involved created virtual contact centres using the Amazon Connect AWS Service.
This python program was written to automate the manual labour of migrating the Amazon Connect configurations between environments and accounts.
At the time of writing this program, there was no method (such as CloudFormation) of migrating full Amazon Connect configurations between environments that would satisfy our work.

##Problems to tackle

Even for any suggestions for 'automating' the migration between accounts, they came with complications that this python program solves:

1. Creating resources in order - Using my knowledge of which resources (see resources section) to create in order, this program was written to do the same.
2. Updating ARNs - The core issue when trying to migrate Amazon Connect setups is referencing newly created resource ARNs. This was written to tackle that issue. Example - when the program tries to migrate a Queue, it will have a reference ARN to an Hours table from the account you are migrating from. However, the program will create a new Hours table (if it doesn't exist already) in the account it is migrating to and then update the reference ARN when creating the queue to match the correct Hours table.
3. Creating dependency resources. As explained in the previous point example, when migrating flows (or any other resources) that depend on the existence of another resource (such as Queues depend on Hours tables), the program will create the dependency. This is even true for contact flows that reference other contact flows (transfer to flows).

## Prerequisites
This program uses profile names set up in your .aws folder files. This requires the installation of aws-cli and boto3 as well as setting up aws-mfa if required. The configuration for each AWS account should be done in your .aws folder.

## Resources

Prompts - Check
<br>
Hours - Check | Make
<br>
Queues - Check | Make
<br>
Flows - Check | Make
<br>
Lambdas - Check | Associate
<br>
Lex Bots - Check | Associate
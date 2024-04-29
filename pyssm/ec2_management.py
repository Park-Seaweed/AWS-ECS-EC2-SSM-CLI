import sys
import boto3
import inquirer
import subprocess

def select_ec2_instance(accessible_instances):
    if not accessible_instances:
        print("\033[1;31mNo SSM-enabled EC2 instances found.\033[0m")
        return None

    instance_choices = [f"{instance['Name']} ({instance['InstanceId']})" for instance in accessible_instances]
    instance_question = [
        inquirer.List('instance',
                      message="Select EC2 Instance",
                      choices=instance_choices)
    ]
    chosen_instance = inquirer.prompt(instance_question)['instance']
    chosen_instance_id = chosen_instance.split('(')[-1].strip(')')
    return chosen_instance_id

def get_accessible_ssm_instances(profile):
    session = boto3.Session(profile_name=profile)
    ssm = session.client('ssm')
    ec2 = session.client('ec2')

    response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])

    accessible_instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            instance_name = [tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'][0]
            # Check SSM connection status
            ssm_response = ssm.describe_instance_information(
                InstanceInformationFilterList=[{'key': 'InstanceIds', 'valueSet': [instance_id]}])
            if ssm_response['InstanceInformationList']:
                accessible_instances.append({'InstanceId': instance_id, 'Name': instance_name})
    return accessible_instances


def start_ssm_session(instance_id, profile):
    cli_command = f"aws ssm start-session --profile {profile} --target {instance_id}"
    subprocess.run(cli_command, shell=True)

def manage_ec2(profile='default'):
    try:
        accessible_instances = get_accessible_ssm_instances(profile)
        chosen_instance_id = select_ec2_instance(accessible_instances)
        if chosen_instance_id:
            start_ssm_session(chosen_instance_id, profile)
    except KeyboardInterrupt:
        print("\n\033[1;33mOperation cancelled by user.\033[0m")
        sys.exit(0)
    except Exception as e:
        print(f"\033[1;31mAn error occurred: {e}\033[0m")
        sys.exit(1)
    finally:
        print("\033[1;32mThank you for using the SSM CLI Tool. Goodbye!\033[0m")


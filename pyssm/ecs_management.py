import sys
import boto3
import inquirer
import subprocess

# Constants
ERROR_COLOR = "\033[1;31m"
INFO_COLOR = "\033[1;34m"
WARNING_COLOR = "\033[1;33m"
RESET_COLOR = "\033[1;32m"
BACK_OPTION = f"{RESET_COLOR}back select\033[0m"
def get_ecs_client(profile):
    session = boto3.Session(profile_name=profile)
    return session.client('ecs')

def list_clusters(profile):
    ecs_client = get_ecs_client(profile)
    all_clusters = ecs_client.list_clusters()['clusterArns']
    fargate_clusters = []

    for cluster_arn in all_clusters:
        tags = ecs_client.list_tags_for_resource(resourceArn=cluster_arn)['tags']
        if any(tag['key'] == 'Fargate' and tag['value'] == 'true' for tag in tags):
            cluster_name = cluster_arn.split('/')[-1]
            fargate_clusters.append(cluster_name)
    return fargate_clusters

def list_services(cluster,profile):
    ecs_client = get_ecs_client(profile)
    service_arns = ecs_client.list_services(cluster=cluster)['serviceArns']
    fargate_service_names = []
    service_arn_to_name = {}

    if service_arns:
        detailed_services = ecs_client.describe_services(cluster=cluster, services=service_arns)
        for service in detailed_services['services']:
            if service.get('launchType') == 'FARGATE' and service.get('enableExecuteCommand', False):
                service_name = service['serviceName']
                fargate_service_names.append(service_name)
                service_arn_to_name[service_name] = service['serviceArn']
    return fargate_service_names, service_arn_to_name

def list_tasks(cluster, service,profile):
    ecs_client = get_ecs_client(profile)
    tasks = ecs_client.list_tasks(cluster=cluster, serviceName=service)
    return tasks.get('taskArns', [])

def get_task_containers(cluster, task_arn,profile):
    ecs_client = get_ecs_client(profile)
    response = ecs_client.describe_tasks(cluster=cluster, tasks=[task_arn])
    all_containers = response['tasks'][0]['containers']
    containers = [container for container in all_containers if container['name'] != 'datadog-sidecar']
    return containers

def select_from_list(question, choices, exit_option=False):
    if exit_option:
        choices.append(f"{RESET_COLOR}exit\033[0m")  # 'exit' 옵션 추가
    else:
        choices.append(BACK_OPTION)  # 기본적으로 'back select' 옵션 사용

    while True:
        selection_question = [inquirer.List('selection', message=question, choices=choices)]
        selection = inquirer.prompt(selection_question)['selection']
        if selection == f"{RESET_COLOR}exit\033[0m" and exit_option:
            return None  # 'exit' 선택시 함수 종료
        elif selection == BACK_OPTION and not exit_option:
            return None  # 'back select' 선택시 함수 종료
        return selection


def execute_cli_command(command):
    subprocess.run(command, shell=True)

def manage_ecs(profile='default', cluster_name=None, service_name=None):
    try:
        while True:
            if cluster_name:
                clusters = [cluster_name]
            else:
                clusters = list_clusters(profile)

            if not clusters:
                print(f"{ERROR_COLOR}No available ECS clusters found.{RESET_COLOR}")
                return

            chosen_cluster = cluster_name if cluster_name else select_from_list("Select ECS Cluster", clusters, exit_option=True)
            if chosen_cluster is None or chosen_cluster == BACK_OPTION:
                return

            while True:
                service_names, service_arn_to_name = list_services(chosen_cluster, profile)
                if service_name and service_name in service_names:
                    chosen_service_name = service_name
                else:
                    chosen_service_name = select_from_list("Select Fargate Service", service_names)
                    if chosen_service_name is None or chosen_service_name == BACK_OPTION:
                        break

                while True:
                    tasks = list_tasks(chosen_cluster, service_arn_to_name[chosen_service_name], profile)
                    if not tasks:
                        print(f"{ERROR_COLOR}No tasks running for the selected service.{RESET_COLOR}")
                        break

                    chosen_task = select_from_list("Select ECS Task", tasks)
                    if chosen_task is None or chosen_task == BACK_OPTION:
                        break

                    while True:
                        containers = get_task_containers(chosen_cluster, chosen_task, profile)
                        container_names = [container['name'] for container in containers]
                        chosen_container = select_from_list("Select Container", container_names)
                        if chosen_container is None or chosen_container == BACK_OPTION:
                            break

                        cli_command = f"aws ecs execute-command --cluster {chosen_cluster} --task {chosen_task} --container {chosen_container} --interactive --command \"/bin/bash\""
                        execute_cli_command(cli_command)
                        return
    except KeyboardInterrupt:
        print(f"\n{WARNING_COLOR}Operation cancelled by user.{RESET_COLOR}")
        sys.exit(0)
    except Exception as e:
        print(f"{ERROR_COLOR}An error occurred: {e}{RESET_COLOR}")
        sys.exit(1)
    finally:
        print(f"{WARNING_COLOR}Thank you for using the ECS management tool. Goodbye!{RESET_COLOR}")
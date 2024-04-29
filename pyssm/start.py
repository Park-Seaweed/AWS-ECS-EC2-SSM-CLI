import sys
import argparse
from ecs_management import manage_ecs
from ec2_management import manage_ec2


def main():
    parser = argparse.ArgumentParser(description="PYSSM Command Line Interface",
                                     usage="pyssm [ecs|ec2] [-p PROFILE]\n"
                                           "Example: pyssm ecs -p myprofile",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=['ecs', 'ec2'], help="Command to execute")
    parser.add_argument('-p', '--profile', default='default', help="Specify AWS profile")
    parser.add_argument('-c', '--cluster', help="Specify ECS cluster name for ECS commands")
    parser.add_argument('-s', '--service', help="Specify ECS service prefix for direct task selection")

    # 인자가 없거나 '-h', '--help'가 있는 경우, 도움말을 출력하고 종료합니다.
    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    try:
        if args.command == 'ecs':
            manage_ecs(args.profile, args.cluster, args.service)
        elif args.command == 'ec2':
            manage_ec2(args.profile)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print("\nAn error occurred:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()

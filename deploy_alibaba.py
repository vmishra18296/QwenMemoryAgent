#!/usr/bin/env python3
import argparse
from app.alibaba_client import AlibabaCloudClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Alibaba Cloud deployment helper for QwenMemoryAgent")
    parser.add_argument("--list", action="store_true", help="List ECS instances")
    parser.add_argument("--create", action="store_true", help="Create a new ECS instance")
    parser.add_argument("--delete", metavar="INSTANCE_ID", help="Delete an ECS instance")
    parser.add_argument("--image-id", default="ubuntu_20_04_x64_20G_alibase_20230427.vhd", help="Alibaba Cloud image ID")
    parser.add_argument("--instance-type", default="ecs.t5-lc2m1.nano", help="ECS instance type")
    parser.add_argument("--security-group-id", help="Security group ID for ECS instance")
    parser.add_argument("--instance-name", default="qwen-memory-agent-ecs", help="ECS instance name")
    args = parser.parse_args()

    client = AlibabaCloudClient()

    if args.list:
        instances = client.describe_instances()
        print("Alibaba Cloud ECS instances:")
        for instance in instances:
            print(f"- {instance.get('InstanceId')} | {instance.get('InstanceName')} | {instance.get('Status')}")
        return

    if args.create:
        if not args.security_group_id:
            raise ValueError("--security-group-id is required to create an ECS instance")
        result = client.create_ecs_instance(
            image_id=args.image_id,
            instance_type=args.instance_type,
            security_group_id=args.security_group_id,
            instance_name=args.instance_name,
        )
        print("Create ECS instance response:")
        print(result)
        return

    if args.delete:
        result = client.delete_instance(args.delete)
        print("Delete ECS instance response:")
        print(result)
        return

    parser.print_help()


if __name__ == "__main__":
    main()

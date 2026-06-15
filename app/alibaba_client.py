import json
import os
from typing import Any, Dict, List

from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526 import (
    CreateInstanceRequest,
    DeleteInstanceRequest,
    DescribeInstancesRequest,
)


class AlibabaCloudClient:
    def __init__(self, access_key: str = None, secret_key: str = None, region: str = None):
        self.access_key = access_key or os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
        self.secret_key = secret_key or os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
        self.region = region or os.getenv("ALIBABA_CLOUD_REGION", "cn-hangzhou")
        if not self.access_key or not self.secret_key:
            raise ValueError("Missing Alibaba Cloud credentials. Set ALIBABA_CLOUD_ACCESS_KEY_ID and ALIBABA_CLOUD_ACCESS_KEY_SECRET.")
        self.client = AcsClient(self.access_key, self.secret_key, self.region)

    def describe_instances(self, page_size: int = 10) -> List[Dict[str, Any]]:
        request = DescribeInstancesRequest.DescribeInstancesRequest()
        request.set_PageSize(page_size)
        response = self.client.do_action_with_exception(request)
        payload = json.loads(response)
        return payload.get("Instances", {}).get("Instance", [])

    def create_ecs_instance(
        self,
        image_id: str,
        instance_type: str,
        security_group_id: str,
        instance_name: str,
        internet_max_bandwidth_out: int = 1,
        system_disk_category: str = "cloud_ssd",
        instance_charge_type: str = "PostPaid",
    ) -> Dict[str, Any]:
        request = CreateInstanceRequest.CreateInstanceRequest()
        request.set_ImageId(image_id)
        request.set_InstanceType(instance_type)
        request.set_SecurityGroupId(security_group_id)
        request.set_InstanceName(instance_name)
        request.set_InternetMaxBandwidthOut(internet_max_bandwidth_out)
        request.set_SystemDiskCategory(system_disk_category)
        request.set_InstanceChargeType(instance_charge_type)
        response = self.client.do_action_with_exception(request)
        return json.loads(response)

    def delete_instance(self, instance_id: str) -> Dict[str, Any]:
        request = DeleteInstanceRequest.DeleteInstanceRequest()
        request.set_InstanceId(instance_id)
        response = self.client.do_action_with_exception(request)
        return json.loads(response)

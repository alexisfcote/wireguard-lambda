import boto3
from botocore.exceptions import ClientError
import os
import secrets
import json
from requests_dict import micro_spot_instance
from time import sleep

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

REGION = "us-east-1"


class AwsManager:
    def __init__(self, *args, **kwargs):
        self.ec2 = boto3.client("ec2", region_name=REGION)
        self.ec2ressource = boto3.resource("ec2", region_name=REGION)
        self.client_token = secrets.token_urlsafe(32)[:32]
        self.instance = None

    def start_instance(self):
        """
        Check is instance with tag wireshark alerady exist. If not launch One.
        Returns instance if success
        """
        instance = self.isInstanceAlreadyLaunched
        if not instance:
            # Do a dryrun first to verify permissions
            print("Trying to launch spot instance")
            try:
                self.ec2.request_spot_instances(
                    **micro_spot_instance, ClientToken=self.client_token, DryRun=True
                )
            except ClientError as e:
                if "DryRunOperation" not in str(e):
                    raise

            # Dry run succeeded, run start_instances without dryrun

            response = self.ec2.request_spot_instances(
                **micro_spot_instance, ClientToken=self.client_token, DryRun=False
            )

            request_id = response["SpotInstanceRequests"][0]["SpotInstanceRequestId"]
            while True:
                try:
                    response = self.ec2.describe_spot_instance_requests(
                        SpotInstanceRequestIds=[request_id],
                    )
                    instance_id = response["SpotInstanceRequests"][0]["InstanceId"]
                    break
                except (KeyError, ClientError):
                    print("Wating for instance to fullfill")
                    sleep(1)

            instance = self.ec2ressource.Instance(instance_id)
            instance.create_tags(Tags=[{'Key':'wireguard', 'Value':''}])

        self.instance = instance
        return self.instance

    @property
    def isInstanceAlreadyLaunched(self):
        response = self.ec2.describe_instances(
            Filters=[{"Name": "tag-key", "Values": ["wireguard"]}]
        )
        reservations = response["Reservations"]
        for reservation in reservations:
            instances = reservation["Instances"]
            for instance in instances:
                if instance["State"]["Name"] in ["pending", "running"]:
                    return self.ec2ressource.Instance(instance["InstanceId"])
        return False

    def link_public_address(self):
        if not self.instance:
            raise Exception("Instance not launched")

        while self.instance.state['Name']=='pending':
            print('Waiting pending instance for ip assignation')
            sleep(1)
            self.instance.load()
        
        response = self.ec2.describe_addresses(
            Filters=[{"Name": "tag-key", "Values": ["wireshark"]}]
        )
        addresses = response["Addresses"]
        if addresses:
            address = addresses[0]
            if self.instance.public_ip_address == address["PublicIp"]:
                return True
            else:
                allocationID = address["AllocationId"]
                response = self.ec2.associate_address(
                    AllocationId=allocationID, InstanceId=self.instance.instance_id
                )
                return True
        return False


def main(*args, **kwargs):
    aws = AwsManager()
    aws.start_instance()
    aws.link_public_address()
    print('Done')
    return {
        "statusCode": 200,
        "body": json.dumps('Done')
    }


if __name__ == "__main__":
    main()

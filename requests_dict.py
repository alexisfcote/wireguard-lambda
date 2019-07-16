micro_spot_instance = dict(
    InstanceCount=1,
    LaunchSpecification={
        "SecurityGroupIds": ["sg-0713f214c08f66a38"],
        "BlockDeviceMappings": [
            {
                "DeviceName": "/dev/sda1",
                "Ebs": {
                    "DeleteOnTermination": True,
                    "VolumeSize": 8,
                    "VolumeType": "gp2",
                    "Encrypted":False,
                },
            }
        ],
        "KeyName": 'hadoop',
        "EbsOptimized": False,
        "ImageId": "ami-07ef9885657eb3222",
        "InstanceType": "t2.micro",
        "Monitoring": {"Enabled":False},
        "Placement": {
            "Tenancy": "default",
        },
    },
    Type="one-time",
    InstanceInterruptionBehavior="terminate",
)

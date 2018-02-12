#! /usr/bin/env python
"""Generating CloudFormation template."""

from troposphere import (
		Base64,
		ec2,
		GetAtt,
		Join,
		Output,
		Parameter,
		Ref,
		Template,
		)

from troposphere.iam import (
    InstanceProfile,
    PolicyType as IAMPolicy,
    Role,
)

from awacs.aws import (
    Action,
    Allow,
    Policy,
    Principal,
    Statement,
)

from awacs.sts import AssumeRole

ApplicationPort="8080"
ApplicationName="jenkins"

GithubAccount = "ruprict"
GithubAnsibleURL = "https://github.com/{}/hw-aws-devops".format(GithubAccount)

AnsiblePullCmd = \
		"/usr/local/bin/ansible-pull -U {} {}.yml -i localhost".format(
			GithubAnsibleURL,
			ApplicationName
		)

t = Template()
t.add_description("Effective DevOps in AWS: Helloworld Web app")

t.add_parameter(Parameter(
	"KeyPair",
	Description="Name an Existing Key Pair to SSH",
	Type="AWS::EC2::KeyPair::KeyName",
	ConstraintDescription="must be the name of an existing EC2 KeyPair.",
	))

t.add_resource(ec2.SecurityGroup(
	"SecurityGroup",
	GroupDescription="Allow SSH and TCP/{} access".format(ApplicationPort),
	VpcId="vpc-275da842",
	SecurityGroupIngress=[
		ec2.SecurityGroupRule(
			IpProtocol="tcp",
			FromPort="22",
			ToPort="22",
			CidrIp="0.0.0.0/0",
			),
		ec2.SecurityGroupRule(
			IpProtocol="tcp",
			FromPort=ApplicationPort,
			ToPort=ApplicationPort,
			CidrIp="0.0.0.0/0",
			),
		],
	))

t.add_resource(Role(
    "Role",
    AssumeRolePolicyDocument=Policy(
        Statement=[
            Statement(
                Effect=Allow,
                Action=[AssumeRole],
                Principal=Principal("Service", ["ec2.amazonaws.com"])
            )
        ]
    )
))

t.add_resource(InstanceProfile(
    "InstanceProfile",
    Path="/",
    Roles=[Ref("Role")]
))
ud = Base64(Join('\n', [
    "#!/bin/bash",
    "yum install --enablerepo=epel -y git",
    "pip install ansible",
    AnsiblePullCmd,
    "echo '*/10 * * * * {}' > /etc/cron.d/ansible-pull".format(AnsiblePullCmd)
]))

t.add_resource(ec2.Instance(
	"instance",
	ImageId="ami-97785bed",
	SubnetId="subnet-071f5038",
	InstanceType="t2.micro",
	SecurityGroupIds=[GetAtt("SecurityGroup", "GroupId")],
	KeyName=Ref("KeyPair"),
	UserData=ud,
	IamInstanceProfile=Ref("InstanceProfile"),
))

t.add_output(Output(
	"InstancePublicIp",
	Description="Public IP of our instance.",
	Value=GetAtt("instance", "PublicIp"),
	))

t.add_output(Output(
	"WebUrl",
	Description="Application endpoint",
	Value=Join("", [
		"http://", GetAtt("instance", "PublicDnsName"),
		":", ApplicationPort
		]),
	))

print t.to_json()

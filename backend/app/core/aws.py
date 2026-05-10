import boto3
from botocore.config import Config
from app.core.config import settings


def get_dynamodb_client():
    return boto3.client("dynamodb", region_name=settings.AWS_REGION)


def get_dynamodb_resource():
    return boto3.resource("dynamodb", region_name=settings.AWS_REGION)


def get_secrets_client():
    return boto3.client("secretsmanager", region_name=settings.AWS_REGION)


def get_sqs_client():
    return boto3.client("sqs", region_name=settings.AWS_REGION)


def get_ses_client():
    return boto3.client("ses", region_name=settings.AWS_REGION)


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        config=Config(signature_version="s3v4"),
    )

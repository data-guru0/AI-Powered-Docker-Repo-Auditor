import boto3
import json
from botocore.config import Config
from app.core.config import settings
from functools import lru_cache


def get_sqs_client():
    return boto3.client("sqs", region_name=settings.AWS_REGION)


def get_dynamodb_resource():
    return boto3.resource("dynamodb", region_name=settings.AWS_REGION)


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        config=Config(signature_version="s3v4"),
    )


def get_secrets_client():
    return boto3.client("secretsmanager", region_name=settings.AWS_REGION)


def get_ses_client():
    return boto3.client("ses", region_name=settings.AWS_REGION)


def get_lambda_client():
    return boto3.client("lambda", region_name=settings.AWS_REGION)


def get_apigateway_management_client(endpoint_url: str):
    return boto3.client(
        "apigatewaymanagementapi",
        endpoint_url=endpoint_url,
        region_name=settings.AWS_REGION,
    )


@lru_cache(maxsize=1)
def get_openai_api_key() -> str:
    client = get_secrets_client()
    resp = client.get_secret_value(SecretId=settings.OPENAI_API_KEY_SECRET_NAME)
    data = json.loads(resp["SecretString"])
    return data.get("api_key", "")


@lru_cache(maxsize=1)
def get_langsmith_api_key() -> str:
    client = get_secrets_client()
    resp = client.get_secret_value(SecretId=settings.LANGSMITH_API_KEY_SECRET_NAME)
    data = json.loads(resp["SecretString"])
    return data.get("api_key", "")

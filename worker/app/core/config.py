from pydantic_settings import BaseSettings
from functools import lru_cache


class WorkerSettings(BaseSettings):
    AWS_REGION: str = "us-east-1"
    DYNAMODB_SCAN_JOBS_TABLE: str
    DYNAMODB_SCAN_RESULTS_TABLE: str
    DYNAMODB_WS_CONNECTIONS_TABLE: str
    DYNAMODB_CHAT_HISTORY_TABLE: str
    S3_SCAN_REPORTS_BUCKET: str
    SQS_SCAN_JOBS_URL: str
    REDIS_URL: str
    OPENAI_API_KEY_SECRET_NAME: str
    LANGSMITH_API_KEY_SECRET_NAME: str
    SECRET_PREFIX: str = "docker-auditor/dev"
    LANGCHAIN_PROJECT: str = "docker-image-auditor"
    LANGCHAIN_TRACING_V2: str = "true"
    TRIVY_LAMBDA_FUNCTION_NAME: str
    WEBSOCKET_API_ENDPOINT: str
    SES_FROM_EMAIL: str

    class Config:
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> WorkerSettings:
    return WorkerSettings()


settings = get_settings()

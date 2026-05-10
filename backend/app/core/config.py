from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    FRONTEND_URL: str
    AWS_REGION: str = "us-east-1"
    COGNITO_USER_POOL_ID: str
    COGNITO_CLIENT_ID: str
    DYNAMODB_SCAN_JOBS_TABLE: str
    DYNAMODB_SCAN_RESULTS_TABLE: str
    DYNAMODB_CONNECTIONS_TABLE: str
    DYNAMODB_WS_CONNECTIONS_TABLE: str
    DYNAMODB_CHAT_HISTORY_TABLE: str
    SQS_SCAN_JOBS_URL: str
    S3_SCAN_REPORTS_BUCKET: str
    REDIS_URL: str
    SES_FROM_EMAIL: str
    SECRET_PREFIX: str
    WEBSOCKET_API_ENDPOINT: str

    class Config:
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

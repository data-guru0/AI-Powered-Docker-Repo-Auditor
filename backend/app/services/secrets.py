import json
from typing import Optional
from app.core.aws import get_secrets_client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def _secret_path(user_id: str, registry_type: str) -> str:
    return f"{settings.SECRET_PREFIX}/users/{user_id}/{registry_type}"


async def store_credential(user_id: str, registry_type: str, credential: dict) -> None:
    client = get_secrets_client()
    secret_id = _secret_path(user_id, registry_type)
    secret_value = json.dumps(credential)
    try:
        client.create_secret(
            Name=secret_id,
            SecretString=secret_value,
        )
    except client.exceptions.ResourceExistsException:
        client.put_secret_value(
            SecretId=secret_id,
            SecretString=secret_value,
        )


async def get_credential(user_id: str, registry_type: str) -> Optional[dict]:
    client = get_secrets_client()
    secret_id = _secret_path(user_id, registry_type)
    try:
        resp = client.get_secret_value(SecretId=secret_id)
        return json.loads(resp["SecretString"])
    except client.exceptions.ResourceNotFoundException:
        return None
    except Exception as exc:
        logger.error("Failed to retrieve credential: %s", exc)
        return None


async def delete_credential(user_id: str, registry_type: str) -> None:
    client = get_secrets_client()
    secret_id = _secret_path(user_id, registry_type)
    try:
        client.delete_secret(
            SecretId=secret_id,
            ForceDeleteWithoutRecovery=True,
        )
    except client.exceptions.ResourceNotFoundException:
        pass

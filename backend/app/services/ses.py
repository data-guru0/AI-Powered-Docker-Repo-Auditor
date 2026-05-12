from app.core.aws import get_ses_client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def send_scan_started_email(to_email: str, repo_id: str, job_id: str) -> None:
    client = get_ses_client()
    try:
        client.send_email(
            Source=settings.SES_FROM_EMAIL,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": f"Scan started: {repo_id}"},
                "Body": {
                    "Text": {
                        "Data": (
                            f"Your scan for {repo_id} has started.\n\n"
                            f"Job ID: {job_id}\n\n"
                            "You will receive another email when the scan completes."
                        )
                    }
                },
            },
        )
    except Exception as exc:
        logger.error("Failed to send scan started email to %s: %s", to_email, exc)


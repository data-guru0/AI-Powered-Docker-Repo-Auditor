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


async def send_scan_completed_email(
    to_email: str,
    repo_id: str,
    job_id: str,
    grade: str,
    cve_critical: int,
    cve_high: int,
    top_findings: list[str],
    dashboard_url: str,
) -> None:
    client = get_ses_client()
    findings_text = "\n".join(f"- {f}" for f in top_findings[:3])
    try:
        client.send_email(
            Source=settings.SES_FROM_EMAIL,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": f"Scan complete: {repo_id} — Grade {grade}"},
                "Body": {
                    "Text": {
                        "Data": (
                            f"Scan complete for {repo_id}\n\n"
                            f"Overall Grade: {grade}\n"
                            f"Critical CVEs: {cve_critical}\n"
                            f"High CVEs: {cve_high}\n\n"
                            f"Top Findings:\n{findings_text}\n\n"
                            f"View full report: {dashboard_url}"
                        )
                    }
                },
            },
        )
    except Exception as exc:
        logger.error("Failed to send scan completed email to %s: %s", to_email, exc)

import os
import logging

logger = logging.getLogger(__name__)


def setup_xray() -> None:
    """
    Configures AWS X-Ray SDK and patches boto3, httpx, and requests automatically.
    Only activates when AWS_XRAY_DAEMON_ADDRESS is set (ECS injects this when the
    X-Ray daemon sidecar is enabled on the task definition).
    """
    daemon_address = os.getenv("AWS_XRAY_DAEMON_ADDRESS")
    if not daemon_address:
        logger.info("AWS_XRAY_DAEMON_ADDRESS not set — X-Ray tracing disabled")
        return

    try:
        from aws_xray_sdk.core import xray_recorder, patch_all

        xray_recorder.configure(
            service="docker-auditor-worker",
            daemon_address=daemon_address,
            sampling=True,
            context_missing="LOG_ERROR",
        )
        patch_all()  # Auto-patches boto3, botocore, requests, httpx
        logger.info("AWS X-Ray SDK enabled, daemon: %s", daemon_address)
    except Exception as exc:
        logger.warning("X-Ray setup failed (non-fatal): %s", exc)

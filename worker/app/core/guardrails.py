import logging
from typing import Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Keywords that indicate a message is relevant to this platform
_DOCKER_TOPICS = {
    "docker", "container", "image", "cve", "vulnerability", "vuln",
    "security", "dockerfile", "kubernetes", "k8s", "ecr", "registry",
    "base image", "trivy", "scan", "compliance", "layer", "bloat",
    "exploit", "patch", "severity", "cvss", "finding", "aws", "cicd",
    "devops", "pillow", "cryptography", "django", "python", "package",
    "dependency", "port", "expose", "root", "user", "secret", "credential",
    "healthcheck", "cis", "benchmark", "grade", "score", "risk",
}

_MAX_INPUT_LENGTH = 2000


def _is_on_topic(text: str) -> tuple[bool, str]:
    if len(text) <= 40:
        return True, ""
    text_lower = text.lower()
    if any(topic in text_lower for topic in _DOCKER_TOPICS):
        return True, ""
    return (
        False,
        "I can only answer questions about container images, Docker security, CVEs, and scan results.",
    )


async def _run_moderation(text: str) -> tuple[bool, str]:
    try:
        client = AsyncOpenAI()
        response = await client.moderations.create(input=text)
        result = response.results[0]
        if result.flagged:
            flagged = [
                cat for cat, val in result.categories.model_dump().items() if val
            ]
            return False, f"Message blocked by content policy ({', '.join(flagged)})."
        return True, ""
    except Exception as exc:
        logger.warning("OpenAI moderation check failed (fail-open): %s", exc)
        return True, ""  # Fail open — never block users due to moderation API errors


async def validate_chat_input(message: str) -> Optional[str]:
    """
    Run all guardrail checks on a chat message.
    Returns a rejection reason string if blocked, None if allowed.
    """
    if not message.strip():
        return "Message cannot be empty."

    if len(message) > _MAX_INPUT_LENGTH:
        return f"Message too long. Please keep it under {_MAX_INPUT_LENGTH} characters."

    topic_ok, topic_reason = _is_on_topic(message)
    if not topic_ok:
        return topic_reason

    mod_ok, mod_reason = await _run_moderation(message)
    if not mod_ok:
        return mod_reason

    return None

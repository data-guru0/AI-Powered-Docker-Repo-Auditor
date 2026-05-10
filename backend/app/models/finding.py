from pydantic import BaseModel
from enum import Enum
from typing import Optional


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class FindingCategory(str, Enum):
    CVE = "cve"
    BLOAT = "bloat"
    BASE_IMAGE = "base_image"
    BEST_PRACTICE = "best_practice"
    COMPLIANCE = "compliance"
    SECRET = "secret"


class EffortLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Finding(BaseModel):
    id: str
    severity: SeverityLevel
    category: FindingCategory
    title: str
    detail: str
    evidence: str
    impact: str
    fix: str
    effort: EffortLevel
    agent: str
    imageId: Optional[str] = None

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ScanStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StartScanRequest(BaseModel):
    repo_id: str = Field(min_length=1)
    image_id: Optional[str] = None


class ScanJob(BaseModel):
    jobId: str
    repoId: str
    status: ScanStatus
    progress: int = 0
    currentStep: str = ""
    startedAt: str
    completedAt: Optional[str] = None
    error: Optional[str] = None


class Scores(BaseModel):
    security: int = Field(ge=0, le=100)
    bloat: int = Field(ge=0, le=100)
    freshness: int = Field(ge=0, le=100)
    bestPractices: int = Field(ge=0, le=100)
    overall: str


class TopAction(BaseModel):
    rank: int
    title: str
    impact: str
    effort: str


class DockerfileChange(BaseModel):
    lineNumber: int
    category: str
    what: str
    why: str
    estimatedSavings: Optional[str] = None


class CVECount(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class ScanResult(BaseModel):
    scanId: str
    repoId: str
    imageId: str
    scores: Scores
    findings: list = []
    dockerfileOriginal: str = ""
    dockerfileOptimized: str = ""
    dockerfileChanges: list[DockerfileChange] = []
    topActions: list[TopAction] = []
    executiveSummary: str = ""
    scanDate: str
    blocked: bool = False
    cveCount: CVECount = Field(default_factory=CVECount)
    totalSizeReduction: int = 0
    estimatedFixTime: int = 0


class ScoreHistory(BaseModel):
    date: str
    security: int
    bloat: int
    freshness: int
    bestPractices: int
    deployMarker: bool = False

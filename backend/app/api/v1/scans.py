from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user
from app.core.rate_limiter import scan_rate_limit
from app.models.scan import StartScanRequest, ScanJob, ScanResult, ScoreHistory
from app.services.queue import dispatch_scan_job
from app.services.dynamodb import get_latest_scan, get_scan_result, get_scan_history
from app.services.ses import send_scan_started_email
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ScanJob)
async def start_scan(
    request: StartScanRequest,
    user: dict = Depends(scan_rate_limit),
) -> ScanJob:
    job = await dispatch_scan_job(
        user["user_id"], request.repo_id, request.image_id, user["email"]
    )
    await send_scan_started_email(
        user["email"], request.repo_id, job.jobId
    )
    return job


@router.get("/latest/{repo_id}", response_model=ScanResult | None)
async def get_latest_scan_result(
    repo_id: str,
    user: dict = Depends(get_current_user),
) -> ScanResult | None:
    item = await get_latest_scan(user["user_id"], repo_id)
    if not item:
        return None
    return ScanResult(**item)


@router.get("/history/{repo_id}", response_model=list[ScoreHistory])
async def get_history(
    repo_id: str,
    user: dict = Depends(get_current_user),
) -> list[ScoreHistory]:
    items = await get_scan_history(user["user_id"], repo_id)
    return [
        ScoreHistory(
            date=item["scanDate"],
            security=item.get("scores", {}).get("security", 0),
            bloat=item.get("scores", {}).get("bloat", 0),
            freshness=item.get("scores", {}).get("freshness", 0),
            bestPractices=item.get("scores", {}).get("bestPractices", 0),
        )
        for item in items
    ]


@router.get("/{scan_id}", response_model=ScanResult)
async def get_scan(
    scan_id: str,
    user: dict = Depends(get_current_user),
) -> ScanResult:
    item = await get_scan_result(scan_id)
    if not item:
        raise HTTPException(status_code=404, detail="Scan not found")
    return ScanResult(**item)

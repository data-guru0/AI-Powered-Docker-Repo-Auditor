import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Optional
from app.agents.cve_analyst import run_cve_analyst
from app.agents.bloat_detective import run_bloat_detective
from app.agents.base_image_strategist import run_base_image_strategist
from app.agents.compliance_checker import run_compliance_checker
from app.agents.dockerfile_optimizer import run_dockerfile_optimizer
from app.agents.risk_scorer import run_risk_scorer
from app.scanners.trivy import run_trivy_scan
from app.scanners.inspector import run_inspector_scan
from app.processors.manifest import fetch_manifest
from app.processors.layer import fetch_layer_data
from app.processors.findings import merge_findings, deduplicate_findings
from app.services.dynamodb import (
    store_scan_result,
    get_previous_scan,
    update_job_status,
)
from app.services.s3 import upload_scan_report
from app.services.websocket import publish_progress
from app.services.ses import send_scan_completed_email
from app.services.eval import run_ragas_evaluation
from app.services.dynamodb import get_user_credentials
import logging

logger = logging.getLogger(__name__)


async def run_orchestrator(
    job_id: str,
    user_id: str,
    repo_id: str,
    image_id: Optional[str],
) -> None:
    scan_id = str(uuid.uuid4())
    scan_date = datetime.now(timezone.utc).isoformat()

    await publish_progress(job_id, "running", 10, "Fetching image manifest")
    await update_job_status(job_id, "running", 10, "Fetching image manifest")

    user_creds = await get_user_credentials(user_id)

    manifest = await fetch_manifest(repo_id, image_id, user_creds)

    await publish_progress(job_id, "running", 20, "Running Trivy scan")
    await update_job_status(job_id, "running", 20, "Running Trivy scan")

    trivy_results, inspector_results, layer_data = await asyncio.gather(
        run_trivy_scan(repo_id, image_id, user_creds),
        run_inspector_scan(repo_id, image_id, user_creds),
        fetch_layer_data(repo_id, image_id, user_creds),
    )

    await publish_progress(job_id, "running", 40, "Running AI agent analysis")
    await update_job_status(job_id, "running", 40, "Running AI agent analysis")

    previous_scan = await get_previous_scan(user_id, repo_id)

    cve_findings, bloat_findings, base_image_analysis, compliance_findings = await asyncio.gather(
        asyncio.wait_for(run_cve_analyst(trivy_results, inspector_results, previous_scan), timeout=120),
        asyncio.wait_for(run_bloat_detective(layer_data, manifest), timeout=120),
        asyncio.wait_for(run_base_image_strategist(manifest), timeout=120),
        asyncio.wait_for(run_compliance_checker(manifest, trivy_results), timeout=120),
        return_exceptions=True,
    )
    if isinstance(cve_findings, BaseException):
        logger.warning("CVE analyst failed/timed out: %s", cve_findings)
        cve_findings = []
    if isinstance(bloat_findings, BaseException):
        logger.warning("Bloat detective failed/timed out: %s", bloat_findings)
        bloat_findings = []
    if isinstance(base_image_analysis, BaseException):
        logger.warning("Base image strategist failed/timed out: %s", base_image_analysis)
        base_image_analysis = []
    if isinstance(compliance_findings, BaseException):
        logger.warning("Compliance checker failed/timed out: %s", compliance_findings)
        compliance_findings = []

    await publish_progress(job_id, "running", 65, "Optimizing Dockerfile")
    await update_job_status(job_id, "running", 65, "Optimizing Dockerfile")

    try:
        dockerfile_result = await asyncio.wait_for(
            run_dockerfile_optimizer(manifest, cve_findings, bloat_findings, base_image_analysis),
            timeout=120,
        )
    except asyncio.TimeoutError:
        logger.warning("Dockerfile optimizer timed out for job %s, using empty result", job_id)
        dockerfile_result = {"original": "", "optimized": "", "changes": []}

    await publish_progress(job_id, "running", 80, "Calculating risk scores")
    await update_job_status(job_id, "running", 80, "Calculating risk scores")

    all_findings = merge_findings(cve_findings, bloat_findings, base_image_analysis, compliance_findings)
    all_findings = deduplicate_findings(all_findings)

    try:
        risk_result = await asyncio.wait_for(
            run_risk_scorer(cve_findings, bloat_findings, base_image_analysis, all_findings, previous_scan),
            timeout=120,
        )
    except asyncio.TimeoutError:
        logger.warning("Risk scorer timed out for job %s, using default scores", job_id)
        risk_result = {
            "scores": {"security": 50, "bloat": 50, "freshness": 50, "bestPractices": 50, "overall": "C"},
            "topActions": [],
            "executiveSummary": "Risk scoring timed out.",
            "blocked": False,
        }

    await publish_progress(job_id, "running", 90, "Storing results")
    await update_job_status(job_id, "running", 90, "Storing results")

    cve_count = {
        "critical": sum(1 for f in all_findings if f.get("severity") == "critical" and f.get("category") == "cve"),
        "high": sum(1 for f in all_findings if f.get("severity") == "high" and f.get("category") == "cve"),
        "medium": sum(1 for f in all_findings if f.get("severity") == "medium" and f.get("category") == "cve"),
        "low": sum(1 for f in all_findings if f.get("severity") == "low" and f.get("category") == "cve"),
    }

    scan_record = {
        "scanId": scan_id,
        "job_id": job_id,
        "user_id": user_id,
        "repoId": repo_id,
        "imageId": image_id or "",
        "scores": risk_result["scores"],
        "findings": all_findings,
        "dockerfileOriginal": dockerfile_result["original"],
        "dockerfileOptimized": dockerfile_result["optimized"],
        "dockerfileChanges": dockerfile_result["changes"],
        "topActions": risk_result["topActions"],
        "executiveSummary": risk_result["executiveSummary"],
        "scanDate": scan_date,
        "blocked": risk_result.get("blocked", False),
        "cveCount": cve_count,
        "totalSizeReduction": sum(
            f.get("sizeImpact", 0) for f in bloat_findings
        ),
        "estimatedFixTime": len(all_findings) * 2,
    }

    await asyncio.gather(
        store_scan_result(job_id, scan_record),
        upload_scan_report(scan_id, scan_record),
    )

    await publish_progress(job_id, "running", 95, "Running Ragas evaluation")
    await update_job_status(job_id, "running", 95, "Running Ragas evaluation")

    asyncio.create_task(
        run_ragas_evaluation(
            user_id, repo_id, scan_id,
            {
                "cve": cve_findings,
                "bloat": bloat_findings,
                "base_image": base_image_analysis,
                "risk": risk_result,
                "dockerfile": dockerfile_result,
            }
        )
    )

    await update_job_status(job_id, "completed", 100, "Scan complete")
    await publish_progress(job_id, "completed", 100, "Scan complete")

    user_info = await get_user_credentials(user_id)
    if user_info.get("email"):
        top_findings = [f.get("title", "") for f in all_findings[:3]]
        await send_scan_completed_email(
            user_info["email"],
            repo_id,
            job_id,
            risk_result["scores"]["overall"],
            cve_count["critical"],
            cve_count["high"],
            top_findings,
            f"{user_info.get('frontend_url', '')}/dashboard/repo/{repo_id}",
        )

    logger.info("Scan job %s completed with scan_id %s", job_id, scan_id)

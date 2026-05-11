import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Optional
from opentelemetry import trace as otel_trace
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
from app.services.dynamodb import get_user_credentials
import app.core.telemetry as tel
import logging

logger = logging.getLogger(__name__)

_tracer = otel_trace.get_tracer("docker-auditor.orchestrator")


async def _timed(coro, agent_name: str):
    t = time.perf_counter()
    try:
        return await coro
    finally:
        if tel.agent_duration:
            tel.agent_duration.record(time.perf_counter() - t, {"agent": agent_name})


async def run_orchestrator(
    job_id: str,
    user_id: str,
    repo_id: str,
    image_id: Optional[str],
) -> None:
    if tel.scans_started:
        tel.scans_started.add(1)

    _start = time.perf_counter()

    with _tracer.start_as_current_span(
        "scan.job",
        attributes={"job_id": job_id, "repo_id": repo_id},
    ) as _span:
        try:
            await _orchestrate(job_id, user_id, repo_id, image_id, _span)
            if tel.scans_completed:
                tel.scans_completed.add(1)
        except Exception as exc:
            from opentelemetry.trace import StatusCode
            _span.set_status(StatusCode.ERROR, str(exc))
            _span.record_exception(exc)
            if tel.scans_failed:
                tel.scans_failed.add(1)
            raise
        finally:
            if tel.scan_duration:
                tel.scan_duration.record(time.perf_counter() - _start, {"repo_id": repo_id})


async def _orchestrate(job_id, user_id, repo_id, image_id, span) -> None:
    scan_id = str(uuid.uuid4())
    scan_date = datetime.now(timezone.utc).isoformat()

    await publish_progress(job_id, "running", 10, "Fetching image manifest")
    await update_job_status(job_id, "running", 10, "Fetching image manifest")

    with _tracer.start_as_current_span("fetch.manifest"):
        user_creds = await get_user_credentials(user_id)
        manifest = await fetch_manifest(repo_id, image_id, user_creds)

    await publish_progress(job_id, "running", 20, "Running Trivy scan")
    await update_job_status(job_id, "running", 20, "Running Trivy scan")

    t_scan = time.perf_counter()
    with _tracer.start_as_current_span("scanners"):
        trivy_results, inspector_results, layer_data = await asyncio.gather(
            run_trivy_scan(repo_id, image_id, user_creds),
            run_inspector_scan(repo_id, image_id, user_creds),
            fetch_layer_data(repo_id, image_id, user_creds),
        )
    if tel.agent_duration:
        tel.agent_duration.record(time.perf_counter() - t_scan, {"agent": "scanners"})

    await publish_progress(job_id, "running", 40, "Running AI agent analysis")
    await update_job_status(job_id, "running", 40, "Running AI agent analysis")

    previous_scan = await get_previous_scan(user_id, repo_id)

    with _tracer.start_as_current_span("agents.parallel"):
        cve_findings, bloat_findings, base_image_analysis, compliance_findings = await asyncio.gather(
            asyncio.wait_for(_timed(run_cve_analyst(trivy_results, inspector_results, previous_scan), "cve_analyst"), timeout=120),
            asyncio.wait_for(_timed(run_bloat_detective(layer_data, manifest), "bloat_detective"), timeout=120),
            asyncio.wait_for(_timed(run_base_image_strategist(manifest), "base_image_strategist"), timeout=120),
            asyncio.wait_for(_timed(run_compliance_checker(manifest, trivy_results), "compliance_checker"), timeout=120),
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
        with _tracer.start_as_current_span("agent.dockerfile_optimizer"):
            dockerfile_result = await asyncio.wait_for(
                _timed(run_dockerfile_optimizer(manifest, cve_findings, bloat_findings, base_image_analysis), "dockerfile_optimizer"),
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
        with _tracer.start_as_current_span("agent.risk_scorer"):
            risk_result = await asyncio.wait_for(
                _timed(run_risk_scorer(cve_findings, bloat_findings, base_image_analysis, all_findings, previous_scan), "risk_scorer"),
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

    span.set_attribute("cve.critical", cve_count["critical"])
    span.set_attribute("cve.high", cve_count["high"])
    span.set_attribute("findings.total", len(all_findings))

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

    await update_job_status(job_id, "completed", 100, "Scan complete")
    await publish_progress(job_id, "completed", 100, "Scan complete")

    user_info = await get_user_credentials(user_id)
    if user_info.get("email"):
        await send_scan_completed_email(
            user_info["email"],
            repo_id,
            job_id,
            risk_result["scores"],
            cve_count,
            risk_result.get("executiveSummary", ""),
            risk_result.get("topActions", []),
            len(all_findings),
            f"{user_info.get('frontend_url', '')}/dashboard/repo/{repo_id}",
        )

    logger.info("Scan job %s completed with scan_id %s", job_id, scan_id)

import uuid
from typing import Any


def merge_findings(*finding_lists: list[dict]) -> list[dict]:
    merged: list[dict] = []
    for findings in finding_lists:
        if isinstance(findings, list):
            merged.extend(findings)
        elif isinstance(findings, dict):
            values = list(findings.values())
            for v in values:
                if isinstance(v, list):
                    merged.extend(v)
    return merged


def deduplicate_findings(findings: list[dict]) -> list[dict]:
    seen_titles: set[str] = set()
    unique: list[dict] = []
    for f in findings:
        title = f.get("title", "")
        key = f"{f.get('category', '')}-{title}"
        if key not in seen_titles:
            seen_titles.add(key)
            if not f.get("id"):
                f["id"] = str(uuid.uuid4())
            unique.append(f)
    return unique


def normalize_severity(severity: str) -> str:
    mapping = {
        "CRITICAL": "critical",
        "HIGH": "high",
        "MEDIUM": "medium",
        "LOW": "low",
        "UNKNOWN": "informational",
        "NEGLIGIBLE": "informational",
    }
    return mapping.get(severity.upper(), severity.lower())


def normalize_trivy_findings(trivy_data: dict, image_id: str) -> list[dict]:
    findings: list[dict] = []
    for result in trivy_data.get("Results", []):
        for vuln in result.get("Vulnerabilities", []):
            findings.append(
                {
                    "id": str(uuid.uuid4()),
                    "severity": normalize_severity(vuln.get("Severity", "unknown")),
                    "category": "cve",
                    "title": vuln.get("VulnerabilityID", "Unknown CVE"),
                    "detail": vuln.get("Description", ""),
                    "evidence": f"{vuln.get('PkgName', '')} {vuln.get('InstalledVersion', '')}",
                    "impact": vuln.get("Description", ""),
                    "fix": vuln.get("FixedVersion", "No fix available"),
                    "effort": "medium",
                    "agent": "trivy",
                    "imageId": image_id,
                    "cvssScore": vuln.get("CVSS", {}).get("nvd", {}).get("V3Score", 0.0),
                }
            )
    return findings

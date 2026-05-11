from app.core.aws import get_ses_client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_GRADE_COLOR = {
    "A+": "#00d4ff", "A": "#00d4ff", "A-": "#00d4ff",
    "B+": "#22c55e", "B": "#22c55e", "B-": "#22c55e",
    "C+": "#f97316", "C": "#f97316", "C-": "#f97316",
    "D": "#ef4444", "F": "#ef4444",
}
_SCORE_BAR_COLOR = {
    "security": "#ef4444",
    "bloat": "#f97316",
    "freshness": "#00d4ff",
    "bestPractices": "#8b5cf6",
}
_SCORE_LABEL = {
    "security": "Security",
    "bloat": "Bloat",
    "freshness": "Freshness",
    "bestPractices": "Best Practices",
}


def _score_bar(label: str, score: int) -> str:
    color = _SCORE_BAR_COLOR.get(label, "#94a3b8")
    pct = max(0, min(100, score))
    return f"""
    <td style="padding:0 8px;width:25%;vertical-align:top;">
      <div style="background:#1e293b;border-radius:8px;padding:12px;text-align:center;">
        <div style="font-size:22px;font-weight:700;color:{color};font-family:monospace;">{score}</div>
        <div style="font-size:10px;color:#94a3b8;margin-top:2px;text-transform:uppercase;letter-spacing:.05em;">{_SCORE_LABEL.get(label, label)}</div>
        <div style="margin-top:6px;height:4px;background:#334155;border-radius:2px;overflow:hidden;">
          <div style="height:4px;width:{pct}%;background:{color};border-radius:2px;"></div>
        </div>
      </div>
    </td>"""


def _cve_badge(count: int, label: str, color: str) -> str:
    if count == 0:
        return ""
    return (
        f'<span style="display:inline-block;background:{color}22;color:{color};'
        f'border:1px solid {color}44;border-radius:4px;padding:2px 8px;'
        f'font-size:12px;font-weight:600;margin-right:6px;">{count} {label}</span>'
    )


def _build_html(
    repo_id: str,
    scores: dict,
    cve_count: dict,
    executive_summary: str,
    top_actions: list,
    total_findings: int,
    dashboard_url: str,
) -> str:
    grade = scores.get("overall", "?")
    grade_color = _GRADE_COLOR.get(grade, "#94a3b8")

    score_cells = "".join(
        _score_bar(k, scores.get(k, 0))
        for k in ("security", "bloat", "freshness", "bestPractices")
    )

    cve_badges = (
        _cve_badge(cve_count.get("critical", 0), "Critical", "#ef4444")
        + _cve_badge(cve_count.get("high", 0), "High", "#f97316")
        + _cve_badge(cve_count.get("medium", 0), "Medium", "#eab308")
        + _cve_badge(cve_count.get("low", 0), "Low", "#22c55e")
    )
    total_cve = sum(cve_count.get(k, 0) for k in ("critical", "high", "medium", "low"))

    action_rows = ""
    for i, action in enumerate(top_actions[:5], 1):
        title = action.get("title", "") if isinstance(action, dict) else str(action)
        desc = action.get("description", "") if isinstance(action, dict) else ""
        action_rows += f"""
        <tr>
          <td style="padding:10px 0;border-bottom:1px solid #1e293b;vertical-align:top;">
            <div style="color:#00d4ff;font-size:11px;font-weight:700;margin-bottom:2px;">
              #{i}
            </div>
            <div style="color:#e2e8f0;font-size:13px;font-weight:600;">{title}</div>
            {"<div style='color:#94a3b8;font-size:12px;margin-top:2px;'>"+desc+"</div>" if desc else ""}
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Scan Report: {repo_id}</title></head>
<body style="margin:0;padding:0;background:#0f172a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0f172a;padding:32px 16px;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

      <!-- Header -->
      <tr>
        <td style="background:#0a0f1e;border:1px solid #1e293b;border-radius:12px 12px 0 0;padding:28px 32px;">
          <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px;">Docker Image Scan Report</div>
          <div style="font-size:22px;font-weight:700;color:#e2e8f0;font-family:monospace;">{repo_id}</div>
        </td>
      </tr>

      <!-- Grade -->
      <tr>
        <td style="background:#0d1526;border-left:1px solid #1e293b;border-right:1px solid #1e293b;padding:24px 32px;text-align:center;">
          <div style="display:inline-block;background:{grade_color}18;border:2px solid {grade_color};border-radius:50%;width:72px;height:72px;line-height:72px;font-size:36px;font-weight:800;color:{grade_color};font-family:monospace;">{grade}</div>
          <div style="font-size:12px;color:#94a3b8;margin-top:8px;">Overall Health Grade</div>
          {f'<div style="margin-top:12px;padding:12px 16px;background:#1e293b;border-radius:8px;font-size:13px;color:#cbd5e1;line-height:1.5;">{executive_summary}</div>' if executive_summary else ""}
        </td>
      </tr>

      <!-- Score breakdown -->
      <tr>
        <td style="background:#0a0f1e;border-left:1px solid #1e293b;border-right:1px solid #1e293b;padding:16px 32px;">
          <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px;">Score Breakdown</div>
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>{score_cells}</tr>
          </table>
        </td>
      </tr>

      <!-- CVE Summary -->
      <tr>
        <td style="background:#0d1526;border-left:1px solid #1e293b;border-right:1px solid #1e293b;padding:16px 32px;">
          <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px;">
            Vulnerability Summary &mdash; {total_cve} CVE{'' if total_cve == 1 else 's'} detected
          </div>
          <div>{cve_badges if cve_badges else '<span style="color:#22c55e;font-size:13px;font-weight:600;">&#10003; No CVEs detected</span>'}</div>
          <div style="margin-top:8px;font-size:12px;color:#94a3b8;">Total findings: {total_findings}</div>
        </td>
      </tr>

      <!-- Top Actions -->
      {f"""<tr>
        <td style="background:#0a0f1e;border-left:1px solid #1e293b;border-right:1px solid #1e293b;padding:16px 32px;">
          <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;">Top Recommendations</div>
          <table width="100%" cellpadding="0" cellspacing="0">{action_rows}</table>
        </td>
      </tr>""" if top_actions else ""}

      <!-- CTA -->
      <tr>
        <td style="background:#0d1526;border:1px solid #1e293b;border-top:none;border-radius:0 0 12px 12px;padding:24px 32px;text-align:center;">
          <a href="{dashboard_url}"
             style="display:inline-block;background:#00d4ff;color:#0a0f1e;font-weight:700;font-size:14px;
                    padding:12px 28px;border-radius:8px;text-decoration:none;letter-spacing:.02em;">
            View Full Report &rarr;
          </a>
          <div style="margin-top:16px;font-size:11px;color:#475569;">
            This report was generated automatically by EvolVue &bull; Do not reply to this email
          </div>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""


def _build_plain(
    repo_id: str,
    scores: dict,
    cve_count: dict,
    executive_summary: str,
    top_actions: list,
    total_findings: int,
    dashboard_url: str,
) -> str:
    grade = scores.get("overall", "?")
    lines = [
        f"Docker Image Scan Report — {repo_id}",
        "=" * 50,
        f"Overall Grade: {grade}",
        "",
    ]
    if executive_summary:
        lines += [executive_summary, ""]

    lines += [
        "SCORES",
        f"  Security:      {scores.get('security', 0)}",
        f"  Bloat:         {scores.get('bloat', 0)}",
        f"  Freshness:     {scores.get('freshness', 0)}",
        f"  Best Practices:{scores.get('bestPractices', 0)}",
        "",
        "VULNERABILITIES",
        f"  Critical: {cve_count.get('critical', 0)}",
        f"  High:     {cve_count.get('high', 0)}",
        f"  Medium:   {cve_count.get('medium', 0)}",
        f"  Low:      {cve_count.get('low', 0)}",
        f"  Total findings: {total_findings}",
        "",
    ]

    if top_actions:
        lines.append("TOP RECOMMENDATIONS")
        for i, a in enumerate(top_actions[:5], 1):
            title = a.get("title", "") if isinstance(a, dict) else str(a)
            lines.append(f"  {i}. {title}")
        lines.append("")

    lines += [f"View full report: {dashboard_url}", ""]
    return "\n".join(lines)


async def send_scan_completed_email(
    to_email: str,
    repo_id: str,
    job_id: str,
    scores: dict,
    cve_count: dict,
    executive_summary: str,
    top_actions: list,
    total_findings: int,
    dashboard_url: str,
) -> None:
    if not to_email or not settings.SES_FROM_EMAIL:
        return

    grade = scores.get("overall", "?")
    crit = cve_count.get("critical", 0)
    subject = (
        f"[⚠️ ACTION REQUIRED] {repo_id} — {crit} critical CVEs | Grade {grade}"
        if crit > 0
        else f"Scan complete: {repo_id} | Grade {grade}"
    )

    html_body = _build_html(repo_id, scores, cve_count, executive_summary, top_actions, total_findings, dashboard_url)
    text_body = _build_plain(repo_id, scores, cve_count, executive_summary, top_actions, total_findings, dashboard_url)

    client = get_ses_client()
    try:
        client.send_email(
            Source=settings.SES_FROM_EMAIL,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {
                    "Html": {"Data": html_body, "Charset": "UTF-8"},
                    "Text": {"Data": text_body, "Charset": "UTF-8"},
                },
            },
        )
        logger.info("Sent scan report email to %s for repo %s (job %s)", to_email, repo_id, job_id)
    except Exception as exc:
        logger.error("Failed to send scan email to %s: %s", to_email, exc)

"use client";

import type { ScanResult, SeverityLevel } from "@/types/scan";

interface CVEListCardProps {
  scan: ScanResult | null;
}

const SEVERITY_ORDER: Record<SeverityLevel, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  informational: 4,
};

const SEVERITY_LABEL: Record<SeverityLevel, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
  informational: "Info",
};

export function CVEListCard({ scan }: CVEListCardProps) {
  const cves = (scan?.findings ?? [])
    .filter((f) => f.category === "cve")
    .sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]);

  const counts = {
    critical: cves.filter((f) => f.severity === "critical").length,
    high: cves.filter((f) => f.severity === "high").length,
    medium: cves.filter((f) => f.severity === "medium").length,
    low: cves.filter((f) => f.severity === "low").length,
  };

  return (
    <div className="bg-bg-card border border-surface-border rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-surface-border flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-text-primary">Detected CVEs</h2>
          <p className="text-text-secondary text-xs mt-0.5">
            {cves.length} vulnerabilities found in this image
          </p>
        </div>
        <div className="flex items-center gap-2">
          {counts.critical > 0 && (
            <span className="severity-badge-critical px-2 py-0.5 rounded text-xs font-medium">
              {counts.critical} Critical
            </span>
          )}
          {counts.high > 0 && (
            <span className="severity-badge-high px-2 py-0.5 rounded text-xs font-medium">
              {counts.high} High
            </span>
          )}
          {counts.medium > 0 && (
            <span className="severity-badge-medium px-2 py-0.5 rounded text-xs font-medium">
              {counts.medium} Medium
            </span>
          )}
          {counts.low > 0 && (
            <span className="severity-badge-low px-2 py-0.5 rounded text-xs font-medium">
              {counts.low} Low
            </span>
          )}
        </div>
      </div>

      {cves.length === 0 ? (
        <div className="px-5 py-10 text-center">
          <p className="text-accent-green text-sm font-medium">No CVEs detected</p>
          <p className="text-text-muted text-xs mt-1">This image has no known vulnerabilities</p>
        </div>
      ) : (
        <div className="divide-y divide-surface-border max-h-80 overflow-y-auto">
          {cves.map((cve) => (
            <div key={cve.id} className="px-5 py-3 flex items-start gap-3 hover:bg-bg-elevated transition-colors">
              <span
                className={`shrink-0 mt-0.5 px-2 py-0.5 rounded text-xs font-medium capitalize severity-badge-${cve.severity}`}
              >
                {SEVERITY_LABEL[cve.severity]}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-text-primary font-mono truncate">{cve.title}</p>
                {cve.evidence && (
                  <p className="text-xs text-text-muted mt-0.5 truncate">{cve.evidence}</p>
                )}
              </div>
              {cve.fix && (
                <p className="shrink-0 text-xs text-accent-cyan hidden sm:block max-w-40 truncate">
                  {cve.fix}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

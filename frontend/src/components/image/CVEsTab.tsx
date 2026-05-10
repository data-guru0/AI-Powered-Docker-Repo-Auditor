"use client";

import { useState } from "react";
import type { Finding } from "@/types/scan";

interface CVEsTabProps {
  findings: Finding[];
  repoId: string;
  imageId: string;
}

export function CVEsTab({ findings }: CVEsTabProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (findings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-3">
        <div className="w-12 h-12 rounded-full bg-accent-green/10 border border-accent-green/30 flex items-center justify-center">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M4 10l4 4 8-8" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <p className="text-text-primary font-medium">No CVEs detected</p>
        <p className="text-text-secondary text-sm">This image is clean</p>
      </div>
    );
  }

  const severityOrder: Record<string, number> = {
    critical: 0,
    high: 1,
    medium: 2,
    low: 3,
    informational: 4,
  };

  const sorted = [...findings].sort(
    (a, b) => severityOrder[a.severity] - severityOrder[b.severity]
  );

  const severityBadge: Record<string, string> = {
    critical: "severity-badge-critical",
    high: "severity-badge-high",
    medium: "severity-badge-medium",
    low: "severity-badge-low",
    informational: "severity-badge-informational",
  };

  return (
    <div className="space-y-2 max-w-4xl">
      <div className="flex items-center gap-4 mb-4 text-sm text-text-secondary">
        <span>{findings.filter((f) => f.severity === "critical").length} critical</span>
        <span>{findings.filter((f) => f.severity === "high").length} high</span>
        <span>{findings.filter((f) => f.severity === "medium").length} medium</span>
        <span>{findings.filter((f) => f.severity === "low").length} low</span>
      </div>
      {sorted.map((finding) => (
        <div
          key={finding.id}
          className="bg-bg-card border border-surface-border rounded-xl overflow-hidden"
        >
          <button
            onClick={() =>
              setExpandedId(expandedId === finding.id ? null : finding.id)
            }
            className="w-full text-left px-4 py-3.5 flex items-start gap-4 hover:bg-bg-elevated transition-colors"
          >
            <span className={`shrink-0 px-2 py-0.5 rounded text-xs font-medium ${severityBadge[finding.severity]}`}>
              {finding.severity}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-mono text-text-primary">{finding.title}</p>
              <p className="text-xs text-text-secondary mt-0.5 truncate">
                {finding.detail}
              </p>
            </div>
            <svg
              width={14}
              height={14}
              viewBox="0 0 14 14"
              fill="none"
              className={`shrink-0 text-text-muted mt-1 transition-transform ${expandedId === finding.id ? "rotate-180" : ""}`}
            >
              <path d="M3 5l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
          {expandedId === finding.id && (
            <div className="px-4 pb-4 pt-0 bg-bg-elevated border-t border-surface-border">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 text-xs">
                <div>
                  <p className="text-text-muted mb-1">Evidence</p>
                  <p className="text-text-secondary">{finding.evidence}</p>
                </div>
                <div>
                  <p className="text-text-muted mb-1">Exploitability Reasoning</p>
                  <p className="text-text-secondary">{finding.impact}</p>
                </div>
                <div>
                  <p className="text-text-muted mb-1">Fix</p>
                  <p className="text-accent-green font-mono">{finding.fix}</p>
                </div>
                <div>
                  <p className="text-text-muted mb-1">Effort</p>
                  <p className="text-text-secondary capitalize">{finding.effort}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

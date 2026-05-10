"use client";

import type { ScanResult } from "@/types/scan";

interface ComplianceStatusCardProps {
  scan: ScanResult | null;
}

export function ComplianceStatusCard({ scan }: ComplianceStatusCardProps) {
  const complianceFindings = scan?.findings.filter(
    (f) => f.category === "compliance"
  ) || [];

  const passing = complianceFindings.filter(
    (f) => f.severity === "informational"
  ).length;
  const failing = complianceFindings.filter(
    (f) => f.severity !== "informational"
  ).length;
  const total = passing + failing;
  const score = total > 0 ? Math.round((passing / total) * 100) : 100;

  return (
    <div className="bg-bg-card border border-surface-border rounded-xl p-4 card-hover">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">
        CIS Docker Benchmark
      </h3>
      <div className="flex items-center gap-3 mb-3">
        <p
          className="text-3xl font-bold font-mono"
          style={{
            color: score >= 80 ? "#10b981" : score >= 60 ? "#eab308" : "#ef4444",
          }}
        >
          {score}%
        </p>
        <p className="text-xs text-text-secondary">compliance</p>
      </div>
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs">
          <span className="text-accent-green">Passing</span>
          <span className="text-accent-green font-semibold">{passing}</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-accent-red">Failing</span>
          <span className="text-accent-red font-semibold">{failing}</span>
        </div>
      </div>
    </div>
  );
}

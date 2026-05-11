"use client";

import type { ScanResult } from "@/types/scan";

interface ComplianceDetailsCardProps {
  scan: ScanResult | null;
}

export function ComplianceDetailsCard({ scan }: ComplianceDetailsCardProps) {
  const findings = scan?.findings.filter((f) => f.category === "compliance") ?? [];
  const passing = findings.filter((f) => f.severity === "informational");
  const failing = findings.filter((f) => f.severity !== "informational");

  if (findings.length === 0) {
    return (
      <div className="bg-bg-card border border-surface-border rounded-xl p-4 card-hover">
        <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">
          CIS Compliance Details
        </h3>
        <p className="text-xs text-text-muted text-center py-6">No compliance data available</p>
      </div>
    );
  }

  return (
    <div className="bg-bg-card border border-surface-border rounded-xl p-4 card-hover">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider">
          CIS Compliance Details
        </h3>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-accent-green font-semibold">{passing.length} pass</span>
          <span className="text-text-muted">/</span>
          <span className="text-accent-red font-semibold">{failing.length} fail</span>
        </div>
      </div>

      <div className="space-y-3 max-h-52 overflow-y-auto pr-1 scrollbar-thin">
        {failing.length > 0 && (
          <div>
            <p className="text-xs text-accent-red font-medium mb-1.5 flex items-center gap-1">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-accent-red" />
              Failing ({failing.length})
            </p>
            <div className="space-y-1">
              {failing.map((f) => (
                <div
                  key={f.id}
                  className="flex items-start gap-2 px-2 py-1.5 rounded-lg bg-accent-red/5 border border-accent-red/10"
                >
                  <span className="shrink-0 mt-0.5 text-accent-red">✗</span>
                  <span className="text-xs text-text-primary leading-snug">{f.title}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {passing.length > 0 && (
          <div>
            <p className="text-xs text-accent-green font-medium mb-1.5 flex items-center gap-1">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-accent-green" />
              Passing ({passing.length})
            </p>
            <div className="space-y-1">
              {passing.map((f) => (
                <div
                  key={f.id}
                  className="flex items-start gap-2 px-2 py-1.5 rounded-lg bg-accent-green/5 border border-accent-green/10"
                >
                  <span className="shrink-0 mt-0.5 text-accent-green">✓</span>
                  <span className="text-xs text-text-primary leading-snug">{f.title}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

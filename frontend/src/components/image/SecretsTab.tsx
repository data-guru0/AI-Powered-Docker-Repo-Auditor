"use client";

import { useEffect, useState } from "react";
import { scansApi } from "@/lib/api";
import type { ScanResult } from "@/types/scan";

interface SecretsTabProps {
  repoId: string;
  imageId: string;
}

export function SecretsTab({ repoId, imageId }: SecretsTabProps) {
  const [scan, setScan] = useState<ScanResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    scansApi.getLatestScan(repoId).then(setScan).catch(() => {}).finally(() => setLoading(false));
  }, [repoId]);

  const secretFindings = scan?.findings.filter(
    (f) => f.category === "secret" && f.imageId === imageId
  ) || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="w-5 h-5 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (secretFindings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-3">
        <div className="w-12 h-12 rounded-full bg-accent-green/10 border border-accent-green/30 flex items-center justify-center">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M4 10l4 4 8-8" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <p className="text-text-primary font-medium">No secrets detected</p>
        <p className="text-text-secondary text-sm">
          No credentials found in image layers
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3 max-w-3xl">
      <div className="p-3 rounded-lg bg-severity-critical/10 border border-severity-critical/30 text-severity-critical text-sm">
        {secretFindings.length} secret{secretFindings.length !== 1 ? "s" : ""} detected. Rotate credentials immediately.
      </div>
      {secretFindings.map((finding) => (
        <div
          key={finding.id}
          className="bg-bg-card border border-severity-critical/30 rounded-xl p-4"
        >
          <div className="flex items-start gap-3">
            <span className="px-2 py-0.5 rounded text-xs font-medium severity-badge-critical">
              Secret
            </span>
            <div>
              <p className="text-sm font-medium text-text-primary">{finding.title}</p>
              <p className="text-xs text-text-secondary mt-1">{finding.evidence}</p>
              <p className="text-xs text-text-muted mt-2">Fix: {finding.fix}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

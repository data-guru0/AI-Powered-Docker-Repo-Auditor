"use client";

import type { ScanResult } from "@/types/scan";

interface BaseImageHealthCardProps {
  scan: ScanResult | null;
}

export function BaseImageHealthCard({ scan }: BaseImageHealthCardProps) {
  const baseImageFinding = scan?.findings.find(
    (f) => f.category === "base_image"
  );

  return (
    <div className="bg-bg-card border border-surface-border rounded-xl p-4 card-hover">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">
        Base Image Health
      </h3>
      {!scan ? (
        <div className="py-6 text-center text-text-muted text-xs">
          No scan data yet
        </div>
      ) : baseImageFinding ? (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-accent-orange" />
            <span className="text-xs text-accent-orange font-medium">
              Action required
            </span>
          </div>
          <p className="text-xs text-text-secondary leading-relaxed">
            {baseImageFinding.title}
          </p>
          <p className="text-xs text-text-muted">{baseImageFinding.fix}</p>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-accent-green" />
            <span className="text-xs text-accent-green font-medium">
              Up to date
            </span>
          </div>
          <p className="text-xs text-text-secondary">
            Base image is current and healthy
          </p>
        </div>
      )}
    </div>
  );
}

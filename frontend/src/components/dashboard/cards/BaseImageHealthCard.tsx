"use client";

import { useEffect, useState } from "react";
import { scansApi } from "@/lib/api";
import type { ScanResult } from "@/types/scan";

interface BaseImageHealthCardProps {
  repoId: string;
}

export function BaseImageHealthCard({ repoId }: BaseImageHealthCardProps) {
  const [scan, setScan] = useState<ScanResult | null>(null);

  useEffect(() => {
    scansApi.getLatestScan(repoId).then(setScan).catch(() => {});
  }, [repoId]);

  const baseImageFinding = scan?.findings.find(
    (f) => f.category === "base_image"
  );

  return (
    <div className="bg-bg-card border border-surface-border rounded-xl p-4 card-hover">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">
        Base Image Health
      </h3>
      {!scan ? (
        <div className="h-24 flex items-center justify-center">
          <div className="w-4 h-4 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="space-y-3">
          {baseImageFinding ? (
            <>
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
            </>
          ) : (
            <>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent-green" />
                <span className="text-xs text-accent-green font-medium">
                  Up to date
                </span>
              </div>
              <p className="text-xs text-text-secondary">
                Base image is current and healthy
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}

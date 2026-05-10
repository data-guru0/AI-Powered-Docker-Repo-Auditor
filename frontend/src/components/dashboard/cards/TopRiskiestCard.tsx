"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { imagesApi, scansApi } from "@/lib/api";
import type { ImageTag } from "@/types/registry";
import type { ScanResult } from "@/types/scan";

interface TopRiskiestCardProps {
  repoId: string;
}

export function TopRiskiestCard({ repoId }: TopRiskiestCardProps) {
  const [images, setImages] = useState<ImageTag[]>([]);
  const [scan, setScan] = useState<ScanResult | null>(null);

  useEffect(() => {
    Promise.all([
      imagesApi.list(repoId),
      scansApi.getLatestScan(repoId),
    ]).then(([imgs, s]) => {
      setImages(imgs);
      setScan(s);
    }).catch(() => {});
  }, [repoId]);

  const riskiest = images
    .map((img) => {
      const cves = scan?.findings.filter(
        (f) => f.imageId === img.id && f.category === "cve" && f.severity === "critical"
      ).length || 0;
      return { img, cves };
    })
    .filter((r) => r.cves > 0)
    .sort((a, b) => b.cves - a.cves)
    .slice(0, 5);

  return (
    <div className="bg-bg-card border border-surface-border rounded-xl p-4 card-hover">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">
        Top 5 Riskiest Images
      </h3>
      {riskiest.length === 0 ? (
        <div className="py-6 text-center text-text-muted text-xs">
          No critical CVEs detected
        </div>
      ) : (
        <div className="space-y-2">
          {riskiest.map(({ img, cves }, i) => (
            <Link
              key={img.id}
              href={`/dashboard/repo/${repoId}/image/${img.id}`}
              className="flex items-center gap-3 hover:bg-bg-elevated rounded-lg px-2 py-1.5 transition-colors"
            >
              <span className="text-xs text-text-muted w-4 text-center">
                {i + 1}
              </span>
              <span className="text-xs font-mono text-text-primary truncate flex-1">
                :{img.tag}
              </span>
              <span className="shrink-0 px-2 py-0.5 rounded text-xs bg-severity-critical/10 text-severity-critical border border-severity-critical/20">
                {cves} critical
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

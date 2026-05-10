"use client";

import { useEffect, useState } from "react";
import { imagesApi } from "@/lib/api";
import type { ImageTag } from "@/types/registry";

interface UnusedImagesCardProps {
  repoId: string;
}

function formatSize(bytes: number): string {
  if (bytes >= 1_073_741_824) return `${(bytes / 1_073_741_824).toFixed(1)}GB`;
  return `${(bytes / 1_048_576).toFixed(0)}MB`;
}

const STALE_THRESHOLD_DAYS = 90;

export function UnusedImagesCard({ repoId }: UnusedImagesCardProps) {
  const [unused, setUnused] = useState<ImageTag[]>([]);

  useEffect(() => {
    imagesApi.list(repoId).then((images) => {
      const cutoff = new Date();
      cutoff.setDate(cutoff.getDate() - STALE_THRESHOLD_DAYS);
      const stale = images.filter(
        (img) => new Date(img.pushedAt) < cutoff
      );
      setUnused(stale);
    }).catch(() => {});
  }, [repoId]);

  const totalSize = unused.reduce((sum, img) => sum + img.size, 0);

  return (
    <div className="bg-bg-card border border-surface-border rounded-xl p-4 card-hover">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">
        Unused Images
      </h3>
      <p className="text-3xl font-bold font-mono text-accent-orange mb-1">
        {unused.length}
      </p>
      <p className="text-xs text-text-secondary mb-2">
        stale images (90+ days)
      </p>
      {totalSize > 0 && (
        <p className="text-xs text-text-muted">
          {formatSize(totalSize)} reclaimable
        </p>
      )}
      {unused.slice(0, 3).map((img) => (
        <div key={img.id} className="mt-2 flex items-center justify-between text-xs">
          <span className="text-text-secondary font-mono truncate max-w-28">
            :{img.tag}
          </span>
          <span className="text-text-muted">
            {Math.floor((Date.now() - new Date(img.pushedAt).getTime()) / 86_400_000)}d ago
          </span>
        </div>
      ))}
    </div>
  );
}

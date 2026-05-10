"use client";

import { useEffect, useState } from "react";
import { imagesApi } from "@/lib/api";
import type { ImageTag } from "@/types/registry";

interface CostIntelligenceCardProps {
  repoId: string;
}

const ECR_STORAGE_COST_PER_GB = 0.1;
const TRANSFER_COST_PER_GB = 0.09;

export function CostIntelligenceCard({ repoId }: CostIntelligenceCardProps) {
  const [images, setImages] = useState<ImageTag[]>([]);

  useEffect(() => {
    imagesApi.list(repoId).then(setImages).catch(() => {});
  }, [repoId]);

  const totalBytes = images.reduce((sum, img) => sum + img.size, 0);
  const totalGB = totalBytes / 1_073_741_824;
  const storageCost = totalGB * ECR_STORAGE_COST_PER_GB;

  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - 90);
  const staleImages = images.filter((img) => new Date(img.pushedAt) < cutoff);
  const staleGB = staleImages.reduce((sum, img) => sum + img.size, 0) / 1_073_741_824;
  const potentialSavings = staleGB * (ECR_STORAGE_COST_PER_GB + TRANSFER_COST_PER_GB);

  return (
    <div className="bg-bg-card border border-surface-border rounded-xl p-4 card-hover">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">
        Cost Intelligence
      </h3>
      <div className="space-y-3">
        <div>
          <p className="text-2xl font-bold font-mono text-accent-cyan">
            ${storageCost.toFixed(2)}
          </p>
          <p className="text-xs text-text-secondary">est. monthly storage</p>
        </div>
        <div className="pt-2 border-t border-surface-border">
          <p className="text-sm font-bold text-accent-green">
            ${potentialSavings.toFixed(2)}/mo
          </p>
          <p className="text-xs text-text-secondary">
            savings from removing {staleImages.length} stale images
          </p>
        </div>
        <div className="text-xs text-text-muted">
          {totalGB.toFixed(2)} GB total stored &bull; ${ECR_STORAGE_COST_PER_GB}/GB/mo
        </div>
      </div>
    </div>
  );
}

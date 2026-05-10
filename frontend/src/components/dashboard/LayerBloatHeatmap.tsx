"use client";

import { useEffect, useState } from "react";
import { imagesApi } from "@/lib/api";
import type { LayerInfo } from "@/types/registry";

interface LayerBloatHeatmapProps {
  repoId: string;
}

function formatSize(bytes: number): string {
  if (bytes >= 1_048_576) return `${(bytes / 1_048_576).toFixed(0)}MB`;
  return `${(bytes / 1024).toFixed(0)}KB`;
}

function getHeatColor(size: number, maxSize: number): string {
  const ratio = size / maxSize;
  if (ratio >= 0.75) return "#ef4444";
  if (ratio >= 0.5) return "#f97316";
  if (ratio >= 0.25) return "#eab308";
  return "#10b981";
}

export function LayerBloatHeatmap({ repoId }: LayerBloatHeatmapProps) {
  const [layers, setLayers] = useState<LayerInfo[]>([]);
  const [tooltip, setTooltip] = useState<{
    layer: LayerInfo;
    x: number;
    y: number;
  } | null>(null);

  useEffect(() => {
    imagesApi.list(repoId).then(async (images) => {
      if (images.length === 0) return;
      const layerData = await imagesApi.getLayers(repoId, images[0].id);
      setLayers(layerData);
    }).catch(() => {});
  }, [repoId]);

  if (layers.length === 0) return null;

  const maxSize = Math.max(...layers.map((l) => l.size));

  return (
    <div className="bg-bg-card border border-surface-border rounded-xl p-5">
      <h3 className="text-sm font-semibold text-text-primary mb-4">
        Layer Bloat Heatmap
      </h3>
      <div className="grid grid-cols-8 gap-1 relative">
        {layers.map((layer, i) => {
          const color = getHeatColor(layer.size, maxSize);
          return (
            <div
              key={layer.digest}
              className="aspect-square rounded-sm cursor-pointer transition-transform hover:scale-110"
              style={{ backgroundColor: `${color}40`, border: `1px solid ${color}60` }}
              onMouseEnter={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                setTooltip({ layer, x: rect.left, y: rect.top });
              }}
              onMouseLeave={() => setTooltip(null)}
            />
          );
        })}
      </div>
      {tooltip && (
        <div className="mt-3 p-3 rounded-lg bg-bg-elevated border border-surface-border text-xs">
          <p className="text-text-primary font-mono truncate mb-1">
            Layer {tooltip.layer.index + 1}: {formatSize(tooltip.layer.size)}
          </p>
          <p className="text-text-secondary truncate">{tooltip.layer.command}</p>
        </div>
      )}
      <div className="flex items-center gap-3 mt-3 text-xs text-text-muted">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-sm bg-accent-green/40 border border-accent-green/60" />
          Small
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-sm bg-accent-yellow/40 border border-accent-yellow/60" />
          Medium
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-sm bg-accent-red/40 border border-accent-red/60" />
          Large
        </span>
      </div>
    </div>
  );
}

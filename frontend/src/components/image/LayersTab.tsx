"use client";

import type { LayerInfo } from "@/types/registry";

interface LayersTabProps {
  layers: LayerInfo[];
}

function formatSize(bytes: number): string {
  if (bytes >= 1_048_576) return `${(bytes / 1_048_576).toFixed(1)} MB`;
  return `${(bytes / 1024).toFixed(0)} KB`;
}

export function LayersTab({ layers }: LayersTabProps) {
  if (layers.length === 0) {
    return (
      <div className="text-center py-12 text-text-muted text-sm">
        No layer data available
      </div>
    );
  }

  const totalSize = layers.reduce((sum, l) => sum + l.size, 0);
  const maxSize = Math.max(...layers.map((l) => l.size));

  return (
    <div className="space-y-2 max-w-4xl">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-text-secondary">
          {layers.length} layers &bull; {formatSize(totalSize)} total
        </p>
      </div>
      {layers.map((layer, i) => {
        const widthPct = maxSize > 0 ? (layer.size / maxSize) * 100 : 0;
        const barColor =
          widthPct >= 75
            ? "#ef4444"
            : widthPct >= 50
            ? "#f97316"
            : widthPct >= 25
            ? "#eab308"
            : "#10b981";

        return (
          <div
            key={layer.digest}
            className="bg-bg-card border border-surface-border rounded-xl p-4"
          >
            <div className="flex items-start gap-4 mb-2">
              <span className="shrink-0 w-7 h-7 rounded-lg bg-bg-elevated border border-surface-border flex items-center justify-center text-xs font-mono text-text-muted">
                {i + 1}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-mono text-text-primary break-all leading-relaxed">
                  {layer.command || "Base layer"}
                </p>
                <p className="text-xs text-text-muted mt-1 font-mono">
                  {layer.digest.slice(0, 19)}...
                </p>
              </div>
              <span
                className="shrink-0 text-sm font-semibold font-mono"
                style={{ color: barColor }}
              >
                {formatSize(layer.size)}
              </span>
            </div>
            <div className="ml-11">
              <div className="h-1.5 rounded-full bg-surface-border overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${widthPct}%`,
                    backgroundColor: barColor,
                  }}
                />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

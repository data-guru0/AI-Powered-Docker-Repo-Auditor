"use client";

interface SizeOverviewCardProps {
  totalSizeReduction: number;
}

function formatSize(bytes: number): string {
  if (bytes >= 1_073_741_824) return `${(bytes / 1_073_741_824).toFixed(2)} GB`;
  if (bytes >= 1_048_576) return `${(bytes / 1_048_576).toFixed(0)} MB`;
  return `${(bytes / 1024).toFixed(0)} KB`;
}

export function SizeOverviewCard({ totalSizeReduction }: SizeOverviewCardProps) {
  return (
    <div className="bg-bg-card border border-surface-border rounded-xl p-4 card-hover">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">
        Size Overview
      </h3>
      <p className="text-3xl font-bold font-mono text-accent-green mb-1">
        -{formatSize(totalSizeReduction)}
      </p>
      <p className="text-xs text-text-secondary mb-4">
        potential reduction if recommendations applied
      </p>
      <div className="space-y-2">
        <div className="flex justify-between text-xs">
          <span className="text-text-muted">Multi-stage builds</span>
          <span className="text-accent-green font-medium">High impact</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-text-muted">Package cache removal</span>
          <span className="text-accent-yellow font-medium">Medium impact</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-text-muted">Layer consolidation</span>
          <span className="text-accent-blue font-medium">Low impact</span>
        </div>
      </div>
    </div>
  );
}

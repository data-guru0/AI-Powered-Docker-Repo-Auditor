"use client";

import type { ImageTag } from "@/types/registry";

interface OverviewTabProps {
  image: ImageTag | null;
}

function formatSize(bytes: number): string {
  if (bytes >= 1_073_741_824) return `${(bytes / 1_073_741_824).toFixed(2)} GB`;
  return `${(bytes / 1_048_576).toFixed(0)} MB`;
}

function OverviewRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center py-3.5 border-b border-surface-border last:border-0">
      <span className="text-xs font-medium text-text-muted sm:w-40">{label}</span>
      <span className="text-sm font-mono text-text-primary mt-1 sm:mt-0 break-all">
        {value}
      </span>
    </div>
  );
}

export function OverviewTab({ image }: OverviewTabProps) {
  if (!image) {
    return (
      <div className="text-center py-12 text-text-muted text-sm">
        Image not found
      </div>
    );
  }

  return (
    <div className="max-w-3xl">
      <div className="bg-bg-card border border-surface-border rounded-xl p-6">
        <OverviewRow label="Tag" value={`:${image.tag}`} />
        <OverviewRow label="Digest" value={image.digest} />
        <OverviewRow label="Size" value={formatSize(image.size)} />
        <OverviewRow label="OS" value={image.os} />
        <OverviewRow label="Architecture" value={image.architecture} />
        <OverviewRow label="Base Image" value={image.baseImage} />
        <OverviewRow
          label="Created"
          value={new Date(image.createdAt).toLocaleString()}
        />
        <OverviewRow
          label="Pushed"
          value={new Date(image.pushedAt).toLocaleString()}
        />
        <OverviewRow
          label="Compressed"
          value={image.compressed ? "Yes" : "No"}
        />
      </div>
    </div>
  );
}

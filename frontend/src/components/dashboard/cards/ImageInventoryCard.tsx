"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { imagesApi } from "@/lib/api";
import type { ImageTag } from "@/types/registry";

interface ImageInventoryCardProps {
  repoId: string;
}

function formatSize(bytes: number): string {
  if (bytes >= 1_073_741_824) return `${(bytes / 1_073_741_824).toFixed(1)}GB`;
  return `${(bytes / 1_048_576).toFixed(0)}MB`;
}

export function ImageInventoryCard({ repoId }: ImageInventoryCardProps) {
  const [images, setImages] = useState<ImageTag[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    imagesApi.list(repoId).then(setImages).catch(() => {}).finally(() => setLoading(false));
  }, [repoId]);

  return (
    <div className="bg-bg-card border border-surface-border rounded-xl p-4 card-hover">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">
        Image Inventory
      </h3>
      {loading ? (
        <div className="h-24 flex items-center justify-center">
          <div className="w-4 h-4 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <>
          <p className="text-3xl font-bold text-text-primary font-mono mb-1">
            {images.length}
          </p>
          <p className="text-xs text-text-secondary mb-3">
            {images.length === 1 ? "image tag" : "image tags"}
          </p>
          <div className="space-y-1.5 max-h-28 overflow-y-auto">
            {images.slice(0, 5).map((img) => (
              <Link
                key={img.id}
                href={`/dashboard/repo/${repoId}/image/${img.id}`}
                className="flex items-center justify-between hover:text-accent-cyan transition-colors"
              >
                <span className="text-xs font-mono text-text-secondary truncate max-w-24">
                  :{img.tag}
                </span>
                <span className="text-xs text-text-muted">
                  {formatSize(img.size)}
                </span>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

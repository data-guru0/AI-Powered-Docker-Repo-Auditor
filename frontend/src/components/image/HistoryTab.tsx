"use client";

import { useEffect, useState } from "react";
import { scansApi } from "@/lib/api";
import type { ScoreHistory } from "@/types/scan";

interface HistoryTabProps {
  repoId: string;
  imageId: string;
}

export function HistoryTab({ repoId }: HistoryTabProps) {
  const [history, setHistory] = useState<ScoreHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    scansApi.getScanHistory(repoId).then(setHistory).catch(() => {}).finally(() => setLoading(false));
  }, [repoId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="w-5 h-5 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="text-center py-12 text-text-muted text-sm">
        No scan history available
      </div>
    );
  }

  return (
    <div className="max-w-3xl space-y-3">
      <p className="text-sm text-text-secondary mb-4">
        {history.length} scan{history.length !== 1 ? "s" : ""} recorded
      </p>
      {[...history].reverse().map((entry, i) => (
        <div
          key={i}
          className="bg-bg-card border border-surface-border rounded-xl p-4"
        >
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm font-medium text-text-primary">
              {new Date(entry.date).toLocaleString()}
            </p>
            {entry.deployMarker && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-accent-purple/10 text-accent-purple border border-accent-purple/20">
                Deploy
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: "Security", value: entry.security, color: "#ef4444" },
              { label: "Bloat", value: entry.bloat, color: "#f97316" },
              { label: "Freshness", value: entry.freshness, color: "#00d4ff" },
              { label: "Best Practices", value: entry.bestPractices, color: "#8b5cf6" },
            ].map((metric) => (
              <div key={metric.label}>
                <p className="text-xs text-text-muted mb-1">{metric.label}</p>
                <p
                  className="text-lg font-bold font-mono"
                  style={{ color: metric.color }}
                >
                  {metric.value}
                </p>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

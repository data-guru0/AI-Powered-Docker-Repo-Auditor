"use client";

import type { TopAction } from "@/types/scan";

interface AIRecommendationsCardProps {
  topActions: TopAction[];
}

const EFFORT_COLORS: Record<string, string> = {
  low: "#10b981",
  medium: "#eab308",
  high: "#f97316",
};

export function AIRecommendationsCard({ topActions }: AIRecommendationsCardProps) {
  return (
    <div className="bg-bg-card border border-surface-border rounded-xl p-4 card-hover">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">
        AI Recommendations
      </h3>
      {topActions.length === 0 ? (
        <div className="py-6 text-center text-text-muted text-xs">
          No recommendations available
        </div>
      ) : (
        <div className="space-y-2.5">
          {topActions.map((action) => (
            <div key={action.rank} className="flex items-start gap-3">
              <span className="shrink-0 w-5 h-5 rounded bg-accent-purple/10 border border-accent-purple/20 flex items-center justify-center text-xs font-bold text-accent-purple">
                {action.rank}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-text-primary leading-snug">
                  {action.title}
                </p>
                <p className="text-xs text-text-muted mt-0.5">
                  Impact: {action.impact}
                </p>
              </div>
              <span
                className="shrink-0 text-xs font-medium capitalize"
                style={{ color: EFFORT_COLORS[action.effort] || "#94a3b8" }}
              >
                {action.effort}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

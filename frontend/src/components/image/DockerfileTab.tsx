"use client";

import { useState } from "react";
import type { DockerfileChange, DiffAnnotationCategory } from "@/types/scan";

interface DockerfileTabProps {
  original: string;
  optimized: string;
  changes: DockerfileChange[];
}

const ANNOTATION_LABELS: Record<DiffAnnotationCategory, string> = {
  security: "Security",
  bloat: "Bloat",
  cache: "Cache",
  "best-practice": "Best Practice",
};

const ANNOTATION_COLORS: Record<DiffAnnotationCategory, string> = {
  security: "#ef4444",
  bloat: "#f97316",
  cache: "#eab308",
  "best-practice": "#3b82f6",
};

function DiffPane({
  title,
  lines,
  changes,
  showAnnotations,
}: {
  title: string;
  lines: string[];
  changes: DockerfileChange[];
  showAnnotations: boolean;
}) {
  const [hoveredLine, setHoveredLine] = useState<number | null>(null);
  const changeMap = new Map(changes.map((c) => [c.lineNumber, c]));

  return (
    <div className="flex-1 min-w-0">
      <div className="px-4 py-2.5 border-b border-surface-border bg-bg-elevated">
        <p className="text-xs font-medium text-text-secondary">{title}</p>
      </div>
      <div className="overflow-auto max-h-[600px]">
        <table className="w-full border-collapse font-mono text-xs">
          <tbody>
            {lines.map((line, i) => {
              const lineNum = i + 1;
              const change = changeMap.get(lineNum);
              const category = change?.category as DiffAnnotationCategory | undefined;
              const rowClass = category
                ? `diff-line-${category}`
                : "";

              return (
                <tr
                  key={i}
                  className={`${rowClass} relative group`}
                  onMouseEnter={() => setHoveredLine(lineNum)}
                  onMouseLeave={() => setHoveredLine(null)}
                >
                  <td className="px-3 py-0.5 text-text-muted select-none w-10 text-right border-r border-surface-border">
                    {lineNum}
                  </td>
                  <td className="px-3 py-0.5 text-text-primary whitespace-pre">
                    {line || " "}
                  </td>
                  {showAnnotations && change && category && (
                    <td className="px-2 w-32">
                      <span
                        className="text-xs px-1.5 py-0.5 rounded"
                        style={{
                          color: ANNOTATION_COLORS[category],
                          backgroundColor: `${ANNOTATION_COLORS[category]}15`,
                          border: `1px solid ${ANNOTATION_COLORS[category]}30`,
                        }}
                      >
                        {ANNOTATION_LABELS[category]}
                      </span>
                    </td>
                  )}

                  {hoveredLine === lineNum && change && (
                    <td className="absolute left-full top-0 z-20 w-72 ml-2">
                      <div className="bg-bg-card border border-surface-border rounded-lg p-3 shadow-xl text-left">
                        <p className="text-xs font-medium text-text-primary mb-1">
                          {change.what}
                        </p>
                        <p className="text-xs text-text-secondary">
                          {change.why}
                        </p>
                        {change.estimatedSavings && (
                          <p className="text-xs text-accent-green mt-1">
                            Saves: {change.estimatedSavings}
                          </p>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function DockerfileTab({
  original,
  optimized,
  changes,
}: DockerfileTabProps) {
  const [showAnnotations, setShowAnnotations] = useState(true);

  if (!original && !optimized) {
    return (
      <div className="text-center py-12 text-text-muted text-sm">
        Dockerfile data not available for this image
      </div>
    );
  }

  const originalLines = original.split("\n");
  const optimizedLines = optimized.split("\n");

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3 flex-wrap">
          {(["security", "bloat", "cache", "best-practice"] as DiffAnnotationCategory[]).map((cat) => (
            <span key={cat} className="flex items-center gap-1.5 text-xs text-text-secondary">
              <span
                className="w-3 h-3 rounded-sm inline-block"
                style={{
                  backgroundColor: `${ANNOTATION_COLORS[cat]}20`,
                  borderLeft: `3px solid ${ANNOTATION_COLORS[cat]}`,
                }}
              />
              {ANNOTATION_LABELS[cat]}
            </span>
          ))}
        </div>
        <label className="ml-auto flex items-center gap-2 text-xs text-text-secondary cursor-pointer">
          <input
            type="checkbox"
            checked={showAnnotations}
            onChange={(e) => setShowAnnotations(e.target.checked)}
            className="rounded"
          />
          Show annotations
        </label>
      </div>

      <div className="flex gap-0 bg-bg-card border border-surface-border rounded-xl overflow-hidden">
        <DiffPane
          title="Original Dockerfile"
          lines={originalLines}
          changes={changes}
          showAnnotations={false}
        />
        <div className="w-px bg-surface-border shrink-0" />
        <DiffPane
          title="Optimized Dockerfile"
          lines={optimizedLines}
          changes={changes}
          showAnnotations={showAnnotations}
        />
      </div>
    </div>
  );
}

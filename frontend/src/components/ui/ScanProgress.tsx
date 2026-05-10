"use client";

import { useEffect } from "react";
import { useScanProgress } from "@/hooks/useScanProgress";

interface ScanProgressProps {
  jobId: string;
  onComplete: (scanId: string) => void;
}

const STEPS = [
  "Fetching image manifest",
  "Running Trivy scan",
  "Running AWS Inspector",
  "Analyzing layers for bloat",
  "CVE Analysis Agent",
  "Bloat Detective Agent",
  "Base Image Strategist Agent",
  "Dockerfile Optimizer Agent",
  "Risk Scorer Agent",
  "Storing results",
  "Running Ragas evaluation",
  "Sending completion email",
];

export function ScanProgress({ jobId, onComplete }: ScanProgressProps) {
  const { job, connected, isComplete } = useScanProgress(jobId);

  useEffect(() => {
    if (job?.status === "completed" && job.jobId) {
      onComplete(job.jobId);
    }
  }, [job?.status, job?.jobId, onComplete]);

  const progress = job?.progress || 0;

  return (
    <div className="bg-bg-card border border-surface-border rounded-xl p-5 relative overflow-hidden scan-running">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-accent-cyan animate-pulse" />
          <span className="text-sm font-medium text-text-primary">
            Scan in progress
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`text-xs ${connected ? "text-accent-green" : "text-accent-yellow"}`}
          >
            {connected ? "Live" : "Reconnecting..."}
          </span>
          <span className="text-sm font-mono text-accent-cyan font-semibold">
            {progress}%
          </span>
        </div>
      </div>

      <div className="h-1.5 rounded-full bg-surface-border overflow-hidden mb-4">
        <div
          className="h-full rounded-full bg-accent-cyan transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      <p className="text-xs text-text-secondary font-mono">
        {job?.currentStep || "Initializing scan..."}
      </p>

      {job?.status === "failed" && (
        <div className="mt-3 p-2 rounded-lg bg-accent-red/10 border border-accent-red/30 text-accent-red text-xs">
          {job.error || "Scan failed unexpectedly"}
        </div>
      )}

      <div className="mt-4 grid grid-cols-3 sm:grid-cols-4 gap-1.5">
        {STEPS.map((step, i) => {
          const stepProgress = (i + 1) / STEPS.length * 100;
          const done = progress >= stepProgress;
          return (
            <div
              key={step}
              className={`text-xs px-2 py-1.5 rounded border truncate transition-colors ${
                done
                  ? "bg-accent-cyan/10 border-accent-cyan/30 text-accent-cyan"
                  : "bg-bg-elevated border-surface-border text-text-muted"
              }`}
              title={step}
            >
              {step}
            </div>
          );
        })}
      </div>
    </div>
  );
}

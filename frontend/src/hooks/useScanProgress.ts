"use client";

import { useState, useEffect } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";
import type { ScanJob, ScanStatus } from "@/types/scan";

export function useScanProgress(jobId: string | null) {
  const { event, connected } = useWebSocket(jobId);
  const [job, setJob] = useState<ScanJob | null>(null);

  useEffect(() => {
    if (!event || !jobId) return;
    setJob((prev) => ({
      jobId,
      repoId: prev?.repoId || "",
      status: event.status as ScanStatus,
      progress: event.progress,
      currentStep: event.step,
      startedAt: prev?.startedAt || event.timestamp,
      completedAt:
        event.status === "completed" || event.status === "failed"
          ? event.timestamp
          : prev?.completedAt,
      error:
        event.status === "failed" ? event.message : undefined,
    }));
  }, [event, jobId]);

  const isComplete =
    job?.status === "completed" || job?.status === "failed";

  return { job, connected, isComplete };
}

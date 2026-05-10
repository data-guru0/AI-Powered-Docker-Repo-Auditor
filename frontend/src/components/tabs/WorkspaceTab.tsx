"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { workspaceApi } from "@/lib/api";
import type { WorkspaceRepo } from "@/types/registry";

const GRADE_COLORS: Record<string, string> = {
  A: "text-grade-a border-grade-a/30 bg-grade-a/10",
  B: "text-grade-b border-grade-b/30 bg-grade-b/10",
  C: "text-grade-c border-grade-c/30 bg-grade-c/10",
  D: "text-grade-d border-grade-d/30 bg-grade-d/10",
  F: "text-grade-f border-grade-f/30 bg-grade-f/10",
};

export function WorkspaceTab() {
  const [repos, setRepos] = useState<WorkspaceRepo[]>([]);
  const [loading, setLoading] = useState(true);
  const [removing, setRemoving] = useState<string | null>(null);

  useEffect(() => {
    workspaceApi.listRepos().then(setRepos).catch(() => {}).finally(() => setLoading(false));
  }, []);

  async function removeFromWorkspace(repoId: string) {
    setRemoving(repoId);
    try {
      await workspaceApi.removeRepo(repoId);
      setRepos((prev) => prev.filter((r) => r.repoId !== repoId));
    } catch {
      /* ignore */
    } finally {
      setRemoving(null);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-5 h-5 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (repos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="w-12 h-12 rounded-xl border border-surface-border-bright bg-bg-card flex items-center justify-center mb-4">
          <div className="w-6 h-6 rounded border-2 border-surface-border-bright" />
        </div>
        <p className="text-text-primary font-medium mb-1">Your workspace is empty</p>
        <p className="text-text-secondary text-sm">
          Go to Repositories and add repos to start scanning
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {repos.map((repo) => {
        const gradeClass = repo.overallGrade
          ? GRADE_COLORS[repo.overallGrade] || "text-text-muted border-surface-border bg-transparent"
          : "text-text-muted border-surface-border bg-transparent";

        return (
          <div
            key={repo.id}
            className="bg-bg-card border border-surface-border rounded-xl p-4 flex flex-col gap-3 card-hover cursor-pointer group"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <Link
                  href={`/dashboard/repo/${repo.repoId}`}
                  className="text-sm font-mono font-medium text-text-primary truncate block hover:text-accent-cyan transition-colors"
                >
                  {repo.name}
                </Link>
                <span className="text-xs text-text-muted uppercase tracking-wider">
                  {repo.registryType === "ecr" ? "ECR" : "DockerHub"}
                </span>
              </div>
              {repo.overallGrade && (
                <span
                  className={`shrink-0 text-lg font-bold px-2.5 py-1 rounded-lg border ${gradeClass}`}
                >
                  {repo.overallGrade}
                </span>
              )}
            </div>

            {repo.criticalCveCount > 0 && (
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-severity-critical" />
                <span className="text-xs text-severity-critical font-medium">
                  {repo.criticalCveCount} critical CVE{repo.criticalCveCount !== 1 ? "s" : ""}
                </span>
              </div>
            )}

            <div className="text-xs text-text-muted">
              {repo.lastScanDate
                ? `Scanned ${new Date(repo.lastScanDate).toLocaleDateString()}`
                : "Not yet scanned"}
            </div>

            <div className="flex items-center gap-2 pt-1 border-t border-surface-border">
              <Link
                href={`/dashboard/repo/${repo.repoId}`}
                className="flex-1 text-center py-1.5 rounded-lg text-xs font-medium text-accent-cyan border border-accent-cyan/20 hover:bg-accent-cyan/10 transition-colors"
              >
                View Dashboard
              </Link>
              <button
                onClick={() => removeFromWorkspace(repo.repoId)}
                disabled={removing === repo.repoId}
                className="p-1.5 rounded-lg text-text-muted hover:text-accent-red hover:bg-accent-red/5 transition-colors disabled:opacity-50"
                title="Remove from workspace"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M11 3L3 11M3 3l8 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { workspaceApi } from "@/lib/api";
import { useState, useEffect } from "react";
import type { WorkspaceRepo } from "@/types/registry";

export function Sidebar() {
  const pathname = usePathname();
  const [repos, setRepos] = useState<WorkspaceRepo[]>([]);

  useEffect(() => {
    workspaceApi.listRepos().then(setRepos).catch(() => {});
  }, []);

  return (
    <aside className="w-56 shrink-0 bg-bg-card border-r border-surface-border flex flex-col h-screen sticky top-0">
      <div className="px-4 py-5 border-b border-surface-border">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-accent-cyan/10 border border-accent-cyan/30 flex items-center justify-center">
            <div className="w-3.5 h-3.5 rounded-sm border-2 border-accent-cyan" />
          </div>
          <span className="text-sm font-semibold text-text-primary tracking-tight">
            DockerAuditor
          </span>
        </div>
      </div>

      <nav className="flex-1 px-2 py-4 overflow-y-auto space-y-0.5">
        <Link
          href="/dashboard"
          className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
            pathname === "/dashboard"
              ? "bg-accent-cyan/10 text-accent-cyan"
              : "text-text-secondary hover:text-text-primary hover:bg-bg-hover"
          }`}
        >
          <span className="w-4 h-4 grid place-items-center">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <rect x="1" y="1" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
              <rect x="8" y="1" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
              <rect x="1" y="8" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
              <rect x="8" y="8" width="5" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" />
            </svg>
          </span>
          Dashboard
        </Link>

        {repos.length > 0 && (
          <div className="mt-4">
            <p className="px-3 mb-1 text-xs font-medium text-text-muted uppercase tracking-wider">
              Workspace
            </p>
            {repos.map((repo) => {
              const href = `/dashboard/repo/${repo.repoId}`;
              const isActive = pathname.startsWith(href);
              return (
                <Link
                  key={repo.id}
                  href={href}
                  className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors group ${
                    isActive
                      ? "bg-accent-cyan/10 text-accent-cyan"
                      : "text-text-secondary hover:text-text-primary hover:bg-bg-hover"
                  }`}
                >
                  <span
                    className={`shrink-0 w-2 h-2 rounded-full ${
                      repo.overallGrade === "A" || repo.overallGrade === "B"
                        ? "bg-accent-green"
                        : repo.overallGrade === "C"
                        ? "bg-accent-yellow"
                        : repo.overallGrade === "D"
                        ? "bg-accent-orange"
                        : repo.overallGrade === "F"
                        ? "bg-accent-red"
                        : "bg-text-muted"
                    }`}
                  />
                  <span className="truncate font-mono text-xs">{repo.name}</span>
                  {repo.criticalCveCount > 0 && (
                    <span className="ml-auto shrink-0 text-xs text-severity-critical font-semibold">
                      {repo.criticalCveCount}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        )}
      </nav>

      <div className="px-4 py-3 border-t border-surface-border">
        <p className="text-xs text-text-muted">Docker Image Auditor</p>
      </div>
    </aside>
  );
}

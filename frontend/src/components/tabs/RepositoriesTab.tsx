"use client";

import { useState, useEffect } from "react";
import { repositoriesApi, workspaceApi } from "@/lib/api";
import type { Repository, RegistryType } from "@/types/registry";

function formatSize(bytes: number): string {
  if (bytes >= 1_073_741_824) return `${(bytes / 1_073_741_824).toFixed(1)} GB`;
  if (bytes >= 1_048_576) return `${(bytes / 1_048_576).toFixed(0)} MB`;
  return `${(bytes / 1024).toFixed(0)} KB`;
}

export function RepositoriesTab() {
  const [activeRegistry, setActiveRegistry] = useState<RegistryType>("dockerhub");
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await repositoriesApi.list(activeRegistry);
        setRepos(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load repositories");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [activeRegistry]);

  async function addToWorkspace(repoId: string) {
    setAdding(repoId);
    try {
      await workspaceApi.addRepo(repoId);
      setRepos((prev) =>
        prev.map((r) => (r.id === repoId ? { ...r, inWorkspace: true } : r))
      );
    } catch {
      /* ignore */
    } finally {
      setAdding(null);
    }
  }

  const filtered = repos.filter((r) =>
    r.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex rounded-lg border border-surface-border overflow-hidden">
          {(["dockerhub", "ecr"] as RegistryType[]).map((reg) => (
            <button
              key={reg}
              onClick={() => setActiveRegistry(reg)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeRegistry === reg
                  ? "bg-accent-cyan/10 text-accent-cyan"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              {reg === "dockerhub" ? "DockerHub" : "AWS ECR"}
            </button>
          ))}
        </div>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter repositories..."
          className="px-3 py-2 rounded-lg bg-bg-card border border-surface-border text-text-primary text-sm focus:outline-none focus:border-accent-cyan/60 transition-colors w-64"
        />
        <span className="text-text-muted text-sm ml-auto">
          {filtered.length} repositories
        </span>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-accent-red/10 border border-accent-red/30 text-accent-red text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="w-5 h-5 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="bg-bg-card border border-surface-border rounded-xl overflow-hidden">
          <div className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-x-6 px-4 py-3 border-b border-surface-border text-xs font-medium text-text-muted">
            <span>Repository</span>
            <span className="text-right">Images</span>
            <span className="text-right">Size</span>
            <span className="text-right">Last pushed</span>
            <span />
          </div>
          {filtered.length === 0 ? (
            <div className="py-16 text-center text-text-muted text-sm">
              No repositories found
            </div>
          ) : (
            <div className="divide-y divide-surface-border">
              {filtered.map((repo) => (
                <div
                  key={repo.id}
                  className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-x-6 px-4 py-3.5 items-center hover:bg-bg-elevated transition-colors"
                >
                  <div>
                    <p className="text-sm font-mono text-text-primary">
                      {repo.name}
                    </p>
                    {repo.isPrivate && (
                      <span className="text-xs text-text-muted">Private</span>
                    )}
                  </div>
                  <span className="text-sm text-text-secondary text-right">
                    {repo.imageCount}
                  </span>
                  <span className="text-sm text-text-secondary text-right">
                    {formatSize(repo.totalSize)}
                  </span>
                  <span className="text-sm text-text-secondary text-right">
                    {new Date(repo.lastPushed).toLocaleDateString()}
                  </span>
                  <div className="flex justify-end">
                    {repo.inWorkspace ? (
                      <span className="px-3 py-1 text-xs text-accent-green border border-accent-green/30 rounded-full">
                        Added
                      </span>
                    ) : (
                      <button
                        onClick={() => addToWorkspace(repo.id)}
                        disabled={adding === repo.id}
                        className="px-3 py-1 text-xs text-accent-cyan border border-accent-cyan/30 rounded-full hover:bg-accent-cyan/10 transition-colors disabled:opacity-50"
                      >
                        {adding === repo.id ? "Adding..." : "Add to Workspace"}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

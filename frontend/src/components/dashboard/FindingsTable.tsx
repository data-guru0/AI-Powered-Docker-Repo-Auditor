"use client";

import { useState, useMemo } from "react";
import type { Finding, SeverityLevel, FindingCategory, AgentName, EffortLevel } from "@/types/scan";

interface FindingsTableProps {
  findings: Finding[];
}

const SEVERITY_ORDER: Record<SeverityLevel, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  informational: 4,
};

type SortKey = "severity" | "category" | "effort";

export function FindingsTable({ findings }: FindingsTableProps) {
  const [severityFilter, setSeverityFilter] = useState<SeverityLevel | "all">("all");
  const [categoryFilter, setCategoryFilter] = useState<FindingCategory | "all">("all");
  const [agentFilter, setAgentFilter] = useState<AgentName | "all">("all");
  const [effortFilter, setEffortFilter] = useState<EffortLevel | "all">("all");
  const [sortKey, setSortKey] = useState<SortKey>("severity");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    return findings
      .filter((f) => severityFilter === "all" || f.severity === severityFilter)
      .filter((f) => categoryFilter === "all" || f.category === categoryFilter)
      .filter((f) => agentFilter === "all" || f.agent === agentFilter)
      .filter((f) => effortFilter === "all" || f.effort === effortFilter)
      .sort((a, b) => {
        if (sortKey === "severity") return SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity];
        if (sortKey === "effort") return a.effort.localeCompare(b.effort);
        return a.category.localeCompare(b.category);
      });
  }, [findings, severityFilter, categoryFilter, agentFilter, effortFilter, sortKey]);

  return (
    <div>
      <div className="px-4 py-3 border-b border-surface-border flex flex-wrap gap-3 items-center">
        <FilterSelect
          label="Severity"
          value={severityFilter}
          options={["all", "critical", "high", "medium", "low", "informational"]}
          onChange={(v) => setSeverityFilter(v as SeverityLevel | "all")}
        />
        <FilterSelect
          label="Category"
          value={categoryFilter}
          options={["all", "cve", "bloat", "base_image", "best_practice", "compliance", "secret"]}
          onChange={(v) => setCategoryFilter(v as FindingCategory | "all")}
        />
        <FilterSelect
          label="Agent"
          value={agentFilter}
          options={["all", "cve_analyst", "bloat_detective", "base_image_strategist", "dockerfile_optimizer", "risk_scorer"]}
          onChange={(v) => setAgentFilter(v as AgentName | "all")}
        />
        <FilterSelect
          label="Effort"
          value={effortFilter}
          options={["all", "low", "medium", "high"]}
          onChange={(v) => setEffortFilter(v as EffortLevel | "all")}
        />
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs text-text-muted">Sort:</span>
          <FilterSelect
            label=""
            value={sortKey}
            options={["severity", "category", "effort"]}
            onChange={(v) => setSortKey(v as SortKey)}
          />
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="py-12 text-center text-text-muted text-sm">
          No findings match the current filters
        </div>
      ) : (
        <div className="divide-y divide-surface-border">
          {filtered.map((finding) => (
            <FindingRow
              key={finding.id}
              finding={finding}
              expanded={expandedId === finding.id}
              onToggle={() =>
                setExpandedId(expandedId === finding.id ? null : finding.id)
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex items-center gap-1.5">
      {label && <span className="text-xs text-text-muted">{label}:</span>}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="px-2 py-1 rounded bg-bg-elevated border border-surface-border text-text-secondary text-xs focus:outline-none focus:border-accent-cyan/60 capitalize"
      >
        {options.map((o) => (
          <option key={o} value={o}>
            {o === "all" ? "All" : o.replace(/_/g, " ")}
          </option>
        ))}
      </select>
    </div>
  );
}

const SEVERITY_BADGE_CLASS: Record<SeverityLevel, string> = {
  critical: "severity-badge-critical",
  high: "severity-badge-high",
  medium: "severity-badge-medium",
  low: "severity-badge-low",
  informational: "severity-badge-informational",
};

function FindingRow({
  finding,
  expanded,
  onToggle,
}: {
  finding: Finding;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div>
      <button
        onClick={onToggle}
        className="w-full text-left px-4 py-3.5 hover:bg-bg-elevated transition-colors flex items-start gap-4"
      >
        <span
          className={`shrink-0 px-2 py-0.5 rounded text-xs font-medium capitalize ${SEVERITY_BADGE_CLASS[finding.severity]}`}
        >
          {finding.severity}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-text-primary font-medium leading-snug">
            {finding.title}
          </p>
          <p className="text-xs text-text-secondary mt-0.5 truncate">
            {finding.detail}
          </p>
        </div>
        <div className="shrink-0 flex items-center gap-3">
          <span className="text-xs text-text-muted capitalize hidden md:block">
            {finding.category.replace(/_/g, " ")}
          </span>
          <span className="text-xs text-text-muted capitalize hidden lg:block">
            {finding.effort} effort
          </span>
          <svg
            width={14}
            height={14}
            viewBox="0 0 14 14"
            fill="none"
            className={`text-text-muted transition-transform ${expanded ? "rotate-180" : ""}`}
          >
            <path d="M3 5l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 bg-bg-elevated border-t border-surface-border">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
            <DetailField label="Evidence" value={finding.evidence} />
            <DetailField label="Impact" value={finding.impact} />
            <DetailField label="Fix" value={finding.fix} />
            <DetailField label="Agent" value={finding.agent.replace(/_/g, " ")} />
          </div>
        </div>
      )}
    </div>
  );
}

function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium text-text-muted mb-1">{label}</p>
      <p className="text-sm text-text-secondary leading-relaxed">{value}</p>
    </div>
  );
}

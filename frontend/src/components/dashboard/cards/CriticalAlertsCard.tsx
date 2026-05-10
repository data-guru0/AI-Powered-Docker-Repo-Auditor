"use client";

interface CriticalAlertsCardProps {
  cveCount: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}

export function CriticalAlertsCard({ cveCount }: CriticalAlertsCardProps) {
  const total = cveCount.critical + cveCount.high + cveCount.medium + cveCount.low;

  return (
    <div className="bg-bg-card border border-surface-border rounded-xl p-4 card-hover">
      <h3 className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">
        Critical Alerts
      </h3>
      <p
        className="text-3xl font-bold font-mono mb-1"
        style={{ color: cveCount.critical > 0 ? "#dc2626" : "#10b981" }}
      >
        {cveCount.critical}
      </p>
      <p className="text-xs text-text-secondary mb-3">critical CVEs</p>
      <div className="space-y-1.5">
        {[
          { label: "High", count: cveCount.high, color: "#f97316" },
          { label: "Medium", count: cveCount.medium, color: "#eab308" },
          { label: "Low", count: cveCount.low, color: "#3b82f6" },
        ].map((item) => (
          <div key={item.label} className="flex items-center justify-between">
            <span className="text-xs text-text-secondary">{item.label}</span>
            <span
              className="text-xs font-semibold"
              style={{ color: item.color }}
            >
              {item.count}
            </span>
          </div>
        ))}
        <div className="pt-1 border-t border-surface-border flex items-center justify-between">
          <span className="text-xs text-text-muted">Total</span>
          <span className="text-xs font-semibold text-text-primary">{total}</span>
        </div>
      </div>
    </div>
  );
}

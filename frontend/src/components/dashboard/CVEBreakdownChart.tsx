"use client";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface CVEBreakdownChartProps {
  cveCount: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}

const SEVERITY_COLORS = {
  critical: "#dc2626",
  high: "#f97316",
  medium: "#eab308",
  low: "#3b82f6",
};

export function CVEBreakdownChart({ cveCount }: CVEBreakdownChartProps) {
  const data = [
    { name: "Critical", value: cveCount.critical, color: SEVERITY_COLORS.critical },
    { name: "High", value: cveCount.high, color: SEVERITY_COLORS.high },
    { name: "Medium", value: cveCount.medium, color: SEVERITY_COLORS.medium },
    { name: "Low", value: cveCount.low, color: SEVERITY_COLORS.low },
  ].filter((d) => d.value > 0);

  const total = data.reduce((sum, d) => sum + d.value, 0);

  return (
    <div className="bg-bg-card border border-surface-border rounded-xl p-5">
      <h3 className="text-sm font-semibold text-text-primary mb-4">
        Active CVEs
      </h3>
      {total === 0 ? (
        <div className="flex items-center justify-center h-32 text-text-muted text-sm">
          No CVEs detected
        </div>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={45}
                outerRadius={70}
                paddingAngle={3}
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0e0e1a",
                  border: "1px solid #1e1e30",
                  borderRadius: "8px",
                  fontSize: "12px",
                  color: "#f1f5f9",
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 gap-2 mt-2">
            {data.map((item) => (
              <div key={item.name} className="flex items-center gap-2">
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-xs text-text-secondary">{item.name}</span>
                <span className="text-xs font-semibold text-text-primary ml-auto">
                  {item.value}
                </span>
              </div>
            ))}
          </div>
          <p className="text-center text-xs text-text-muted mt-2">
            {total} total CVEs
          </p>
        </>
      )}
    </div>
  );
}

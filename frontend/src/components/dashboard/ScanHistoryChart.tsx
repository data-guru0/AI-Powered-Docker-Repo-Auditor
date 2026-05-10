"use client";

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { scansApi } from "@/lib/api";
import type { ScoreHistory } from "@/types/scan";

interface ScanHistoryChartProps {
  repoId: string;
}

export function ScanHistoryChart({ repoId }: ScanHistoryChartProps) {
  const [history, setHistory] = useState<ScoreHistory[]>([]);

  useEffect(() => {
    scansApi.getScanHistory(repoId).then(setHistory).catch(() => {});
  }, [repoId]);

  if (history.length === 0) return null;

  const formatted = history.map((h) => ({
    ...h,
    date: new Date(h.date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    }),
  }));

  return (
    <div className="bg-bg-card border border-surface-border rounded-xl p-5">
      <h3 className="text-sm font-semibold text-text-primary mb-4">
        Scan History
      </h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={formatted}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e1e30" />
          <XAxis
            dataKey="date"
            tick={{ fill: "#475569", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fill: "#475569", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={28}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#0e0e1a",
              border: "1px solid #1e1e30",
              borderRadius: "8px",
              fontSize: "12px",
              color: "#f1f5f9",
            }}
          />
          {formatted
            .filter((d) => d.deployMarker)
            .map((d, i) => (
              <ReferenceLine
                key={i}
                x={d.date}
                stroke="#1e1e30"
                strokeDasharray="4 4"
                label={{ value: "Deploy", fill: "#475569", fontSize: 9 }}
              />
            ))}
          <Line
            type="monotone"
            dataKey="security"
            stroke="#ef4444"
            strokeWidth={2}
            dot={false}
            name="Security"
          />
          <Line
            type="monotone"
            dataKey="bloat"
            stroke="#f97316"
            strokeWidth={2}
            dot={false}
            name="Bloat"
          />
          <Line
            type="monotone"
            dataKey="freshness"
            stroke="#00d4ff"
            strokeWidth={2}
            dot={false}
            name="Freshness"
          />
          <Line
            type="monotone"
            dataKey="bestPractices"
            stroke="#8b5cf6"
            strokeWidth={2}
            dot={false}
            name="Best Practices"
          />
        </LineChart>
      </ResponsiveContainer>
      <div className="flex items-center gap-4 mt-2 flex-wrap">
        {[
          { label: "Security", color: "#ef4444" },
          { label: "Bloat", color: "#f97316" },
          { label: "Freshness", color: "#00d4ff" },
          { label: "Best Practices", color: "#8b5cf6" },
        ].map((item) => (
          <span key={item.label} className="flex items-center gap-1.5 text-xs text-text-secondary">
            <span
              className="w-3 h-0.5 rounded-full inline-block"
              style={{ backgroundColor: item.color }}
            />
            {item.label}
          </span>
        ))}
      </div>
    </div>
  );
}

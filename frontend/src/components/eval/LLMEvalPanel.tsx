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
} from "recharts";
import { evalApi } from "@/lib/api";
import type { EvalSummary, AgentEvalScore } from "@/types/agent";

interface LLMEvalPanelProps {
  repoId: string;
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 80 ? "#10b981" : pct >= 60 ? "#eab308" : "#ef4444";

  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-text-secondary">{label}</span>
        <span className="font-mono" style={{ color }}>{pct}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-surface-border overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

function AgentCard({ score }: { score: AgentEvalScore }) {
  const avg = Math.round(
    ((score.faithfulness +
      score.answerRelevancy +
      (1 - score.hallucinationScore) +
      score.contextPrecision +
      score.contextRecall +
      score.answerCorrectness) /
      6) *
      100
  );
  const agentLabel = score.agentName.replace(/_/g, " ");

  return (
    <div className="bg-bg-elevated border border-surface-border rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-text-primary capitalize">
          {agentLabel}
        </p>
        <span
          className="text-sm font-bold font-mono"
          style={{
            color: avg >= 80 ? "#10b981" : avg >= 60 ? "#eab308" : "#ef4444",
          }}
        >
          {avg}%
        </span>
      </div>
      <div className="space-y-2">
        <ScoreBar label="Faithfulness" value={score.faithfulness} />
        <ScoreBar label="Answer Relevancy" value={score.answerRelevancy} />
        <ScoreBar label="Context Precision" value={score.contextPrecision} />
        <ScoreBar label="Hallucination" value={1 - score.hallucinationScore} />
      </div>
    </div>
  );
}

export function LLMEvalPanel({ repoId }: LLMEvalPanelProps) {
  const [summary, setSummary] = useState<EvalSummary | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    evalApi.getSummary(repoId).then(setSummary).catch(() => {});
  }, [repoId]);

  if (!summary) return null;

  const trendData = summary.trends.reduce<
    Record<string, Record<string, number>>
  >((acc, t) => {
    if (!acc[t.date]) acc[t.date] = { date: t.date };
    acc[t.date][t.agentName] = Math.round(t.averageScore * 100);
    return acc;
  }, {});

  const chartData = Object.values(trendData);
  const agentNames = [...new Set(summary.trends.map((t) => t.agentName))];
  const agentColors = ["#00d4ff", "#8b5cf6", "#10b981", "#f97316", "#ef4444"];

  return (
    <div className="bg-bg-card border border-surface-border rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full px-6 py-4 border-b border-surface-border flex items-center justify-between hover:bg-bg-elevated transition-colors"
      >
        <div className="text-left">
          <h2 className="text-base font-semibold text-text-primary">
            LLM Evaluation Dashboard
          </h2>
          <p className="text-text-secondary text-xs mt-0.5">
            {summary.totalEvaluations} evaluations &bull; {summary.flaggedResponses} flagged &bull; worst: {summary.worstPerformingAgent.replace(/_/g, " ")}
          </p>
        </div>
        <svg
          width={16}
          height={16}
          viewBox="0 0 16 16"
          fill="none"
          className={`text-text-muted transition-transform ${expanded ? "rotate-180" : ""}`}
        >
          <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {expanded && (
        <div className="p-6 space-y-6">
          {chartData.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-text-primary mb-3">
                Score Trends
              </h3>
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e1e30" />
                  <XAxis dataKey="date" tick={{ fill: "#475569", fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fill: "#475569", fontSize: 10 }} axisLine={false} tickLine={false} width={28} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0e0e1a", border: "1px solid #1e1e30", borderRadius: "8px", fontSize: "11px", color: "#f1f5f9" }}
                  />
                  {agentNames.map((name, i) => (
                    <Line
                      key={name}
                      type="monotone"
                      dataKey={name}
                      stroke={agentColors[i % agentColors.length]}
                      strokeWidth={2}
                      dot={false}
                      name={name.replace(/_/g, " ")}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          <div>
            <h3 className="text-sm font-semibold text-text-primary mb-3">
              Per-Agent Scores
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {summary.scores.map((score) => (
                <AgentCard key={score.agentName} score={score} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

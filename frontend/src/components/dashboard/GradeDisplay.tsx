"use client";

const GRADE_STYLES: Record<string, { color: string; glow: string }> = {
  A: { color: "#10b981", glow: "0 0 40px rgba(16, 185, 129, 0.3)" },
  B: { color: "#00d4ff", glow: "0 0 40px rgba(0, 212, 255, 0.3)" },
  C: { color: "#eab308", glow: "0 0 40px rgba(234, 179, 8, 0.3)" },
  D: { color: "#f97316", glow: "0 0 40px rgba(249, 115, 22, 0.3)" },
  F: { color: "#ef4444", glow: "0 0 40px rgba(239, 68, 68, 0.3)" },
};

interface GradeDisplayProps {
  grade: string;
  summary: string;
}

export function GradeDisplay({ grade, summary }: GradeDisplayProps) {
  const style = GRADE_STYLES[grade] || GRADE_STYLES["F"];

  return (
    <div className="flex flex-col items-center gap-4 bg-bg-card border border-surface-border rounded-xl p-6 min-w-56">
      <div
        className="w-24 h-24 rounded-2xl flex items-center justify-center border-2"
        style={{
          borderColor: style.color,
          boxShadow: style.glow,
          backgroundColor: `${style.color}10`,
        }}
      >
        <span
          className="text-5xl font-bold font-mono"
          style={{ color: style.color }}
        >
          {grade}
        </span>
      </div>
      <div className="text-center">
        <p className="text-sm font-medium text-text-primary mb-1">
          Overall Grade
        </p>
        <p className="text-xs text-text-secondary max-w-48 leading-relaxed">
          {summary}
        </p>
      </div>
    </div>
  );
}

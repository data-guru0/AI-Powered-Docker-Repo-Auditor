"use client";

import { useEffect, useState } from "react";

interface RingScoreProps {
  label: string;
  score: number;
  color: string;
  reason?: string;
}

const RADIUS = 45;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export function RingScore({ label, score, color, reason }: RingScoreProps) {
  const [animatedOffset, setAnimatedOffset] = useState(CIRCUMFERENCE);

  useEffect(() => {
    const timer = setTimeout(() => {
      const offset = CIRCUMFERENCE - (score / 100) * CIRCUMFERENCE;
      setAnimatedOffset(offset);
    }, 100);
    return () => clearTimeout(timer);
  }, [score]);

  const scoreColor =
    score >= 80
      ? "#10b981"
      : score >= 60
      ? "#eab308"
      : score >= 40
      ? "#f97316"
      : "#ef4444";

  return (
    <div className="flex flex-col items-center gap-1.5 min-w-0">
      <svg
        width={112}
        height={112}
        viewBox="0 0 112 112"
        className="overflow-visible shrink-0"
      >
        <circle
          cx={56}
          cy={56}
          r={RADIUS}
          fill="none"
          stroke="#1e1e30"
          strokeWidth={8}
        />
        <circle
          cx={56}
          cy={56}
          r={RADIUS}
          fill="none"
          stroke={scoreColor}
          strokeWidth={8}
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={animatedOffset}
          transform="rotate(-90 56 56)"
          className="ring-score-circle"
          style={{ filter: `drop-shadow(0 0 6px ${scoreColor}60)` } as React.CSSProperties}
        />
        <text
          x={56}
          y={52}
          textAnchor="middle"
          fill={scoreColor}
          fontSize={22}
          fontWeight={700}
          fontFamily="var(--font-jetbrains-mono)"
        >
          {score}
        </text>
        <text
          x={56}
          y={66}
          textAnchor="middle"
          fill="#475569"
          fontSize={9}
          fontWeight={500}
          fontFamily="var(--font-space-grotesk)"
        >
          / 100
        </text>
      </svg>
      <span className="text-xs font-semibold text-text-secondary tracking-wide text-center">
        {label}
      </span>
      {reason && (
        <span className="text-[10px] text-text-muted text-center leading-tight max-w-[110px]">
          {reason}
        </span>
      )}
    </div>
  );
}

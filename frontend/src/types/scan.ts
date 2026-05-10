export type SeverityLevel =
  | "critical"
  | "high"
  | "medium"
  | "low"
  | "informational";

export type FindingCategory =
  | "cve"
  | "bloat"
  | "base_image"
  | "best_practice"
  | "compliance"
  | "secret";

export type AgentName =
  | "cve_analyst"
  | "bloat_detective"
  | "base_image_strategist"
  | "dockerfile_optimizer"
  | "risk_scorer";

export type EffortLevel = "low" | "medium" | "high";

export type DiffAnnotationCategory =
  | "security"
  | "bloat"
  | "cache"
  | "best-practice";

export interface Finding {
  id: string;
  severity: SeverityLevel;
  category: FindingCategory;
  title: string;
  detail: string;
  evidence: string;
  impact: string;
  fix: string;
  effort: EffortLevel;
  agent: AgentName;
  imageId?: string;
}

export interface Scores {
  security: number;
  bloat: number;
  freshness: number;
  bestPractices: number;
  overall: "A" | "B" | "C" | "D" | "F";
}

export interface DockerfileChange {
  lineNumber: number;
  category: DiffAnnotationCategory;
  what: string;
  why: string;
  estimatedSavings?: string;
}

export interface TopAction {
  rank: number;
  title: string;
  impact: string;
  effort: EffortLevel;
}

export interface ScanResult {
  scanId: string;
  repoId: string;
  imageId: string;
  scores: Scores;
  findings: Finding[];
  dockerfileOriginal: string;
  dockerfileOptimized: string;
  dockerfileChanges: DockerfileChange[];
  topActions: TopAction[];
  executiveSummary: string;
  scanDate: string;
  blocked: boolean;
  cveCount: { critical: number; high: number; medium: number; low: number };
  totalSizeReduction: number;
  estimatedFixTime: number;
}

export type ScanStatus = "queued" | "running" | "completed" | "failed";

export interface ScanJob {
  jobId: string;
  repoId: string;
  status: ScanStatus;
  progress: number;
  currentStep: string;
  startedAt: string;
  completedAt?: string;
  error?: string;
}

export interface ScoreHistory {
  date: string;
  security: number;
  bloat: number;
  freshness: number;
  bestPractices: number;
  deployMarker?: boolean;
}

export interface ScanProgressEvent {
  jobId: string;
  step: string;
  progress: number;
  status: ScanStatus;
  message: string;
  timestamp: string;
}

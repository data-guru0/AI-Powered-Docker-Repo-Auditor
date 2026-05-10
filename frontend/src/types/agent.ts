export interface AgentEvalScore {
  agentName: string;
  faithfulness: number;
  answerRelevancy: number;
  hallucinationScore: number;
  contextPrecision: number;
  contextRecall: number;
  answerCorrectness: number;
  timestamp: string;
  scanId: string;
}

export interface EvalTrend {
  date: string;
  agentName: string;
  averageScore: number;
}

export interface EvalSummary {
  totalEvaluations: number;
  flaggedResponses: number;
  worstPerformingAgent: string;
  scores: AgentEvalScore[];
  trends: EvalTrend[];
}

export interface CVEFinding {
  cveId: string;
  severity: string;
  description: string;
  affectedPackage: string;
  affectedVersion: string;
  fixVersion: string;
  epssScore: number;
  isInKEV: boolean;
  exploitabilityReasoning: string;
  cvssScore: number;
  nvdUrl: string;
  isRegression: boolean;
}

export interface BloatFinding {
  layerDigest: string;
  layerCommand: string;
  layerIndex: number;
  sizeImpact: number;
  description: string;
  rootCause: string;
  fix: string;
  isGhostFile: boolean;
}

export interface MigrationOption {
  targetImage: string;
  sizeDelta: number;
  compatibility: string;
  securityImprovement: string;
  tradeoffs: string;
}

export interface BaseImageAnalysis {
  currentImage: string;
  currentDigest: string;
  currentVersion: string;
  latestVersion: string;
  isEOL: boolean;
  eolDate?: string;
  hasMutableTag: boolean;
  migrationOptions: MigrationOption[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  sources?: string[];
}

export interface ChatRequest {
  message: string;
  conversationHistory: ChatMessage[];
  repoScope?: string[];
}

export interface ComplianceCheck {
  checkId: string;
  title: string;
  description: string;
  status: "pass" | "fail" | "warn" | "na";
  severity: string;
  remediation: string;
}

export interface CostIntelligence {
  currentMonthlyCost: number;
  projectedSavings: number;
  unusedImages: number;
  unusedImageSize: number;
  recommendations: string[];
}

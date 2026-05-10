"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import { scansApi } from "@/lib/api";
import { RingScore } from "@/components/dashboard/RingScore";
import { GradeDisplay } from "@/components/dashboard/GradeDisplay";
import { ScanHistoryChart } from "@/components/dashboard/ScanHistoryChart";
import { CVEBreakdownChart } from "@/components/dashboard/CVEBreakdownChart";
import { LayerBloatHeatmap } from "@/components/dashboard/LayerBloatHeatmap";
import { FindingsTable } from "@/components/dashboard/FindingsTable";
import { ImageInventoryCard } from "@/components/dashboard/cards/ImageInventoryCard";
import { CriticalAlertsCard } from "@/components/dashboard/cards/CriticalAlertsCard";
import { SizeOverviewCard } from "@/components/dashboard/cards/SizeOverviewCard";
import { BaseImageHealthCard } from "@/components/dashboard/cards/BaseImageHealthCard";
import { TopRiskiestCard } from "@/components/dashboard/cards/TopRiskiestCard";
import { UnusedImagesCard } from "@/components/dashboard/cards/UnusedImagesCard";
import { AIRecommendationsCard } from "@/components/dashboard/cards/AIRecommendationsCard";
import { ComplianceStatusCard } from "@/components/dashboard/cards/ComplianceStatusCard";
import { CostIntelligenceCard } from "@/components/dashboard/cards/CostIntelligenceCard";
import { ScanProgress } from "@/components/ui/ScanProgress";
import { ChatAgent } from "@/components/ui/ChatAgent";
import type { ScanResult } from "@/types/scan";

function scoreReasons(scan: ScanResult) {
  const { cveCount, findings, totalSizeReduction, scores } = scan;

  // Security
  const securityReason =
    cveCount.critical > 0
      ? `${cveCount.critical} critical, ${cveCount.high} high CVEs found`
      : cveCount.high > 0
      ? `${cveCount.high} high severity CVEs`
      : cveCount.medium > 0
      ? `${cveCount.medium} medium severity CVEs only`
      : "No significant CVEs detected";

  // Bloat
  const bloatFindings = findings.filter((f) => f.category === "bloat");
  const mbReduction = Math.round(totalSizeReduction / 1024 / 1024);
  const bloatReason =
    bloatFindings.length > 0
      ? `${bloatFindings.length} bloat source${bloatFindings.length > 1 ? "s" : ""}${mbReduction > 0 ? `, ~${mbReduction}MB reclaimable` : ""}`
      : "Minimal unnecessary layers";

  // Freshness
  const baseFindings = findings.filter((f) => f.category === "base_image");
  const freshnessReason =
    baseFindings.length > 0
      ? baseFindings[0].title?.split(".")[0] || "Base image needs updating"
      : "Base image is current";

  // Best Practices
  const bpFindings = findings.filter((f) => f.category === "best_practice");
  const bestPracticesReason =
    bpFindings.length > 0
      ? `${bpFindings.length} best practice violation${bpFindings.length > 1 ? "s" : ""}`
      : scores.bestPractices < 70
      ? "Several Dockerfile improvements needed"
      : "Following Docker best practices";

  return { securityReason, bloatReason, freshnessReason, bestPracticesReason };
}

export default function RepoDashboardPage() {
  const { repoId } = useParams<{ repoId: string }>();
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"dashboard" | "chat">("dashboard");
  const [error, setError] = useState<string | null>(null);

  const loadLatestScan = useCallback(async () => {
    try {
      const result = await scansApi.getLatestScan(repoId);
      setScanResult(result);
    } catch {
      setError("Failed to load scan results");
    } finally {
      setLoading(false);
    }
  }, [repoId]);

  useEffect(() => {
    loadLatestScan();
  }, [loadLatestScan]);

  async function startScan() {
    setScanning(true);
    setError(null);
    try {
      const job = await scansApi.startScan(repoId);
      setCurrentJobId(job.jobId);
    } catch {
      setError("Failed to start scan");
      setScanning(false);
    }
  }

  function onScanComplete(jobId: string) {
    setScanning(false);
    setCurrentJobId(null);
    scansApi.getScanResult(jobId).then(setScanResult).catch(() => {});
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin" />
          <span className="text-text-secondary">Loading dashboard...</span>
        </div>
      </div>
    );
  }

  const reasons = scanResult ? scoreReasons(scanResult) : null;

  return (
    <div className="p-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-text-primary font-mono">{repoId}</h1>
          {scanResult && (
            <p className="text-text-secondary text-sm mt-0.5">
              Last scanned {new Date(scanResult.scanDate).toLocaleString()}
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab(activeTab === "dashboard" ? "chat" : "dashboard")}
            className="px-4 py-2 rounded-lg border border-surface-border text-text-secondary text-sm hover:text-text-primary hover:border-surface-border-bright transition-colors"
          >
            {activeTab === "dashboard" ? "Chat Agent" : "Dashboard"}
          </button>
          <button
            onClick={startScan}
            disabled={scanning}
            className="px-4 py-2 rounded-lg bg-accent-cyan text-bg-base font-semibold text-sm hover:bg-accent-cyan-dim transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {scanning ? "Scanning..." : "Run Scan"}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-accent-red/10 border border-accent-red/30 text-accent-red text-sm">
          {error}
        </div>
      )}

      {scanning && currentJobId && (
        <ScanProgress jobId={currentJobId} onComplete={onScanComplete} />
      )}

      {activeTab === "chat" ? (
        <ChatAgent repoId={repoId} />
      ) : scanResult ? (
        <>
          {scanResult.blocked && (
            <div className="p-4 rounded-lg bg-severity-critical/10 border border-severity-critical/30 text-severity-critical text-sm font-medium">
              This image is blocked from production deployment based on your configured policy thresholds.
            </div>
          )}

          {/* Row 1: Grade + Score Rings */}
          <div className="bg-bg-card border border-surface-border rounded-xl p-6">
            <div className="flex flex-col lg:flex-row gap-6 items-center">
              <GradeDisplay grade={scanResult.scores.overall} summary={scanResult.executiveSummary} />
              <div className="flex-1 grid grid-cols-2 sm:grid-cols-4 gap-6 justify-items-center">
                <RingScore
                  label="Security"
                  score={scanResult.scores.security}
                  color="#ef4444"
                  reason={reasons?.securityReason}
                />
                <RingScore
                  label="Bloat"
                  score={scanResult.scores.bloat}
                  color="#f97316"
                  reason={reasons?.bloatReason}
                />
                <RingScore
                  label="Freshness"
                  score={scanResult.scores.freshness}
                  color="#00d4ff"
                  reason={reasons?.freshnessReason}
                />
                <RingScore
                  label="Best Practices"
                  score={scanResult.scores.bestPractices}
                  color="#8b5cf6"
                  reason={reasons?.bestPracticesReason}
                />
              </div>
            </div>
          </div>

          {/* Row 2: 4 stat cards */}
          <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
            <CriticalAlertsCard cveCount={scanResult.cveCount} />
            <SizeOverviewCard totalSizeReduction={scanResult.totalSizeReduction} />
            <BaseImageHealthCard scan={scanResult} />
            <ComplianceStatusCard scan={scanResult} />
          </div>

          {/* Row 3: History chart + CVE breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2">
              <ScanHistoryChart repoId={repoId} />
            </div>
            <CVEBreakdownChart cveCount={scanResult.cveCount} />
          </div>

          {/* Row 4: AI Recommendations + Layer Heatmap + Top Riskiest */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <AIRecommendationsCard topActions={scanResult.topActions} />
            <LayerBloatHeatmap repoId={repoId} />
            <TopRiskiestCard repoId={repoId} scan={scanResult} />
          </div>

          {/* Row 5: Image Inventory + Unused Images + Cost Intelligence */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <ImageInventoryCard repoId={repoId} />
            <UnusedImagesCard repoId={repoId} />
            <CostIntelligenceCard repoId={repoId} />
          </div>

          {/* Row 6: All Findings */}
          <div className="bg-bg-card border border-surface-border rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-surface-border">
              <h2 className="text-base font-semibold text-text-primary">All Findings</h2>
              <p className="text-text-secondary text-xs mt-0.5">
                {scanResult.findings.length} findings &bull;{" "}
                {scanResult.estimatedFixTime}h estimated fix time &bull;{" "}
                {(scanResult.totalSizeReduction / 1024 / 1024).toFixed(0)}MB potential reduction
              </p>
            </div>
            <FindingsTable findings={scanResult.findings} />
          </div>

        </>
      ) : (
        <div className="flex flex-col items-center justify-center h-64 gap-4">
          <p className="text-text-secondary">No scan results yet.</p>
          <button
            onClick={startScan}
            className="px-6 py-2.5 rounded-lg bg-accent-cyan text-bg-base font-semibold text-sm hover:bg-accent-cyan-dim transition-colors"
          >
            Run First Scan
          </button>
        </div>
      )}
    </div>
  );
}

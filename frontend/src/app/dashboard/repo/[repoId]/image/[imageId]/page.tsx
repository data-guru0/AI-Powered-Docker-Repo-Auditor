"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { imagesApi, scansApi } from "@/lib/api";
import { OverviewTab } from "@/components/image/OverviewTab";
import { LayersTab } from "@/components/image/LayersTab";
import { CVEsTab } from "@/components/image/CVEsTab";
import { SecretsTab } from "@/components/image/SecretsTab";
import { DockerfileTab } from "@/components/image/DockerfileTab";
import { HistoryTab } from "@/components/image/HistoryTab";
import type { ImageTag, LayerInfo } from "@/types/registry";
import type { ScanResult } from "@/types/scan";

type ImageDetailTab =
  | "overview"
  | "layers"
  | "cves"
  | "secrets"
  | "dockerfile"
  | "history";

const IMAGE_TABS: { id: ImageDetailTab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "layers", label: "Layers" },
  { id: "cves", label: "CVEs" },
  { id: "secrets", label: "Secrets" },
  { id: "dockerfile", label: "Dockerfile" },
  { id: "history", label: "History" },
];

export default function ImageDetailPage() {
  const { repoId, imageId } = useParams<{ repoId: string; imageId: string }>();
  const [activeTab, setActiveTab] = useState<ImageDetailTab>("overview");
  const [image, setImage] = useState<ImageTag | null>(null);
  const [layers, setLayers] = useState<LayerInfo[]>([]);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const [images, layerData, scan] = await Promise.all([
        imagesApi.list(repoId),
        imagesApi.getLayers(repoId, imageId),
        scansApi.getLatestScan(repoId),
      ]);
      const found = images.find((img) => img.id === imageId) || null;
      setImage(found);
      setLayers(layerData);
      setScanResult(scan);
    } catch {
      /* errors handled by individual tabs */
    } finally {
      setLoading(false);
    }
  }, [repoId, imageId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin" />
          <span className="text-text-secondary">Loading image details...</span>
        </div>
      </div>
    );
  }

  const imageFindings = scanResult?.findings.filter(
    (f) => f.imageId === imageId
  ) || [];

  return (
    <div className="flex flex-col h-full">
      <div className="px-6 py-4 border-b border-surface-border">
        <Link
          href={`/dashboard/repo/${repoId}`}
          className="text-text-secondary text-sm hover:text-text-primary transition-colors"
        >
          {repoId}
        </Link>
        <span className="text-text-muted mx-2">/</span>
        <span className="text-text-primary text-sm font-mono">
          {image?.tag || imageId}
        </span>
        {image && (
          <p className="text-text-muted text-xs mt-1 font-mono truncate max-w-lg">
            {image.digest}
          </p>
        )}
      </div>
      <div className="border-b border-surface-border">
        <nav className="flex gap-1 px-6">
          {IMAGE_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3.5 text-sm font-medium transition-colors border-b-2 ${
                activeTab === tab.id
                  ? "text-accent-cyan border-accent-cyan"
                  : "text-text-secondary border-transparent hover:text-text-primary"
              }`}
            >
              {tab.label}
              {tab.id === "cves" && imageFindings.length > 0 && (
                <span className="ml-1.5 px-1.5 py-0.5 rounded text-xs bg-accent-red/20 text-accent-red">
                  {imageFindings.filter((f) => f.category === "cve").length}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>
      <div className="flex-1 overflow-auto p-6">
        {activeTab === "overview" && <OverviewTab image={image} />}
        {activeTab === "layers" && <LayersTab layers={layers} />}
        {activeTab === "cves" && (
          <CVEsTab
            findings={imageFindings.filter((f) => f.category === "cve")}
            repoId={repoId}
            imageId={imageId}
          />
        )}
        {activeTab === "secrets" && <SecretsTab repoId={repoId} imageId={imageId} />}
        {activeTab === "dockerfile" && scanResult && (
          <DockerfileTab
            original={scanResult.dockerfileOriginal}
            optimized={scanResult.dockerfileOptimized}
            changes={scanResult.dockerfileChanges}
          />
        )}
        {activeTab === "history" && (
          <HistoryTab repoId={repoId} imageId={imageId} />
        )}
      </div>
    </div>
  );
}

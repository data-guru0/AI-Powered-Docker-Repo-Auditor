"use client";

import { useState } from "react";
import { ConnectionsTab } from "@/components/tabs/ConnectionsTab";
import { RepositoriesTab } from "@/components/tabs/RepositoriesTab";
import { WorkspaceTab } from "@/components/tabs/WorkspaceTab";

type Tab = "connections" | "repositories" | "workspace";

const TABS: { id: Tab; label: string }[] = [
  { id: "connections", label: "Connections" },
  { id: "repositories", label: "Repositories" },
  { id: "workspace", label: "Workspace" },
];

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<Tab>("connections");

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-surface-border bg-bg-base sticky top-0 z-10">
        <div className="px-6">
          <nav className="flex gap-1">
            {TABS.map((tab) => (
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
              </button>
            ))}
          </nav>
        </div>
      </div>
      <div className="flex-1 p-6 overflow-auto">
        {activeTab === "connections" && <ConnectionsTab />}
        {activeTab === "repositories" && <RepositoriesTab />}
        {activeTab === "workspace" && <WorkspaceTab />}
      </div>
    </div>
  );
}

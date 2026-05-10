"use client";

import { useState, useEffect } from "react";
import { connectionsApi } from "@/lib/api";
import type { Connection, DockerHubCredentials, ECRCredentials } from "@/types/registry";

export function ConnectionsTab() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [dockerhubForm, setDockerhubForm] = useState<DockerHubCredentials>({
    username: "",
    accessToken: "",
  });
  const [ecrForm, setEcrForm] = useState<ECRCredentials>({
    accessKeyId: "",
    secretAccessKey: "",
    region: "us-east-1",
  });
  const [dhLoading, setDhLoading] = useState(false);
  const [ecrLoading, setEcrLoading] = useState(false);
  const [dhError, setDhError] = useState<string | null>(null);
  const [ecrError, setEcrError] = useState<string | null>(null);

  useEffect(() => {
    connectionsApi.getStatus().then(setConnections).catch(() => {});
  }, []);

  const dhConnection = connections.find((c) => c.type === "dockerhub");
  const ecrConnection = connections.find((c) => c.type === "ecr");

  async function connectDockerHub() {
    setDhError(null);
    setDhLoading(true);
    try {
      const conn = await connectionsApi.connectDockerHub(dockerhubForm);
      setConnections((prev) => [
        ...prev.filter((c) => c.type !== "dockerhub"),
        conn,
      ]);
      setDockerhubForm({ username: "", accessToken: "" });
    } catch (err: unknown) {
      setDhError(err instanceof Error ? err.message : "Connection failed");
    } finally {
      setDhLoading(false);
    }
  }

  async function connectECR() {
    setEcrError(null);
    setEcrLoading(true);
    try {
      const conn = await connectionsApi.connectECR(ecrForm);
      setConnections((prev) => [
        ...prev.filter((c) => c.type !== "ecr"),
        conn,
      ]);
      setEcrForm({ accessKeyId: "", secretAccessKey: "", region: "us-east-1" });
    } catch (err: unknown) {
      setEcrError(err instanceof Error ? err.message : "Connection failed");
    } finally {
      setEcrLoading(false);
    }
  }

  async function disconnect(type: string) {
    try {
      await connectionsApi.disconnect(type);
      setConnections((prev) => prev.filter((c) => c.type !== type));
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div className="bg-bg-card border border-surface-border rounded-xl p-6">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-base font-semibold text-text-primary">DockerHub</h2>
            <p className="text-text-secondary text-sm mt-0.5">
              Connect your DockerHub account to browse and scan repositories
            </p>
          </div>
          <StatusBadge connection={dhConnection} />
        </div>

        {dhConnection?.status === "connected" ? (
          <div className="flex items-center justify-between p-3 rounded-lg bg-accent-green/5 border border-accent-green/20">
            <div>
              <p className="text-sm text-text-primary font-medium">
                {dhConnection.username}
              </p>
              <p className="text-xs text-text-secondary">
                Connected {dhConnection.connectedAt ? new Date(dhConnection.connectedAt).toLocaleDateString() : ""}
              </p>
            </div>
            <button
              onClick={() => disconnect("dockerhub")}
              className="text-xs text-accent-red hover:underline"
            >
              Disconnect
            </button>
          </div>
        ) : (
          <>
            {dhError && (
              <div className="mb-4 p-3 rounded-lg bg-accent-red/10 border border-accent-red/30 text-accent-red text-sm">
                {dhError}
              </div>
            )}
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1">
                  Username
                </label>
                <input
                  type="text"
                  value={dockerhubForm.username}
                  onChange={(e) =>
                    setDockerhubForm((p) => ({ ...p, username: e.target.value }))
                  }
                  className="w-full px-3 py-2 rounded-lg bg-bg-elevated border border-surface-border text-text-primary text-sm focus:outline-none focus:border-accent-cyan/60 transition-colors"
                  placeholder="dockerhub-username"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1">
                  Access Token
                </label>
                <input
                  type="password"
                  value={dockerhubForm.accessToken}
                  onChange={(e) =>
                    setDockerhubForm((p) => ({
                      ...p,
                      accessToken: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 rounded-lg bg-bg-elevated border border-surface-border text-text-primary text-sm focus:outline-none focus:border-accent-cyan/60 transition-colors"
                  placeholder="dckr_pat_..."
                />
              </div>
              <button
                onClick={connectDockerHub}
                disabled={
                  dhLoading ||
                  !dockerhubForm.username ||
                  !dockerhubForm.accessToken
                }
                className="w-full py-2 rounded-lg bg-accent-cyan text-bg-base font-semibold text-sm hover:bg-accent-cyan-dim transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {dhLoading ? "Connecting..." : "Connect DockerHub"}
              </button>
            </div>
          </>
        )}
      </div>

      <div className="bg-bg-card border border-surface-border rounded-xl p-6">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-base font-semibold text-text-primary">
              AWS ECR
            </h2>
            <p className="text-text-secondary text-sm mt-0.5">
              Connect Elastic Container Registry for ECR-native scanning
            </p>
          </div>
          <StatusBadge connection={ecrConnection} />
        </div>

        {ecrConnection?.status === "connected" ? (
          <div className="flex items-center justify-between p-3 rounded-lg bg-accent-green/5 border border-accent-green/20">
            <div>
              <p className="text-sm text-text-primary font-medium">
                Account {ecrConnection.accountId}
              </p>
              <p className="text-xs text-text-secondary">
                {ecrConnection.region} &bull; Connected{" "}
                {ecrConnection.connectedAt
                  ? new Date(ecrConnection.connectedAt).toLocaleDateString()
                  : ""}
              </p>
            </div>
            <button
              onClick={() => disconnect("ecr")}
              className="text-xs text-accent-red hover:underline"
            >
              Disconnect
            </button>
          </div>
        ) : (
          <>
            {ecrError && (
              <div className="mb-4 p-3 rounded-lg bg-accent-red/10 border border-accent-red/30 text-accent-red text-sm">
                {ecrError}
              </div>
            )}
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1">
                  AWS Access Key ID
                </label>
                <input
                  type="text"
                  value={ecrForm.accessKeyId}
                  onChange={(e) =>
                    setEcrForm((p) => ({ ...p, accessKeyId: e.target.value }))
                  }
                  className="w-full px-3 py-2 rounded-lg bg-bg-elevated border border-surface-border text-text-primary text-sm font-mono focus:outline-none focus:border-accent-cyan/60 transition-colors"
                  placeholder="AKIAIOSFODNN7EXAMPLE"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1">
                  AWS Secret Access Key
                </label>
                <input
                  type="password"
                  value={ecrForm.secretAccessKey}
                  onChange={(e) =>
                    setEcrForm((p) => ({
                      ...p,
                      secretAccessKey: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 rounded-lg bg-bg-elevated border border-surface-border text-text-primary text-sm focus:outline-none focus:border-accent-cyan/60 transition-colors"
                  placeholder="wJalrXUtnFEMI..."
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-text-secondary mb-1">
                  Region
                </label>
                <select
                  value={ecrForm.region}
                  onChange={(e) =>
                    setEcrForm((p) => ({ ...p, region: e.target.value }))
                  }
                  className="w-full px-3 py-2 rounded-lg bg-bg-elevated border border-surface-border text-text-primary text-sm focus:outline-none focus:border-accent-cyan/60 transition-colors"
                >
                  {[
                    "us-east-1","us-east-2","us-west-1","us-west-2",
                    "eu-west-1","eu-west-2","eu-central-1",
                    "ap-northeast-1","ap-southeast-1","ap-southeast-2",
                  ].map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={connectECR}
                disabled={
                  ecrLoading ||
                  !ecrForm.accessKeyId ||
                  !ecrForm.secretAccessKey
                }
                className="w-full py-2 rounded-lg bg-accent-cyan text-bg-base font-semibold text-sm hover:bg-accent-cyan-dim transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {ecrLoading ? "Connecting..." : "Connect ECR"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ connection }: { connection?: Connection }) {
  if (!connection || connection.status === "disconnected") {
    return (
      <span className="flex items-center gap-1.5 text-xs text-text-muted">
        <span className="w-1.5 h-1.5 rounded-full bg-text-muted" />
        Disconnected
      </span>
    );
  }
  if (connection.status === "validating") {
    return (
      <span className="flex items-center gap-1.5 text-xs text-accent-yellow">
        <span className="w-1.5 h-1.5 rounded-full bg-accent-yellow animate-pulse" />
        Validating
      </span>
    );
  }
  if (connection.status === "connected") {
    return (
      <span className="flex items-center gap-1.5 text-xs text-accent-green">
        <span className="w-1.5 h-1.5 rounded-full bg-accent-green" />
        Connected
      </span>
    );
  }
  return (
    <span className="flex items-center gap-1.5 text-xs text-accent-red">
      <span className="w-1.5 h-1.5 rounded-full bg-accent-red" />
      Error
    </span>
  );
}

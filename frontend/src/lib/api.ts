import { fetchAuthSession } from "aws-amplify/auth";
import type {
  DockerHubCredentials,
  ECRCredentials,
  Connection,
  Repository,
  WorkspaceRepo,
  ImageTag,
  LayerInfo,
} from "@/types/registry";
import type { ScanJob, ScanResult, ScoreHistory } from "@/types/scan";
import type { ChatRequest, ChatMessage } from "@/types/agent";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL;

async function getAuthHeaders(): Promise<Record<string, string>> {
  const session = await fetchAuthSession();
  const token = session.tokens?.idToken?.toString();
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { ...headers, ...options.headers },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export const connectionsApi = {
  connectDockerHub: (credentials: DockerHubCredentials): Promise<Connection> =>
    request("/api/v1/connections/dockerhub", {
      method: "POST",
      body: JSON.stringify(credentials),
    }),

  connectECR: (credentials: ECRCredentials): Promise<Connection> =>
    request("/api/v1/connections/ecr", {
      method: "POST",
      body: JSON.stringify(credentials),
    }),

  getStatus: (): Promise<Connection[]> =>
    request("/api/v1/connections/status"),

  disconnect: (type: string): Promise<void> =>
    request(`/api/v1/connections/${type}`, { method: "DELETE" }),
};

export const repositoriesApi = {
  list: (registryType: string): Promise<Repository[]> =>
    request(`/api/v1/repositories?registry_type=${registryType}`),
};

export const workspaceApi = {
  listRepos: (): Promise<WorkspaceRepo[]> =>
    request("/api/v1/workspace/repos"),

  addRepo: (repoId: string): Promise<WorkspaceRepo> =>
    request(`/api/v1/workspace/repos/${repoId}`, { method: "POST" }),

  removeRepo: (repoId: string): Promise<void> =>
    request(`/api/v1/workspace/repos/${repoId}`, { method: "DELETE" }),
};

export const scansApi = {
  startScan: (repoId: string, imageId?: string): Promise<ScanJob> =>
    request("/api/v1/scans", {
      method: "POST",
      body: JSON.stringify({ repo_id: repoId, image_id: imageId }),
    }),

  getScanResult: (scanId: string): Promise<ScanResult> =>
    request(`/api/v1/scans/${scanId}`),

  getScanHistory: (repoId: string): Promise<ScoreHistory[]> =>
    request(`/api/v1/scans/history/${repoId}`),

  getLatestScan: (repoId: string): Promise<ScanResult | null> =>
    request(`/api/v1/scans/latest/${repoId}`),
};

export const imagesApi = {
  list: (repoId: string): Promise<ImageTag[]> =>
    request(`/api/v1/images/${repoId}`),

  getLayers: (repoId: string, imageId: string): Promise<LayerInfo[]> =>
    request(`/api/v1/images/${repoId}/${imageId}/layers`),
};

export const chatApi = {
  send: (payload: ChatRequest): Promise<ChatMessage> =>
    request("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

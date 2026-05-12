export type RegistryType = "dockerhub" | "ecr";
export type ConnectionStatus =
  | "connected"
  | "disconnected"
  | "validating"
  | "error";

export interface Connection {
  type: RegistryType;
  status: ConnectionStatus;
  connectedAt?: string;
  username?: string;
  region?: string;
  accountId?: string;
  errorMessage?: string;
}

export interface DockerHubCredentials {
  username: string;
  accessToken: string;
}

export interface ECRCredentials {
  accessKeyId: string;
  secretAccessKey: string;
  region: string;
}

export interface Repository {
  id: string;
  name: string;
  registryType: RegistryType;
  imageCount: number;
  lastPushed: string;
  totalSize: number;
  inWorkspace: boolean;
  isPrivate: boolean;
}

export interface WorkspaceRepo {
  id: string;
  repoId: string;
  name: string;
  registryType: RegistryType;
  lastScanDate?: string;
  overallGrade?: string;
  criticalCveCount: number;
  addedAt: string;
}

export interface ImageTag {
  id: string;
  repoId: string;
  tag: string;
  digest: string;
  size: number;
  os: string;
  architecture: string;
  createdAt: string;
  pushedAt: string;
  baseImage: string;
  compressed: boolean;
}

export interface LayerInfo {
  index: number;
  digest: string;
  size: number;
  command: string;
  createdAt: string;
  mediaType: string;
}

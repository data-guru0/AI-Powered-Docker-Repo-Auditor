from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class RegistryType(str, Enum):
    DOCKERHUB = "dockerhub"
    ECR = "ecr"


class ConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    VALIDATING = "validating"
    ERROR = "error"


class DockerHubCredentials(BaseModel):
    username: str = Field(min_length=1)
    accessToken: str = Field(min_length=1)


class ECRCredentials(BaseModel):
    accessKeyId: str = Field(min_length=16)
    secretAccessKey: str = Field(min_length=1)
    region: str = Field(min_length=1)


class Connection(BaseModel):
    type: RegistryType
    status: ConnectionStatus
    connectedAt: Optional[str] = None
    username: Optional[str] = None
    region: Optional[str] = None
    accountId: Optional[str] = None
    errorMessage: Optional[str] = None


class Repository(BaseModel):
    id: str
    name: str
    registryType: RegistryType
    imageCount: int
    lastPushed: str
    totalSize: int
    inWorkspace: bool = False
    isPrivate: bool = False


class WorkspaceRepo(BaseModel):
    id: str
    repoId: str
    name: str
    registryType: RegistryType
    lastScanDate: Optional[str] = None
    overallGrade: Optional[str] = None
    criticalCveCount: int = 0
    addedAt: str


class ImageTag(BaseModel):
    id: str
    repoId: str
    tag: str
    digest: str
    size: int
    os: str = "linux"
    architecture: str = "amd64"
    createdAt: str
    pushedAt: str
    baseImage: str = ""
    compressed: bool = True


class LayerInfo(BaseModel):
    index: int
    digest: str
    size: int
    command: str
    createdAt: str
    mediaType: str = "application/vnd.docker.image.rootfs.diff.tar.gzip"

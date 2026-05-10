from fastapi import APIRouter
from app.api.v1 import connections, repositories, workspace, scans, images, ws_events

api_router = APIRouter()
api_router.include_router(connections.router, prefix="/connections", tags=["connections"])
api_router.include_router(repositories.router, prefix="/repositories", tags=["repositories"])
api_router.include_router(workspace.router, prefix="/workspace", tags=["workspace"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
api_router.include_router(images.router, prefix="/images", tags=["images"])
api_router.include_router(ws_events.router, tags=["websocket"])

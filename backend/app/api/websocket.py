from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging

logger = logging.getLogger(__name__)
websocket_router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self._job_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        if job_id not in self._job_connections:
            self._job_connections[job_id] = []
        self._job_connections[job_id].append(websocket)

    def disconnect(self, websocket: WebSocket, job_id: str):
        if job_id in self._job_connections:
            self._job_connections[job_id] = [
                ws for ws in self._job_connections[job_id] if ws is not websocket
            ]

    async def broadcast(self, job_id: str, data: dict):
        connections = self._job_connections.get(job_id, [])
        dead: list[WebSocket] = []
        for ws in connections:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, job_id)


manager = ConnectionManager()


@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    job_id: str = ""
    try:
        await websocket.accept()
        raw = await websocket.receive_text()
        message = json.loads(raw)

        if message.get("action") == "subscribe":
            job_id = message.get("jobId", "")
            if not job_id:
                await websocket.close(code=1008)
                return

            await manager.connect(websocket, job_id)
            await websocket.send_text(
                json.dumps({"status": "subscribed", "jobId": job_id})
            )

            while True:
                await websocket.receive_text()

    except WebSocketDisconnect:
        if job_id:
            manager.disconnect(websocket, job_id)
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
        if job_id:
            manager.disconnect(websocket, job_id)

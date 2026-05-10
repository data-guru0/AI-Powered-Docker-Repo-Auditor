from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.middleware import RequestIdMiddleware
from app.api.v1.router import api_router
from app.api.websocket import websocket_router
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Docker Image Auditor API")
    yield
    logger.info("Shutting down Docker Image Auditor API")


app = FastAPI(
    title="Docker Image Auditor API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(RequestIdMiddleware)

app.include_router(api_router, prefix="/api/v1")
app.include_router(websocket_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok", "version": "1.0.0"}

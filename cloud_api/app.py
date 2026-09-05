"""Phase 1 cloud heartbeat API — separate from the local FastAPI agent."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from cloud_api.cors import resolve_cors_origins
from cloud_api.store import HeartbeatStore

ONLINE_TIMEOUT_SECONDS = 30.0


class HeartbeatRequest(BaseModel):
    device_id: str = Field(min_length=1, max_length=128)
    timestamp: str | None = Field(default=None, max_length=64)
    status: str = Field(default="online", max_length=32)


def create_cloud_app(
    store: HeartbeatStore | None = None,
    *,
    online_timeout_seconds: float = ONLINE_TIMEOUT_SECONDS,
    web_origins: list[str] | None = None,
) -> FastAPI:
    resolved = store or HeartbeatStore(online_timeout_seconds=online_timeout_seconds)
    origins = web_origins if web_origins is not None else resolve_cors_origins()
    app = FastAPI(
        title="AminVC Agent Cloud",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.heartbeat_store = resolved
    app.state.cors_origins = origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Accept"],
    )

    @app.post("/agent/heartbeat")
    def post_heartbeat(body: HeartbeatRequest) -> dict[str, str | bool]:
        seen = resolved.record(body.device_id, body.timestamp)
        return {
            "device_id": body.device_id,
            "accepted": True,
            "last_seen": seen.isoformat(),
        }

    @app.get("/agent/status/{device_id}")
    def get_status(device_id: str) -> dict[str, str | bool | None]:
        return resolved.status(device_id)

    return app


app = create_cloud_app()

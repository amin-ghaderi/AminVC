"""API route modules."""

from fastapi import APIRouter

from app.api.routes import (
    builds,
    chunks,
    events,
    health,
    parts,
    projects,
    queue,
    recovery,
    worker,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(projects.router)
api_router.include_router(parts.router)
api_router.include_router(chunks.router)
api_router.include_router(queue.router)
api_router.include_router(worker.router)
api_router.include_router(builds.router)
api_router.include_router(recovery.router)
api_router.include_router(events.router)

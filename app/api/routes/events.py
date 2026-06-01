"""Event history routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_services
from app.api.mappers import event_response
from app.api.schemas.common import EventEnvelopeResponse
from app.api.services import ApplicationServices

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/recent", response_model=list[EventEnvelopeResponse])
def recent_events(
    limit: int = Query(100, ge=1, le=1000),
    services: ApplicationServices = Depends(get_services),
) -> list[EventEnvelopeResponse]:
    events = services.event_bus.store.recent(limit)
    return [event_response(e) for e in events]

"""E7.0 central service registry — single composition root for the API."""

from __future__ import annotations

from dataclasses import dataclass

from app.config.settings import AppSettings
from app.events.bus import EventBus
from app.lifecycle import ApprovalService, RebuildService
from app.queue.manager import QueueManager
from app.recovery.recovery_service import RecoveryService
from app.services.storage_service import StorageService
from app.storage.project_store import ProjectStore
from app.worker.execution_engine import WorkerExecutionEngine


@dataclass(slots=True)
class ApplicationServices:
    settings: AppSettings
    project_store: ProjectStore
    storage: StorageService
    event_bus: EventBus
    queue: QueueManager
    recovery: RecoveryService
    approval: ApprovalService
    rebuild: RebuildService
    worker: WorkerExecutionEngine

    @classmethod
    def create(cls, settings: AppSettings | None = None) -> ApplicationServices:
        settings = settings or AppSettings()
        event_bus = EventBus()
        project_store = ProjectStore(settings)
        storage = StorageService(settings)
        queue = QueueManager(
            project_store=project_store,
            event_bus=event_bus,
        )
        recovery = RecoveryService(
            store=project_store,
            event_bus=event_bus,
        )
        approval = ApprovalService(project_store, event_bus=event_bus)
        rebuild = RebuildService(project_store, event_bus=event_bus)
        worker = WorkerExecutionEngine(
            queue=queue,
            recovery=recovery,
            project_store=project_store,
            event_bus=event_bus,
        )
        return cls(
            settings=settings,
            project_store=project_store,
            storage=storage,
            event_bus=event_bus,
            queue=queue,
            recovery=recovery,
            approval=approval,
            rebuild=rebuild,
            worker=worker,
        )

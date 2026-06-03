"""E7.0 central service registry — single composition root for the API."""

from __future__ import annotations

from dataclasses import dataclass

from app.config.settings import AppSettings
from app.events.bus import EventBus
from app.lifecycle import ApprovalService, RebuildService
from app.queue.manager import QueueManager
from app.queue.store import QueueStore
from app.recovery.recovery_service import RecoveryService
from app.services.audio_asset_service import AudioAssetService
from app.services.part_summary_service import PartSummaryService
from app.services.part_text_service import PartTextService
from app.services.queue_query_service import QueueQueryService
from app.services.reference_audio_service import ReferenceAudioService
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
    queue_query: QueueQueryService
    audio_assets: AudioAssetService
    part_summary: PartSummaryService
    part_text: PartTextService
    reference_audio: ReferenceAudioService

    @classmethod
    def create(cls, settings: AppSettings | None = None) -> ApplicationServices:
        settings = settings or AppSettings()
        event_bus = EventBus()
        project_store = ProjectStore(settings)
        storage = StorageService(settings)
        queue_store = QueueStore(settings)
        queue = QueueManager(
            store=queue_store,
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
            queue_query=QueueQueryService(queue_store),
            audio_assets=AudioAssetService(project_store),
            part_summary=PartSummaryService(project_store),
            part_text=PartTextService(project_store),
            reference_audio=ReferenceAudioService(project_store),
        )

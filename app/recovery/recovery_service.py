"""
RecoveryService — manifest-driven recovery and resume planning (E2.0).
"""

from __future__ import annotations

from pathlib import Path

from app.config.settings import AppSettings
from app.contracts.manifests import ChunkManifest
from app.contracts.recovery import (
    PartScanResult,
    ProjectScanResult,
    RecoveryCategory,
    RecoveryReport,
    RestartPlan,
    ResumePlan,
)
from app.contracts.recovery_rules import narration_asset_complete
from app.contracts.states import (
    STATE_INTERRUPTED,
    STATE_NARRATION_FAILED,
    STATE_VC_FAILED,
)
from app.events.bus import EventBus
from app.recovery.events import publish_restart_plan_created, publish_resume_plan_created
from app.recovery.scanner import RecoveryScanner
from app.services.storage_service import StorageService
from app.storage.project_store import ProjectStore

MAX_CHUNK_RETRIES = 5


class RecoveryService:
    def __init__(
        self,
        store: ProjectStore | None = None,
        scanner: RecoveryScanner | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        settings = AppSettings()
        self._store = store if store is not None else ProjectStore(settings)
        self._storage = StorageService(settings)
        self._event_bus = event_bus
        self._scanner = scanner or RecoveryScanner(self._store, event_bus=event_bus)

    def _ensure_part(self, project_id: str, part_id: str) -> None:
        self._storage.ensure_part_tree(project_id, part_id)

    def scan_project(self, project_id: str) -> ProjectScanResult:
        return self._scanner.scan_project(project_id)

    def scan_part(self, project_id: str, part_id: str) -> PartScanResult:
        self._ensure_part(project_id, part_id)
        return self._scanner.scan_part(project_id, part_id)

    def build_recovery_report(self, project_id: str, part_id: str) -> RecoveryReport:
        scan = self.scan_part(project_id, part_id)
        return self._report_from_scan(scan)

    def create_resume_plan(self, project_id: str, part_id: str) -> ResumePlan:
        scan = self.scan_part(project_id, part_id)
        report = self._report_from_scan(scan)
        if report.next_chunk is None:
            plan = ResumePlan(
                project_id=project_id,
                part_id=part_id,
                start_chunk=0,
                remaining_chunks=[],
            )
            publish_resume_plan_created(self._event_bus, plan)
            return plan
        ordered = sorted(r.chunk_id for r in scan.chunks)
        remaining = [
            cid
            for cid in ordered
            if cid >= report.next_chunk
            and cid not in report.completed_chunks
            and cid not in report.failed_chunks
        ]
        plan = ResumePlan(
            project_id=project_id,
            part_id=part_id,
            start_chunk=report.next_chunk,
            remaining_chunks=remaining,
        )
        publish_resume_plan_created(self._event_bus, plan)
        return plan

    def create_restart_plan(self, project_id: str, part_id: str) -> RestartPlan:
        chunks = self._store.list_chunks(project_id, part_id)
        plan = RestartPlan(
            project_id=project_id,
            part_id=part_id,
            chunks=sorted(c.chunk_id for c in chunks),
        )
        publish_restart_plan_created(self._event_bus, plan)
        return plan

    def apply_resume_preparation(self, project_id: str, part_id: str) -> ResumePlan:
        """
        Scan, increment retry_count on interrupted chunks in resume scope, persist failures.
        Returns an updated resume plan after preparation.
        """
        self.scan_part(project_id, part_id)
        plan = self.create_resume_plan(project_id, part_id)
        for chunk_id in plan.remaining_chunks:
            chunk = self._store.load_chunk(project_id, part_id, chunk_id)
            if chunk.state != STATE_INTERRUPTED:
                continue
            chunk.retry_count += 1
            if chunk.retry_count > MAX_CHUNK_RETRIES:
                narr_path, vc_path = self._asset_paths(project_id, part_id, chunk)
                chunk.state = (
                    STATE_NARRATION_FAILED
                    if not narration_asset_complete(chunk, narr_path)
                    else STATE_VC_FAILED
                )
            self._store.save_chunk(project_id, part_id, chunk)
        return self.create_resume_plan(project_id, part_id)

    def _report_from_scan(self, scan: PartScanResult) -> RecoveryReport:
        completed: list[int] = []
        interrupted: list[int] = []
        failed: list[int] = []
        pending: list[int] = []
        for result in scan.chunks:
            if result.category == RecoveryCategory.COMPLETED:
                completed.append(result.chunk_id)
            elif result.category == RecoveryCategory.INTERRUPTED:
                interrupted.append(result.chunk_id)
            elif result.category == RecoveryCategory.FAILED:
                failed.append(result.chunk_id)
            elif result.category == RecoveryCategory.PENDING:
                pending.append(result.chunk_id)

        completed.sort()
        interrupted.sort()
        failed.sort()
        pending.sort()

        last_completed = completed[-1] if completed else None
        ordered_ids = sorted(r.chunk_id for r in scan.chunks)
        next_chunk: int | None = None
        for cid in ordered_ids:
            if cid not in completed:
                next_chunk = cid
                break

        return RecoveryReport(
            project_id=scan.project_id,
            part_id=scan.part_id,
            last_completed_chunk=last_completed,
            next_chunk=next_chunk,
            interrupted_chunks=interrupted,
            failed_chunks=failed,
            pending_chunks=pending,
            completed_chunks=completed,
        )

    def _asset_paths(
        self,
        project_id: str,
        part_id: str,
        chunk: ChunkManifest,
    ) -> tuple[Path, Path]:
        pl = self._store.part_layout(project_id, part_id)
        narration = (
            self._store.resolve_part_path(project_id, part_id, chunk.narration.file)
            if chunk.narration.file
            else pl.narration_wav_path(chunk.chunk_id)
        )
        vc = (
            self._store.resolve_part_path(project_id, part_id, chunk.vc.file)
            if chunk.vc.file
            else pl.vc_wav_path(chunk.chunk_id)
        )
        return narration, vc

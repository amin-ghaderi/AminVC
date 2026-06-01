"""Shared API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str


class HealthResponse(BaseModel):
    status: str = "ok"


class VersionResponse(BaseModel):
    version: str


class AssetSlotResponse(BaseModel):
    status: str = ""
    file: str | None = None
    duration_seconds: float | None = None


class ProjectResponse(BaseModel):
    project_id: str
    title: str = ""
    created_at: str = ""
    updated_at: str = ""
    status: str = "active"
    parts: list[str] = Field(default_factory=list)


class CreateProjectRequest(BaseModel):
    project_id: str
    title: str = ""


class PartResponse(BaseModel):
    part_id: str
    project_id: str
    title: str = ""
    state: str = ""
    processing_profile: str = ""
    chunks_total: int = 0
    chunks_completed_narration: int = 0
    chunks_completed_vc: int = 0
    current_chunk: int | None = None
    created_at: str = ""
    updated_at: str = ""


class CreatePartRequest(BaseModel):
    part_id: str | None = None
    title: str = ""


class ChunkResponse(BaseModel):
    chunk_id: int
    state: str
    narration_approved: bool = False
    vc_approved: bool = False
    text: str = ""
    narration: AssetSlotResponse
    vc: AssetSlotResponse
    retry_count: int = 0
    last_error: str | None = None
    updated_at: str = ""


class UpdateChunkTextRequest(BaseModel):
    text: str


class PartTextResponse(BaseModel):
    text: str
    source: str


class SavePartTextRequest(BaseModel):
    text: str


class SourceUploadResponse(BaseModel):
    filename: str
    size_bytes: int
    path: str


class QueueSnapshotResponse(BaseModel):
    queued: int
    running: int
    completed: int
    failed: int
    cancelled: int


class QueueJobRequest(BaseModel):
    project_id: str
    part_id: str
    chunk_id: int


class QueueResumeRequest(BaseModel):
    project_id: str
    part_id: str
    job_type: str = "narration"


class QueueJobResponse(BaseModel):
    job_id: str
    project_id: str
    part_id: str
    chunk_id: int | None = None
    job_type: str
    status: str


class WorkerStatusResponse(BaseModel):
    running: bool
    state: str


class BuildResponse(BaseModel):
    build_id: str
    project_id: str
    part_id: str
    name: str = ""
    created_at: str = ""
    updated_at: str = ""
    chunks: list[int] = Field(default_factory=list)
    output_file: str = ""
    duration_seconds: float | None = None


class CreateBuildRequest(BaseModel):
    name: str
    chunks: list[int]
    build_id: str | None = None


class RecoveryReportResponse(BaseModel):
    project_id: str
    part_id: str
    last_completed_chunk: int | None = None
    next_chunk: int | None = None
    interrupted_chunks: list[int] = Field(default_factory=list)
    failed_chunks: list[int] = Field(default_factory=list)
    pending_chunks: list[int] = Field(default_factory=list)
    completed_chunks: list[int] = Field(default_factory=list)


class ResumePlanResponse(BaseModel):
    project_id: str
    part_id: str
    start_chunk: int
    remaining_chunks: list[int]


class RestartPlanResponse(BaseModel):
    project_id: str
    part_id: str
    chunks: list[int]


class QueueJobRow(BaseModel):
    job_id: str
    job_type: str
    project_id: str
    part_id: str
    chunk_id: int | None = None
    status: str
    created_at: str = ""
    started_at: str | None = None
    completed_at: str | None = None
    attempts: int = 0
    last_error: str | None = None


class QueueJobsResponse(BaseModel):
    queued: list[QueueJobRow]
    running: list[QueueJobRow]
    completed: list[QueueJobRow]
    failed: list[QueueJobRow]
    cancelled: list[QueueJobRow]


class ExtractTextResponse(BaseModel):
    text: str


class ChunkingRequest(BaseModel):
    text: str
    chunk_size: int


class ChunkingResponse(BaseModel):
    chunks_created: int


class PartSummaryResponse(BaseModel):
    total_chunks: int
    narration_ready: int
    narration_approved: int
    vc_ready: int
    vc_approved: int
    failed: int
    interrupted: int


class ChunkAssetsResponse(BaseModel):
    narration_exists: bool
    vc_exists: bool
    narration_url: str
    vc_url: str
    narration_size: int | None = None
    vc_size: int | None = None


class EventEnvelopeResponse(BaseModel):
    event_id: str
    event_type: str
    timestamp: str
    project_id: str | None = None
    part_id: str | None = None
    chunk_id: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

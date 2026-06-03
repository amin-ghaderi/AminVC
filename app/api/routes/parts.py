"""Part, source, and part-level text routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse

from app.api.dependencies import get_services
from app.api.mappers import part_response
from app.api.schemas.common import (
    ChunkingRequest,
    ChunkingResponse,
    CreatePartRequest,
    ExtractTextResponse,
    PartResponse,
    PartSummaryResponse,
    PartTextResponse,
    ReferenceAudioDeleteResponse,
    ReferenceAudioUploadResponse,
    SavePartTextRequest,
    SourceUploadResponse,
)
from app.api.services import ApplicationServices
from app.contracts.manifests import PartManifest
from app.storage.layout import EDITED_TEXT_NAME, EXTRACTED_TEXT_NAME

router = APIRouter(prefix="/projects/{project_id}/parts", tags=["parts"])


def _part_response(
    services: ApplicationServices,
    manifest: PartManifest,
) -> PartResponse:
    meta = services.reference_audio.reference_metadata(
        manifest.project_id,
        manifest.part_id,
    )
    return part_response(manifest, reference_audio=meta)


@router.get("", response_model=list[PartResponse])
def list_parts(
    project_id: str,
    services: ApplicationServices = Depends(get_services),
) -> list[PartResponse]:
    return [
        _part_response(services, p)
        for p in services.project_store.list_parts(project_id)
    ]


@router.post("", response_model=PartResponse, status_code=201)
def create_part(
    project_id: str,
    body: CreatePartRequest,
    services: ApplicationServices = Depends(get_services),
) -> PartResponse:
    manifest = services.project_store.create_part(
        project_id,
        part_id=body.part_id,
        title=body.title,
    )
    return _part_response(services, manifest)


@router.get("/{part_id}", response_model=PartResponse)
def get_part(
    project_id: str,
    part_id: str,
    services: ApplicationServices = Depends(get_services),
) -> PartResponse:
    manifest = services.project_store.load_part(project_id, part_id)
    return _part_response(services, manifest)


@router.post("/{part_id}/reference", response_model=ReferenceAudioUploadResponse)
async def upload_reference_audio(
    project_id: str,
    part_id: str,
    file: UploadFile = File(...),
    services: ApplicationServices = Depends(get_services),
) -> ReferenceAudioUploadResponse:
    services.storage.ensure_part_tree(project_id, part_id)
    data = await file.read()
    result = services.reference_audio.upload_reference_audio(
        project_id,
        part_id,
        data,
    )
    return ReferenceAudioUploadResponse(
        filename=result.filename,
        size_bytes=result.size_bytes,
        path=result.path,
    )


@router.get("/{part_id}/reference")
def download_reference_audio(
    project_id: str,
    part_id: str,
    services: ApplicationServices = Depends(get_services),
) -> FileResponse:
    path = services.reference_audio.reference_path(project_id, part_id)
    return FileResponse(path, media_type="audio/wav", filename=path.name)


@router.delete("/{part_id}/reference", response_model=ReferenceAudioDeleteResponse)
def delete_reference_audio(
    project_id: str,
    part_id: str,
    services: ApplicationServices = Depends(get_services),
) -> ReferenceAudioDeleteResponse:
    services.reference_audio.delete_reference_audio(project_id, part_id)
    return ReferenceAudioDeleteResponse()


@router.post("/{part_id}/source", response_model=SourceUploadResponse)
async def upload_source(
    project_id: str,
    part_id: str,
    file: UploadFile = File(...),
    services: ApplicationServices = Depends(get_services),
) -> SourceUploadResponse:
    pl = services.storage.ensure_part_tree(project_id, part_id)
    data = await file.read()
    pl.source_pdf_path.write_bytes(data)
    return SourceUploadResponse(
        filename=file.filename or "source.pdf",
        size_bytes=len(data),
        path=f"source/{pl.source_pdf_path.name}",
    )


@router.get("/{part_id}/text", response_model=PartTextResponse)
def get_part_text(
    project_id: str,
    part_id: str,
    services: ApplicationServices = Depends(get_services),
) -> PartTextResponse:
    pl = services.storage.ensure_part_tree(project_id, part_id)
    if pl.edited_txt_path.is_file():
        text = pl.edited_txt_path.read_text(encoding="utf-8")
        return PartTextResponse(text=text, source=EDITED_TEXT_NAME)
    if pl.extracted_txt_path.is_file():
        text = pl.extracted_txt_path.read_text(encoding="utf-8")
        return PartTextResponse(text=text, source=EXTRACTED_TEXT_NAME)
    return PartTextResponse(text="", source="")


@router.put("/{part_id}/text", response_model=PartTextResponse)
def save_part_text(
    project_id: str,
    part_id: str,
    body: SavePartTextRequest,
    services: ApplicationServices = Depends(get_services),
) -> PartTextResponse:
    pl = services.storage.ensure_part_tree(project_id, part_id)
    pl.text_dir.mkdir(parents=True, exist_ok=True)
    pl.edited_txt_path.write_text(body.text, encoding="utf-8")
    for chunk in services.project_store.list_chunks(project_id, part_id):
        services.rebuild.update_chunk_text(
            project_id,
            part_id,
            chunk.chunk_id,
            body.text,
        )
    return PartTextResponse(text=body.text, source=EDITED_TEXT_NAME)


@router.post("/{part_id}/extract-text", response_model=ExtractTextResponse)
def extract_part_text(
    project_id: str,
    part_id: str,
    services: ApplicationServices = Depends(get_services),
) -> ExtractTextResponse:
    text = services.part_text.extract_text_from_source_pdf(project_id, part_id)
    return ExtractTextResponse(text=text)


@router.post("/{part_id}/chunking", response_model=ChunkingResponse, status_code=201)
def create_part_chunks(
    project_id: str,
    part_id: str,
    body: ChunkingRequest,
    services: ApplicationServices = Depends(get_services),
) -> ChunkingResponse:
    count = services.part_text.save_text_and_create_chunks(
        project_id,
        part_id,
        body.text,
        body.chunk_size,
    )
    return ChunkingResponse(chunks_created=count)


@router.get("/{part_id}/summary", response_model=PartSummaryResponse)
def part_summary(
    project_id: str,
    part_id: str,
    services: ApplicationServices = Depends(get_services),
) -> PartSummaryResponse:
    summary = services.part_summary.summarize(project_id, part_id)
    return PartSummaryResponse(
        total_chunks=summary.total_chunks,
        narration_ready=summary.narration_ready,
        narration_approved=summary.narration_approved,
        vc_ready=summary.vc_ready,
        vc_approved=summary.vc_approved,
        vc_queued=summary.vc_queued,
        vc_processing=summary.vc_processing,
        failed=summary.failed,
        interrupted=summary.interrupted,
    )

"""Part, source, and part-level text routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.dependencies import get_services
from app.api.mappers import part_response
from app.api.schemas.common import (
    CreatePartRequest,
    PartResponse,
    PartTextResponse,
    SavePartTextRequest,
    SourceUploadResponse,
)
from app.api.services import ApplicationServices
from app.storage.layout import EDITED_TEXT_NAME, EXTRACTED_TEXT_NAME

router = APIRouter(prefix="/projects/{project_id}/parts", tags=["parts"])


@router.get("", response_model=list[PartResponse])
def list_parts(
    project_id: str,
    services: ApplicationServices = Depends(get_services),
) -> list[PartResponse]:
    return [part_response(p) for p in services.project_store.list_parts(project_id)]


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
    return part_response(manifest)


@router.get("/{part_id}", response_model=PartResponse)
def get_part(
    project_id: str,
    part_id: str,
    services: ApplicationServices = Depends(get_services),
) -> PartResponse:
    return part_response(services.project_store.load_part(project_id, part_id))


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

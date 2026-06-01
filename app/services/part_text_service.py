"""E7.1 — PDF extraction and part chunking via narration-engine."""

from __future__ import annotations

from pathlib import Path

from app.contracts.states import STATE_TEXT_SAVED
from app.narration.bridge import ensure_narration_engine_path
from app.storage.project_store import ProjectStore


class PdfTextExtractionError(ValueError):
    """Raised when PDF text extraction fails."""


class PartChunkingError(ValueError):
    """Raised when part chunking cannot proceed."""


_VALID_CHUNK_SIZES = frozenset({600, 700, 800, 900, 1000})


class PartTextService:
    def __init__(self, store: ProjectStore) -> None:
        self._store = store

    def extract_text_from_source_pdf(self, project_id: str, part_id: str) -> str:
        pl = self._store.part_layout(project_id, part_id)
        self._store.load_part(project_id, part_id)
        pdf_path = pl.source_pdf_path
        if not pdf_path.is_file():
            raise FileNotFoundError(f"Source PDF not found: {pdf_path}")

        pdf_bytes = pdf_path.read_bytes()
        try:
            full_text = _extract_pdf_bytes(pdf_bytes, filename=pdf_path.name)
        except Exception as exc:
            raise PdfTextExtractionError(str(exc)) from exc

        pl.text_dir.mkdir(parents=True, exist_ok=True)
        pl.extracted_txt_path.write_text(full_text, encoding="utf-8")
        return full_text

    def save_text_and_create_chunks(
        self,
        project_id: str,
        part_id: str,
        text: str,
        chunk_size: int,
    ) -> int:
        if chunk_size not in _VALID_CHUNK_SIZES:
            raise PartChunkingError(
                f"chunk_size must be one of {sorted(_VALID_CHUNK_SIZES)}"
            )

        self._store.load_part(project_id, part_id)
        existing = self._store.list_chunks(project_id, part_id)
        if existing:
            raise PartChunkingError(
                "Part already has chunks; remove them before re-chunking"
            )

        body = (text or "").strip()
        if not body:
            raise PartChunkingError("text must not be empty")

        pl = self._store.part_layout(project_id, part_id)
        pl.text_dir.mkdir(parents=True, exist_ok=True)
        pl.edited_txt_path.write_text(body, encoding="utf-8")
        if not pl.extracted_txt_path.is_file():
            pl.extracted_txt_path.write_text(body, encoding="utf-8")

        pieces = _split_text(body, validation_max_chars=chunk_size)
        if not pieces:
            raise PartChunkingError("No chunks produced from text")

        for index, chunk_text in enumerate(pieces, start=1):
            chunk = self._store.create_chunk(
                project_id,
                part_id,
                index,
                text=chunk_text,
            )
            chunk.state = STATE_TEXT_SAVED
            self._store.save_chunk(project_id, part_id, chunk)

        part = self._store.load_part(project_id, part_id)
        part.chunks_total = len(pieces)
        self._store.save_part(part)
        return len(pieces)


def _extract_pdf_bytes(pdf_bytes: bytes, *, filename: str) -> str:
    ensure_narration_engine_path()
    from backend.services.pdf_extractor import PageText, PdfExtractor, PdfExtractionError
    from backend.services.persian_text_repair import PersianTextRepairService
    from backend.services.text_cleaner import TextCleaner

    extractor = PdfExtractor()
    cleaner = TextCleaner()
    repair = PersianTextRepairService(debug_dir=None)

    try:
        raw = extractor.extract(pdf_bytes, filename=filename)
        cleaned = cleaner.clean_result(raw)
    except PdfExtractionError:
        raise
    except Exception as exc:
        raise PdfTextExtractionError(str(exc)) from exc

    if not any(p.text.strip() for p in cleaned.pages):
        raise PdfTextExtractionError("No text could be extracted from this PDF.")

    repaired_pages: list[PageText] = []
    for page in cleaned.pages:
        result = repair.repair(page.text)
        repaired_pages.append(PageText(page_number=page.page_number, text=result.text))

    parts: list[str] = []
    for page in repaired_pages:
        body = page.text.strip()
        if body:
            parts.append(f"--- Page {page.page_number} ---\n{body}")
    return "\n\n".join(parts)


def _split_text(text: str, *, validation_max_chars: int) -> list[str]:
    ensure_narration_engine_path()
    from backend.services.text_splitter import split_text

    return split_text(text, validation_max_chars=validation_max_chars)

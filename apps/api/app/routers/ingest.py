from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, UploadFile, status
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.config import get_settings
from app.services.orchestrator import queue_ingest_job
from app.utils.logger import logger
from app.utils.slugify import slugify

router = APIRouter(prefix="/ingest", tags=["ingest"])


def _ensure_project_dir(base_dir: Path, project_label: str | None) -> tuple[str, Path]:
    root = base_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    slug = slugify(project_label) if project_label else f"project-{datetime.utcnow():%Y%m%d-%H%M%S}"
    candidate = root / slug
    counter = 1
    while candidate.exists():
        counter += 1
        candidate = root / f"{slug}-{counter:02d}"
    candidate.mkdir(parents=True, exist_ok=True)
    return slug, candidate


async def _persist_upload(file: UploadFile, destination: Path) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        content = await file.read()
        destination.write_bytes(content)
    finally:
        await file.close()

    return {
        "name": file.filename,
        "path": str(destination),
        "size": destination.stat().st_size,
        "content_type": file.content_type,
    }


def _parse_urls(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.replace("\r", "\n").split("\n") if item.strip()]


def _write_references(destination: Path, references: Iterable[dict[str, Any]]) -> None:
    references = list(references)
    if not references:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "references": references,
        "generated_at": datetime.utcnow().isoformat(),
    }
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")


@router.post("/submit", status_code=status.HTTP_201_CREATED)
async def submit_ingest(background_tasks: BackgroundTasks, request: Request) -> dict[str, Any]:
    form = await request.form()

    uploads: list[UploadFile] = []
    for item in form.getlist("files"):
        if isinstance(item, (UploadFile, StarletteUploadFile)):
            uploads.append(item)

    reference_urls = form.get("reference_urls")
    tag_category = form.get("tag_category")
    note_detail = form.get("note_detail") or "standard"
    project_label = form.get("project_label")

    urls = _parse_urls(reference_urls)

    if not uploads and not urls:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide at least one file or URL")

    settings = get_settings()
    base_dir = settings.project_root / settings.data_root
    project_slug, project_dir = _ensure_project_dir(base_dir, project_label)

    source_dir = project_dir / "source"
    artifacts_dir = project_dir / "artifacts"
    source_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    saved_files: list[dict[str, Any]] = []
    for upload in uploads:
        safe_name = Path(upload.filename or "unnamed").name
        destination = source_dir / safe_name
        try:
            saved = await _persist_upload(upload, destination)
            saved_files.append(saved)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.bind(project_dir=str(project_dir), filename=safe_name).exception("failed to persist upload")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    reference_payloads: list[dict[str, Any]] = []
    for url in urls:
        reference_payloads.append(
            {
                "url": url,
                "captured_at": datetime.utcnow().isoformat(),
                "tag_category": tag_category,
                "note_detail": note_detail,
            }
        )
    _write_references(source_dir / "references.json", reference_payloads)

    project_id = str(uuid.uuid4())

    metadata = {
        "tag_category": tag_category,
        "note_detail": note_detail,
        "project_label": project_label,
        "project_slug": project_slug,
        "project_dir": str(project_dir),
        "saved_files": saved_files,
        "references": reference_payloads,
        "submitted_at": datetime.utcnow().isoformat(),
    }

    job_id = queue_ingest_job(
        background_tasks=background_tasks,
        project_id=project_id,
        metadata=metadata,
        payload={"files": saved_files, "references": reference_payloads},
    )

    logger.bind(project_id=project_id, slug=project_slug, job_id=job_id).info(
        "ingest submitted", files=len(saved_files), references=len(reference_payloads)
    )

    return {
        "status": "queued",
        "job_id": job_id,
        "project_id": project_id,
        "project_slug": project_slug,
        "project_dir": str(project_dir),
        "files": saved_files,
        "references": reference_payloads,
    }
"""Orchestrator stubs for Celery-driven ingestion.

These helpers centralise queue naming and troubleshooting hooks so we can
provide consistent logging across API and worker processes.
"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import BackgroundTasks

from app.config import get_settings
from app.domain.pipeline import PipelineStage
from app.services.pipeline_runner import PipelineJob, run_pipeline
from app.state.job_store import JobRecord, job_store
from app.utils.logger import logger


def queue_ingest_job(
    *,
    background_tasks: BackgroundTasks,
    project_id: str,
    metadata: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> str:
    """Queue an ingestion job and kick off the synchronous pipeline runner."""

    job = PipelineJob(job_id=str(uuid.uuid4()), stage=PipelineStage.INGEST, payload=payload or {})
    settings = get_settings()

    logger.bind(stage=job.stage, job_id=job.job_id, project_id=project_id).info(
        "queueing job", payload_keys=list(job.payload.keys())
    )

    job_store.add_job(
        JobRecord(
            job_id=job.job_id,
            project_id=project_id,
            metadata=metadata or {},
        )
    )

    background_tasks.add_task(_run_pipeline, job, metadata or {})
    return job.job_id


def _run_pipeline(job: PipelineJob, metadata: dict[str, Any]) -> None:
    try:
        run_pipeline(job, metadata)
    except Exception as exc:  # pragma: no cover - defensive logging
        job_store.append_error(job.job_id, str(exc))
        logger.bind(job_id=job.job_id).exception("pipeline execution failed")


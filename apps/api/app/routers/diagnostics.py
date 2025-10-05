from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter

from app.state.job_store import JobRecord, StageSnapshot, job_store

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])


def _serialise_stage(stage: StageSnapshot) -> dict[str, object]:
    payload = asdict(stage)
    payload["stage"] = stage.stage.value
    if stage.started_at:
        payload["started_at"] = stage.started_at.isoformat()
    if stage.finished_at:
        payload["finished_at"] = stage.finished_at.isoformat()
    return payload


def _serialise_job(job: JobRecord) -> dict[str, object]:
    payload = asdict(job)
    payload["created_at"] = job.created_at.isoformat()
    payload["stages"] = [_serialise_stage(stage) for stage in job.stages]
    return payload


@router.get("/jobs")
def list_jobs() -> dict[str, object]:
    jobs = job_store.list_jobs()
    return {"jobs": [_serialise_job(job) for job in jobs]}

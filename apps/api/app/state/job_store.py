from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Callable, Dict, List, Literal

from app.domain.pipeline import PIPELINE_ORDER, PipelineStage

StageStatus = Literal["queued", "running", "succeeded", "failed"]
JobStatus = Literal["queued", "processing", "completed", "failed"]


class JobNotFoundError(Exception):
    """Raised when an operation references a job that is not registered."""


@dataclass(slots=True)
class StageSnapshot:
    stage: PipelineStage
    status: StageStatus = "queued"
    detail: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


@dataclass(slots=True)
class JobRecord:
    job_id: str
    project_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: JobStatus = "queued"
    metadata: Dict[str, Any] = field(default_factory=dict)
    stages: List[StageSnapshot] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class JobStore:
    def __init__(self) -> None:
        self._jobs: Dict[str, JobRecord] = {}
        self._lock = Lock()

    def add_job(self, job: JobRecord) -> None:
        with self._lock:
            if not job.stages:
                job.stages = [StageSnapshot(stage=stage) for stage in PIPELINE_ORDER]
            self._jobs[job.job_id] = job

    def list_jobs(self) -> List[JobRecord]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda job: job.created_at, reverse=True)

    def get_job(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def require_job(self, job_id: str) -> JobRecord:
        record = self.get_job(job_id)
        if record is None:
            raise JobNotFoundError(job_id)
        return record

    def set_job_status(self, job_id: str, status: JobStatus) -> None:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise JobNotFoundError(job_id)
            record.status = status

    def update_stage(self, job_id: str, stage: PipelineStage, **updates: Any) -> None:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise JobNotFoundError(job_id)
            snapshot = next((s for s in record.stages if s.stage == stage), None)
            if snapshot is None:
                raise ValueError(f"Stage {stage} not registered for job {job_id}")
            for key, value in updates.items():
                setattr(snapshot, key, value)

    def start_stage(self, job_id: str, stage: PipelineStage, detail: str | None = None) -> None:
        now = datetime.utcnow()
        self.update_stage(job_id, stage, status="running", detail=detail, started_at=now, finished_at=None)
        self.set_job_status(job_id, "processing")

    def complete_stage(self, job_id: str, stage: PipelineStage, detail: str | None = None) -> None:
        now = datetime.utcnow()
        self.update_stage(job_id, stage, status="succeeded", detail=detail, finished_at=now)

    def fail_stage(self, job_id: str, stage: PipelineStage, message: str) -> None:
        now = datetime.utcnow()
        self.update_stage(job_id, stage, status="failed", detail=message, finished_at=now)
        self.append_error(job_id, message)

    def append_error(self, job_id: str, message: str) -> None:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise JobNotFoundError(job_id)
            record.errors.append(message)
            record.status = "failed"

    def run_stage(self, job_id: str, stage: PipelineStage, detail: str, func: Callable[[], Any]) -> Any:
        self.start_stage(job_id, stage, detail)
        try:
            result = func()
        except Exception as exc:  # pragma: no cover - defensive logging
            self.fail_stage(job_id, stage, str(exc))
            raise
        else:
            self.complete_stage(job_id, stage, detail)
            return result


job_store = JobStore()

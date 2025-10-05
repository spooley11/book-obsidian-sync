from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "apps" / "api"))

from celery import Celery  # noqa: E402

from app.config import get_settings  # noqa: E402

settings = get_settings()
app = Celery(
    "converter",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

app.autodiscover_tasks(["workers.tasks"])


@app.task
def ping() -> str:
    return "pong"

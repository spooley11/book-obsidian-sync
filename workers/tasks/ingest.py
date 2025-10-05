from pathlib import Path

from workers.worker import app


@app.task(bind=True)
def ingest(self, file_path: str) -> dict[str, str]:
    path = Path(file_path)
    if not path.exists():
        self.retry(countdown=5, max_retries=3)
    return {"status": "stub", "file": path.name}

from fastapi import FastAPI

from app.config import get_settings
from app.routers import diagnostics, ingest

app = FastAPI(title="Converter Pipeline", version="0.1.0")
app.include_router(ingest.router)
app.include_router(diagnostics.router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "env": settings.app_env}

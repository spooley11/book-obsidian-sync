Wanted to start some coding projects that allows me to test out different code systems and various AI integreations to see where i can take it.
This one in particular came about since i have a large library of religous books or audio files i wanted a way to compress the data easily and find the various connections. also make it more fun to upload places like notebooklm

biggest issues to overcome
- getting ollama to conversationally provide notes and add tags, had to break it up into chunks and then revisit the chunks for consistency because of the difficulty i had with the automation
- reading the data accurately, i have a number of low quality images of texts that ocr can struggle with






# Converter AI Pipeline
Modular workspace for the religious studies ingestion, transcription, and summarisation toolchain.

## Quickstart

```powershell
# from repo root
./scripts/bootstrap.ps1
```

- Installs Python/Poetry deps for API and workers inside `.venv`
- Enables `pnpm` via Corepack and installs the web app packages
- Starts Postgres, Redis, Ollama containers (unless `-SkipDocker` is provided)
- Launches FastAPI, Celery, and Vite dev servers in background jobs

Use `Get-Job` / `Receive-Job` / `Stop-Job` in PowerShell to inspect or stop services.

## Layout Highlights

- `apps/api` – FastAPI service, settings, routers, orchestration hooks
- `workers/` – Celery workers plus stub pipelines
- `apps/web` – React/Vite dashboard with drag-and-drop ingest and status widgets
- `services/` – Shared Python utilities (DB session mgmt, LLM prompt loader, transcription stubs)
- `shared/config/prompts.yaml` – Source-of-truth YAML for Ollama prompt personas
- `docker/` – Dockerfiles for api/worker/web containers
- `docker-compose.yml` – Local orchestration for Postgres, Redis, Ollama, API, workers, and web UI

## Troubleshooting Checklist

1. **Docker health** – `docker compose ps` should list postgres/redis/ollama as `healthy`. Restart with `docker compose restart <svc>`.
2. **Python path issues** – Ensure `.\.venv\Scripts\activate` before running CLI tasks so workers resolve `app.*` imports.
3. **Celery queue stalls** – Inspect redis queue lengths: `docker exec -it converter-redis-1 redis-cli llen celery`.
4. **Frontend proxy errors** – Vite proxies `/api` and `/ws` to port 8000; confirm FastAPI is live via `Invoke-WebRequest http://localhost:8000/health`.
5. **Prompt updates** – Edit `shared/config/prompts.yaml`; both API and workers read it on each task so restarts not required during dev.

## Next Steps

- Flesh out database models under `services/db` and migrate via Alembic
- Replace transcription stub with faster-whisper integration
- Implement actual WebSocket progress streaming and analytics aggregation
- Wire YouTube/URL ingestion once storage layer is ready
## Diagnostics & Metadata\n\n- Submitting files or URLs now queues the pipeline immediately and stores artefacts under `vault/<project-slug>/` using your Project Label when provided.\n- URL references persist in `references.json` inside the project `source/` directory so you can review or tweak later.\n- Visit `/diagnostics` in the web UI to inspect raw job payloads, stage status, and metadata when debugging failures.\n- Tag category and note detail selections travel with each submission for downstream processing and folder naming.\n

## Pipeline Outputs

- Uploaded projects now land under `vault/<project-slug>/` with `source/` for originals and `artifacts/` for generated assets (extracted text, chunk metadata, summaries, quotes, metadata JSON).
- The dashboard immediately queues processing and progresses through Ingest → Transcribe → Chunk → Summarise → Export; each stage updates in the UI.\n- `summary.md` now includes YAML front matter with placeholders for `cover_image`, `author_image`, publication details, and a `source_files` list so you can fill in cover/author art later.
- PDF support relies on `pdfminer.six`; rerun `./scripts/bootstrap.ps1` (or `poetry install` inside `apps/api`) after pulling to ensure dependencies are installed.


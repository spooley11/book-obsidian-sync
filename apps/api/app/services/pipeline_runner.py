from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

try:
    from pdfminer.high_level import extract_text as pdf_extract_text
except ModuleNotFoundError as exc:
    raise RuntimeError("pdfminer.six is required for PDF ingestion; run poetry install") from exc

from app.domain.pipeline import PIPELINE_ORDER, PipelineStage
from app.state.job_store import job_store
from app.utils.logger import logger


@dataclass(slots=True)
class PipelineJob:
    job_id: str
    stage: PipelineStage
    payload: dict[str, Any]


class PipelineContext:
    def __init__(self, job: PipelineJob, metadata: dict[str, Any]) -> None:
        self.job = job
        self.metadata = metadata
        self.project_dir = Path(metadata["project_dir"]).resolve()
        self.source_dir = self.project_dir / "source"
        self.artifacts_dir = self.project_dir / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.documents: list[dict[str, Any]] = []
        self.chunks: list[dict[str, Any]] = []

    def log(self, message: str, **extra: Any) -> None:
        logger.bind(job_id=self.job.job_id, project_dir=str(self.project_dir), **extra).info(message)


def run_pipeline(job: PipelineJob, metadata: dict[str, Any]) -> None:
    ctx = PipelineContext(job, metadata)
    job_store.set_job_status(job.job_id, "processing")

    for stage in PIPELINE_ORDER:
        handler = _STAGE_HANDLERS.get(stage)
        if handler is None:
            continue
        detail = handler.__doc__ or stage.value
        job_store.start_stage(job.job_id, stage, detail=detail)
        try:
            handler(ctx)
        except Exception as exc:  # pragma: no cover
            job_store.fail_stage(job.job_id, stage, str(exc))
            ctx.log("stage failed", stage=stage.value, error=str(exc))
            return
        else:
            job_store.complete_stage(job.job_id, stage)
            ctx.log("stage complete", stage=stage.value)

    job_store.set_job_status(job.job_id, "completed")


def stage_ingest(ctx: PipelineContext) -> None:
    """Ingest source files and normalise text."""
    extracted_dir = ctx.artifacts_dir / "extracted"
    extracted_dir.mkdir(parents=True, exist_ok=True)

    for file_info in ctx.metadata.get("saved_files", []):
        path = Path(file_info["path"]).resolve()
        suffix = path.suffix.lower()
        text = ""

        if suffix == ".pdf":
            text = pdf_extract_text(path)
        elif suffix in {".txt", ".md", ".markdown"}:
            text = path.read_text(encoding="utf-8")
        else:
            ctx.log("unsupported media type for ingest", file=str(path), suffix=suffix)
            continue

        extracted_path = extracted_dir / f"{path.stem}.txt"
        extracted_path.write_text(text, encoding="utf-8")
        ctx.documents.append({
            "name": path.name,
            "text": text,
            "extracted_path": str(extracted_path),
        })

    if not ctx.documents:
        raise RuntimeError("No textual documents available after ingest stage")

    combined = "

".join(doc["text"] for doc in ctx.documents)

    combined = "

".join(doc["text"] for doc in ctx.documents)
\n\n".join(doc["text"] for doc in ctx.documents)
    (extracted_dir / "combined.txt").write_text(combined, encoding="utf-8")
def stage_transcribe(ctx: PipelineContext) -> None:
    """Transcription stage (currently a passthrough for text sources)."""
    return None


def stage_chunk(ctx: PipelineContext) -> None:
    """Split documents into manageable analysis chunks."""
    max_words = 400
    chunks: list[dict[str, Any]] = []
    chunk_dir = ctx.artifacts_dir / "chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)

    for doc in ctx.documents:
        paragraphs = [p.strip() for p in doc["text"].split("

") if p.strip()]
        buffer: list[str] = []
        word_count = 0
        chunk_index = 0

        def flush_buffer() -> None:
            nonlocal buffer, word_count, chunk_index
            if not buffer:
                return
            chunk_text = "

".join(buffer).strip()
            chunk_filename = f"{Path(doc['name']).stem}-chunk-{chunk_index:03d}.txt"
            (chunk_dir / chunk_filename).write_text(chunk_text, encoding="utf-8")
            chunks.append({
                "document": doc["name"],
                "index": chunk_index,
                "text": chunk_text,
                "word_count": word_count,
                "chunk_file": str(chunk_dir / chunk_filename),
            })
            buffer = []
            word_count = 0
            chunk_index += 1

        for paragraph in paragraphs:
            words = paragraph.split()
            paragraph_word_count = len(words)
            if word_count + paragraph_word_count > max_words and buffer:
                flush_buffer()
            buffer.append(paragraph)
            word_count += paragraph_word_count
        flush_buffer()

    ctx.chunks = chunks
    (ctx.artifacts_dir / "chunks.json").write_text(json.dumps(chunks, indent=2), encoding="utf-8")


def stage_summarise(ctx: PipelineContext) -> None:
    """Generate lightweight chapter summaries and quote suggestions."""
    from app.services.llm.ollama_client import OllamaError, summarise_chunk, synthesise_overview

    project_label = ctx.metadata.get("project_label") or ctx.metadata.get("project_slug") or ctx.project_dir.name
    created_at = datetime.utcnow().isoformat()

    chunk_notes: List[Dict[str, Any]] = []
    aggregated_quotes: List[Dict[str, Any]] = []

    for chunk in ctx.chunks:
        try:
            note = summarise_chunk(chunk["text"], document=chunk["document"], chunk_index=chunk["index"])
        except OllamaError as exc:
            ctx.log("chunk summarisation fallback", chunk_index=chunk["index"], error=str(exc))
            note = _fallback_chunk_summary(chunk["text"])
        chunk_notes.append({**chunk, "note": note})
        for quote in note.get("quotes", []):
            if isinstance(quote, dict):
                text_value = quote.get("text") or quote.get("quote") or ""
                context_value = quote.get("context") or quote.get("explanation") or quote.get("source") or ""
            else:
                text_value = str(quote)
                context_value = ""
            if not text_value.strip():
                continue
            aggregated_quotes.append({
                "document": chunk["document"],
                "index": chunk["index"],
                "text": text_value.strip(),
                "context": context_value.strip(),
            })

    try:
        overview = synthesise_overview([cn["note"] for cn in chunk_notes], project_label=project_label)
    except OllamaError as exc:
        ctx.log("overview synthesis fallback", error=str(exc))
        overview = _fallback_overview([cn["note"] for cn in chunk_notes])

    summary_lines = _build_summary_markdown(project_label, created_at, ctx.metadata.get("saved_files", []), overview, chunk_notes)
    quotes_lines = _build_quotes_markdown(project_label, created_at, aggregated_quotes)

    (ctx.artifacts_dir / "summary.md").write_text("
".join(summary_lines), encoding="utf-8")
    (ctx.artifacts_dir / "quotes.md").write_text("
".join(quotes_lines), encoding="utf-8")

    summaries_json = [{
        "document": chunk["document"],
        "index": chunk["index"],
        "summary": chunk["note"].get("summary", ""),
        "insights": chunk["note"].get("insights", []),
        "questions": chunk["note"].get("questions", []),
        "quotes": chunk["note"].get("quotes", []),
    } for chunk in chunk_notes]
    (ctx.artifacts_dir / "chunk_summaries.json").write_text(json.dumps(summaries_json, indent=2), encoding="utf-8")
    (ctx.artifacts_dir / "overview.json").write_text(json.dumps(overview, indent=2), encoding="utf-8")


def _fallback_chunk_summary(text: str) -> Dict[str, Any]:
    sentence_pattern = re.compile(r"(?<=[.!?]) +")
    sentences = sentence_pattern.split(text)[:3]
    summary = " ".join(s.strip() for s in sentences if s.strip())
    if not summary:
        summary = text.split("
")[0][:280]
    return {
        "summary": summary,
        "insights": [],
        "questions": [],
        "quotes": [],
    }


def _fallback_overview(notes: List[Dict[str, Any]]) -> Dict[str, Any]:
    combined = "

".join(doc["text"] for doc in ctx.documents)
 ".join(note.get("summary", "") for note in notes)
    return {
        "overview": combined[:600],
        "themes": [],
        "action_items": [],
    }


def _build_summary_markdown(project_label: str, created_at: str, saved_files: list[dict[str, Any]], overview: Dict[str, Any], chunk_notes: List[Dict[str, Any]]) -> List[str]:
    frontmatter = [
        "---",
        f'title: "{project_label}"',
        'cover_image: ""',
        'author_image: ""',
        'source_publication: ""',
        'publication_date: ""',
        f'summary_created_at: "{created_at}"',
        'source_files:',
    ]
    if saved_files:
        for file_info in saved_files:
            filename = Path(file_info.get("path", "unknown")).name
            frontmatter.append(f'  - "{filename}"')
    else:
        frontmatter.append('  - "unknown"')
    frontmatter.extend(["---", ""])

    lines = frontmatter
    lines.extend(["# Overview", overview.get("overview", ""), ""])

    themes = overview.get("themes") or []
    if themes:
        lines.append("## Key Themes")
        lines.extend([f"- {theme}" for theme in themes])
        lines.append("")

    actions = overview.get("action_items") or []
    if actions:
        lines.append("## Recommended Study Actions")
        lines.extend([f"- {action}" for action in actions])
        lines.append("")

    lines.append("## Chunk Summaries")
    for chunk in chunk_notes:
        note = chunk["note"]
        lines.append(f"### {chunk['document']} - Chunk {chunk['index'] + 1}")
        summary = note.get("summary") or "Summary unavailable."
        lines.append(summary)
        insights = note.get("insights") or []
        if insights:
            lines.append("#### Key Insights")
            lines.extend([f"- {ins}" for ins in insights])
        questions = note.get("questions") or []
        if questions:
            lines.append("#### Follow-up Questions")
            lines.extend([f"- {q}" for q in questions])
        lines.append("")

    return lines


def _build_quotes_markdown(project_label: str, created_at: str, quotes: List[Dict[str, Any]]) -> List[str]:
    frontmatter = [
        "---",
        f'title: "{project_label} Quotes"',
        'cover_image: ""',
        'author_image: ""',
        f'quotes_generated_at: "{created_at}"',
        '---',
        "",
    ]

    lines = frontmatter
    lines.append("# Suggested Quotes")
    lines.append("")

    if not quotes:
        lines.append("- No notable quotes found.")
        return lines

    for quote in quotes:
        text = quote.get("text", "").strip()
        context = quote.get("context", "").strip()
        document = quote.get("document")
        index = quote.get("index")
        header = f"- **{document} - Chunk {index + 1}**: {text}"
        lines.append(header)
        if context:
            lines.append(f"  - _Context_: {context}")
    return lines


def stage_export(ctx: PipelineContext) -> None:
    """Persist pipeline metadata."""
    metadata = {
        "job_id": ctx.job.job_id,
        "project_dir": str(ctx.project_dir),
        "created_at": datetime.utcnow().isoformat(),
        "documents": [
            {
                "name": doc["name"],
                "extracted_path": doc["extracted_path"],
            }
            for doc in ctx.documents
        ],
        "chunks": len(ctx.chunks),
    }
    (ctx.artifacts_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


_STAGE_HANDLERS = {
    PipelineStage.INGEST: stage_ingest,
    PipelineStage.TRANSCRIBE: stage_transcribe,
    PipelineStage.CHUNK: stage_chunk,
    PipelineStage.SUMMARISE: stage_summarise,
    PipelineStage.EXPORT: stage_export,
}
from __future__ import annotations

import json
from typing import Any, Dict

import httpx

from app.config import get_settings

DEFAULT_TIMEOUT = 120.0


class OllamaError(RuntimeError):
    pass


def _post_generate(payload: Dict[str, Any]) -> str:
    settings = get_settings()
    url = f"{settings.ollama_endpoint.rstrip('/')}/api/generate"
    data = {"model": settings.ollama_model, "stream": False, **payload}

    with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
        response = client.post(url, json=data)
    try:
        response.raise_for_status()
    except httpx.HTTPError as exc:  # pragma: no cover - network failure
        raise OllamaError(f"Ollama request failed: {exc}") from exc

    body = response.json()
    text = body.get("response")
    if not text:
        # Some versions nest the message inside `message`/`content`
        message = body.get("message") or {}
        text = message.get("content")
    if not text:
        raise OllamaError("No response content from Ollama")
    return text.strip()


def summarise_chunk(chunk_text: str, *, document: str, chunk_index: int) -> Dict[str, Any]:
    """Return structured notes for a single chunk."""
    prompt = f"""
You are an expert Latter-day Saint scholar creating study notes. Analyse the following excerpt.
Return JSON with keys:
- summary: concise paragraph (<=120 words).
- insights: list of 3 key takeaways (phrases or short sentences).
- questions: list of 2 thoughtful follow-up questions.
- quotes: list of objects with fields text and context (context explains significance).
Reference the document "{document}" and chunk #{chunk_index} when useful. Keep quotes <=200 characters.

TEXT:
"""
{chunk_text}
"""
JSON OUTPUT:
"""
    """
    raw = _post_generate({"prompt": prompt})
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise OllamaError("Chunk summary response was not valid JSON")

    return {
        "summary": data.get("summary", ""),
        "insights": data.get("insights") or [],
        "questions": data.get("questions") or [],
        "quotes": data.get("quotes") or [],
    }


def synthesise_overview(chunk_summaries: list[Dict[str, Any]], *, project_label: str) -> Dict[str, Any]:
    """Produce a higher-level overview from chunk notes."""
    summaries_text = "
".join(cs.get("summary", "") for cs in chunk_summaries if cs.get("summary"))
    prompt = f"""
You are preparing a study overview for the project "{project_label}".
Using the following notes, craft JSON with:
- overview: one paragraph synopsis (<=150 words).
- themes: list of 3-5 overarching themes or doctrines.
- action_items: list of 2-3 recommended follow-up study actions.

NOTES:
{summaries_text}

JSON OUTPUT:
"""
    """
    raw = _post_generate({"prompt": prompt})
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise OllamaError("Overview response was not valid JSON")

    return {
        "overview": data.get("overview", ""),
        "themes": data.get("themes") or [],
        "action_items": data.get("action_items") or [],
    }

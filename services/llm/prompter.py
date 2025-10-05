"""Prompt loading utilities shared across API and workers."""

from pathlib import Path
from typing import Any

import yaml

PROMPT_PATH = Path(__file__).resolve().parents[2] / "shared" / "config" / "prompts.yaml"


def load_prompts() -> dict[str, Any]:
    with PROMPT_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def get_prompt(role: str) -> dict[str, Any]:
    prompts = load_prompts()
    return prompts["roles"].get(role, {})

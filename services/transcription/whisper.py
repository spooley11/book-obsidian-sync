from pathlib import Path
from typing import Literal

from app.utils.logger import logger

MediaType = Literal["audio", "video"]


def transcribe(media_path: Path, media_type: MediaType) -> Path:
    """Placeholder transcription hook.

    Later this will call faster-whisper / whisper.cpp. For now we drop a stub
    markdown file to keep downstream pipeline tests happy.
    """

    transcript_path = media_path.with_suffix(".transcript.md")

    transcript_path.write_text(
      f"# Transcript placeholder\n\nOriginal file: {media_path.name}\n\nStatus: pending integration with whisper.cpp\n",
      encoding="utf-8"
    )

    logger.bind(media=media_path.name, output=str(transcript_path)).info("transcription stub executed")
    return transcript_path

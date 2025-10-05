from enum import Enum


class PipelineStage(str, Enum):
    INGEST = "ingest"
    TRANSCRIBE = "transcribe"
    CHUNK = "chunk"
    SUMMARISE = "summarise"
    EXPORT = "export"


PIPELINE_ORDER = [
    PipelineStage.INGEST,
    PipelineStage.TRANSCRIBE,
    PipelineStage.CHUNK,
    PipelineStage.SUMMARISE,
    PipelineStage.EXPORT,
]

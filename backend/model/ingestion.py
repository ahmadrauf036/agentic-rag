from pydantic import BaseModel, Field


class IngestionRequest(BaseModel):
    file_path: list[str] = Field(..., min_length=1, description="Paths to files on disk to ingest")


class IngestionResponse(BaseModel):
    success: bool
    detail: str
    num_chunks: int | None = None
    files: list["IngestedFileInfo"] | None = None
    unpaused_sessions: int | None = None  # NEW


class IngestedFileInfo(BaseModel):
    source: str
    file_hash: str
    num_chunks: int
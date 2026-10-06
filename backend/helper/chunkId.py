from langchain_core.documents import Document

def generate_chunk_id(chunk: Document, index: int) -> str:
    """Deterministic ID: same file content + same chunk position = same ID,
    so re-ingesting an unchanged file overwrites rather than duplicates."""
    file_hash = chunk.metadata.get("file_hash", "unknown")
    return f"{file_hash}-{index}"
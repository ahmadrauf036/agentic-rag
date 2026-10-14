import logging
from collections import defaultdict

from db.documents import upsert_document
from db.sessions import unpause_sessions_referencing_file
from ingestion.chunking import chunking
from ingestion.loader import load_fastapi_uploads, load_files
from model.ingestion import IngestedFileInfo, IngestionResponse
from retrieval.tenant_stores import get_docs_store

logger = logging.getLogger(__name__)


def generate_chunk_id(chunk, index: int) -> str:
    return f"{chunk.metadata.get('file_hash', 'unknown')}-{index}"


def _ingest_documents(docs, org_id: str, uploaded_by: str) -> IngestionResponse:
    chunks = chunking(docs)

    per_file = defaultdict(lambda: {"source": None, "num_chunks": 0})
    ids = []
    for chunk in chunks:
        h = chunk.metadata["file_hash"]
        chunk.metadata["org_id"] = org_id
        chunk.metadata["uploaded_by"] = uploaded_by
        ids.append(generate_chunk_id(chunk, per_file[h]["num_chunks"]))  # per-file index
        per_file[h]["source"] = chunk.metadata["source"]
        per_file[h]["num_chunks"] += 1

    get_docs_store(org_id).add_documents(documents=chunks, ids=ids)

    files_info, unpaused = [], 0
    for h, info in per_file.items():
        upsert_document(org_id, h, info["source"], info["num_chunks"], uploaded_by)
        unpaused += unpause_sessions_referencing_file(org_id=org_id, file_hash=h)
        files_info.append(IngestedFileInfo(source=info["source"], file_hash=h, num_chunks=info["num_chunks"]))

    return IngestionResponse(success=True, detail="Files ingested successfully.",
                             num_chunks=len(chunks), files=files_info, unpaused_sessions=unpaused)


async def ingest_uploaded_files(files: list, org_id: str, uploaded_by: str) -> IngestionResponse:
    try:
        return _ingest_documents(await load_fastapi_uploads(files), org_id, uploaded_by)
    except Exception as error:
        logger.exception("Upload ingestion failed")
        return IngestionResponse(success=False, detail=str(error))


def ingestion(file_paths: list[str], org_id: str, uploaded_by: str) -> IngestionResponse:
    """Disk-path variant, for tests and scripts."""
    try:
        return _ingest_documents(load_files(file_paths), org_id, uploaded_by)
    except Exception as error:
        logger.exception("Ingestion failed")
        return IngestionResponse(success=False, detail=str(error))
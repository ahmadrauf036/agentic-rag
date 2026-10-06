import logging

from ingestion.chunking import chunking
from ingestion.loader import load_files, load_fastapi_uploads
from model.ingestion import IngestionResponse, IngestedFileInfo
from retrieval.vectorstore import get_vector_store
from helper.chunkId import generate_chunk_id
from collections import defaultdict
from db.sessions import unpause_sessions_referencing_file
logger = logging.getLogger(__name__)

def ingestion(file_paths: list[str]) -> IngestionResponse:
    try:
        docs = load_files(file_paths)
        chunks = chunking(docs)

        vector_store = get_vector_store()
        ids = [generate_chunk_id(chunk, i) for i, chunk in enumerate(chunks)]
        vector_store.add_documents(documents=chunks, ids=ids)

        # Group chunk counts per file_hash for the response
        per_file = defaultdict(lambda: {"source": None, "count": 0})
        for chunk in chunks:
            h = chunk.metadata["file_hash"]
            per_file[h]["source"] = chunk.metadata["source"]
            per_file[h]["count"] += 1

        files_info = [
            IngestedFileInfo(source=info["source"], file_hash=h, num_chunks=info["count"])
            for h, info in per_file.items()
        ]

        return IngestionResponse(
            success=True,
            detail="Files ingested successfully.",
            num_chunks=len(chunks),
            files=files_info,
        )
    except Exception as error:
        logger.exception("Ingestion failed for files: %s", file_paths)
        return IngestionResponse(success=False, detail=str(error))
    
async def ingest_uploaded_files(files: list, owner_id: str) -> IngestionResponse:
    try:
        docs = await load_fastapi_uploads(files)
        chunks = chunking(docs)

        for chunk in chunks:
            chunk.metadata["owner_id"] = owner_id

        vector_store = get_vector_store()
        ids = [generate_chunk_id(chunk, i) for i, chunk in enumerate(chunks)]
        vector_store.add_documents(documents=chunks, ids=ids)

        per_file = defaultdict(lambda: {"source": None, "num_chunks": 0})
        for chunk in chunks:
            h = chunk.metadata["file_hash"]
            per_file[h]["source"] = chunk.metadata["source"]
            per_file[h]["num_chunks"] += 1

        files_info = []
        unpaused_total = 0
        for h, info in per_file.items():
            files_info.append(
                IngestedFileInfo(source=info["source"], file_hash=h, num_chunks=info["num_chunks"])
            )
            unpaused_total += unpause_sessions_referencing_file(file_hash=h)

        return IngestionResponse(
            success=True,
            detail="Files ingested successfully.",
            num_chunks=len(chunks),
            files=files_info,
            unpaused_sessions=unpaused_total,  # new field, see model update below
        )
    except Exception as error:
        logger.exception("Upload ingestion failed")
        return IngestionResponse(success=False, detail=str(error))
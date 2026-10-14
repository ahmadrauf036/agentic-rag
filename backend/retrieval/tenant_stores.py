import logging
import os
import threading
import uuid

from dotenv import load_dotenv
from langchain_chroma import Chroma

from core.embeddings import embedding_model

load_dotenv()
logger = logging.getLogger(__name__)

_cache: dict[str, Chroma] = {}  # one small object per org; fine at this scale
_lock = threading.Lock()


def _collection_name(org_id: str, kind: str) -> str:
    # uuid.UUID() raises ValueError for anything that isn't a UUID, so a
    # collection name can never be built from arbitrary input.
    return f"org_{uuid.UUID(str(org_id))}_{kind}"


def _get_store(org_id: str, kind: str) -> Chroma:
    name = _collection_name(org_id, kind)  # validates first, before any I/O
    with _lock:
        store = _cache.get(name)
        if store is None:
            store = Chroma(
                collection_name=name,
                embedding_function=embedding_model(),
                chroma_cloud_api_key=os.getenv("CHROMA_API_KEY"),
                tenant=os.getenv("CHROMA_TENANT"),
                database=os.getenv("CHROMA_DATABASE"),
            )
            _cache[name] = store
        return store


def get_docs_store(org_id: str) -> Chroma:
    return _get_store(org_id, "docs")


def get_memory_store(org_id: str) -> Chroma:
    return _get_store(org_id, "memory")


def provision_org_collections(org_id: str) -> None:
    get_docs_store(org_id)
    get_memory_store(org_id)


def drop_org_collections(org_id: str) -> None:
    """Offboarding and test cleanup: removes an org's vectors entirely."""
    for kind in ("docs", "memory"):
        name = _collection_name(org_id, kind)
        _get_store(org_id, kind).delete_collection()
        with _lock:
            _cache.pop(name, None)
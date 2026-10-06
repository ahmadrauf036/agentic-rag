import logging
from config import CHUNK_OVERLAP,CHUNK_SIZE
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

def chunking(docs: list[Document]) -> list[Document]:
    """Split loaded documents into retrieval-sized chunks, preserving metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = splitter.split_documents(docs)
    logger.info("Split %d documents into %d chunks", len(docs), len(chunks))
    return chunks
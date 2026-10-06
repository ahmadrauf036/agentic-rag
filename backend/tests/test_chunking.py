from langchain_core.documents import Document
from ingestion.chunking import chunking


def test_chunking_splits_long_text():
    long_text = "word " * 500  # long enough to force multiple chunks
    docs = [Document(page_content=long_text, metadata={"source": "test.txt"})]
    chunks = chunking(docs)
    assert len(chunks) > 1


def test_chunking_preserves_metadata():
    docs = [Document(page_content="short text", metadata={"source": "test.txt", "page": 1})]
    chunks = chunking(docs)
    assert chunks[0].metadata["source"] == "test.txt"
    assert chunks[0].metadata["page"] == 1


def test_chunking_empty_list_returns_empty():
    assert chunking([]) == []

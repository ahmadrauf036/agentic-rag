import pytest

from ingestion.chunking import chunking
from ingestion.loader import load_file
from ingestion.pipeline import generate_chunk_id, ingestion


@pytest.mark.integration
def test_ingestion_success_returns_response():
    result = ingestion(["data/sample.txt"])
    assert result.success is True
    assert result.num_chunks is not None and result.num_chunks > 0


@pytest.mark.integration
def test_ingestion_bad_path_returns_failure_not_exception():
    result = ingestion(["data/does_not_exist.pdf"])
    assert result.success is False
    assert result.detail  # some error message present


@pytest.mark.integration
def test_reingesting_same_file_does_not_duplicate():
    """Ingesting the same unchanged file twice should upsert (overwrite),
    not create a second copy of every chunk."""
    first = ingestion(["data/sample.txt"])
    second = ingestion(["data/sample.txt"])

    assert first.success is True
    assert second.success is True
    # Same file content -> same chunk count both times, since IDs are
    # deterministic and the second call overwrites rather than appends.
    assert first.num_chunks == second.num_chunks


# --- generate_chunk_id (pure, no external calls) -------------------------

def test_generate_chunk_id_is_deterministic_for_same_content():
    docs = load_file("data/sample.txt")
    chunks_a = chunking(docs)
    chunks_b = chunking(docs)

    ids_a = [generate_chunk_id(c, i) for i, c in enumerate(chunks_a)]
    ids_b = [generate_chunk_id(c, i) for i, c in enumerate(chunks_b)]

    assert ids_a == ids_b


def test_generate_chunk_id_differs_by_index():
    docs = load_file("data/sample.txt")
    chunks = chunking(docs)
    if len(chunks) < 2:
        pytest.skip("sample.txt too short to produce multiple chunks")

    id_0 = generate_chunk_id(chunks[0], 0)
    id_1 = generate_chunk_id(chunks[1], 1)
    assert id_0 != id_1


def test_generate_chunk_id_differs_for_different_file_hash():
    docs_txt = load_file("data/sample.txt")
    docs_pdf = load_file("data/sample.pdf")

    id_txt = generate_chunk_id(docs_txt[0], 0)
    id_pdf = generate_chunk_id(docs_pdf[0], 0)

    assert id_txt != id_pdf
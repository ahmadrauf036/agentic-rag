import pytest

from ingestion.loader import (
    UnsupportedFileTypeError,
    compute_file_hash,
    load_file,
    load_files,
)

SAMPLE_PDF = "data/sample.pdf"
SAMPLE_TXT = "data/sample.txt"


def test_load_pdf_returns_documents():
    docs = load_file(SAMPLE_PDF)
    assert len(docs) > 0
    assert docs[0].metadata["file_type"] == "pdf"
    assert docs[0].metadata["source"] == "sample.pdf"
    assert docs[0].page_content.strip() != ""


def test_load_txt_returns_single_document():
    docs = load_file(SAMPLE_TXT)
    assert len(docs) == 1
    assert docs[0].metadata["file_type"] == "txt"


def test_load_file_not_found_raises():
    with pytest.raises(FileNotFoundError):
        load_file("data/does_not_exist.pdf")


def test_load_unsupported_extension_raises():
    # Extension check happens before the existence check, so this path
    # doesn't need to actually exist for the test to be valid.
    with pytest.raises(UnsupportedFileTypeError):
        load_file("data/sample.docx")


def test_load_files_combines_multiple():
    docs = load_files([SAMPLE_PDF, SAMPLE_TXT])
    pdf_only = load_file(SAMPLE_PDF)
    txt_only = load_file(SAMPLE_TXT)
    assert len(docs) == len(pdf_only) + len(txt_only)


# --- file_hash / dedup-support tests ------------------------------------

def test_compute_file_hash_is_deterministic():
    data = b"identical content"
    assert compute_file_hash(data) == compute_file_hash(data)


def test_compute_file_hash_differs_for_different_content():
    assert compute_file_hash(b"content A") != compute_file_hash(b"content B")


def test_loaded_documents_carry_file_hash():
    docs = load_file(SAMPLE_TXT)
    assert "file_hash" in docs[0].metadata
    assert len(docs[0].metadata["file_hash"]) > 0


def test_same_file_loaded_twice_has_same_hash():
    docs_first = load_file(SAMPLE_TXT)
    docs_second = load_file(SAMPLE_TXT)
    assert docs_first[0].metadata["file_hash"] == docs_second[0].metadata["file_hash"]


def test_pdf_pages_share_same_file_hash():
    # All pages of one PDF come from the same file, so they should all
    # carry the same file_hash (hash is per-file, not per-page).
    docs = load_file(SAMPLE_PDF)
    hashes = {doc.metadata["file_hash"] for doc in docs}
    assert len(hashes) == 1
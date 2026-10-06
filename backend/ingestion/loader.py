"""
File loaders for the ingestion pipeline.

Two entry points, for two different situations:

- `load_uploaded_files()` — for FastAPI's `UploadFile` objects (in-memory
  bytes). This is what the `/ingest` API route will call.
- `load_file()` / `load_files()` / `load_directory()` — for files already
  saved on disk. Useful for dev/debug scripts and bulk reprocessing.

Both paths converge on the same Document shape (page_content + metadata:
source, file_type, page) so downstream chunking/embedding/citation code
doesn't need to know or care which path a Document came from.
"""

import io
import os
from pathlib import Path
from typing import Iterable, List

from langchain_core.documents import Document
from pypdf import PdfReader
from helper.filehash import compute_file_hash
SUPPORTED_EXTENSIONS = {".pdf", ".txt"}


class UnsupportedFileTypeError(Exception):
    """Raised when a file extension is not supported by the ingestion pipeline."""
    pass


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _pdf_bytes_to_documents(file_bytes: bytes, source_name: str) -> List[Document]:
    """
    Parse PDF bytes into one Document per page, skipping pages with no
    extractable text (blank pages, image-only/scanned pages).

    Raises:
        ValueError: if the PDF is corrupted, encrypted, or otherwise unreadable.
    """
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except Exception as error:
        raise ValueError(
            f"Could not read PDF '{source_name}': the file may be corrupted, "
            f"password-protected, or not a valid PDF. ({error})"
        )

    if reader.is_encrypted:
        raise ValueError(
            f"Cannot process '{source_name}': the PDF is password-protected. "
            "Please upload an unencrypted version."
        )

    documents: List[Document] = []
    file_hash = compute_file_hash(file_bytes)

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            documents.append(Document(
                page_content=text,
                metadata={
                    "source": source_name,
                    "file_hash": file_hash,
                    "file_type": "pdf",
                    "page": page_number,
                    "total_pages": len(reader.pages),
                },
            ))

    return documents


def _txt_bytes_to_documents(file_bytes: bytes, source_name: str) -> List[Document]:
    """
    Decode TXT bytes into a single Document. Tries UTF-8 first, falls back
    to latin-1 (which never raises) rather than pulling in chardet as a
    dependency just for this.
    """
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1")

    if not text.strip():
        return []
    file_hash = compute_file_hash(file_bytes)
    return [Document(
        page_content=text,
        metadata={"source": source_name,"file_hash":file_hash, "file_type": "txt", "page": 1},
    )]


# ---------------------------------------------------------------------------
# Path 1: in-memory uploads (FastAPI UploadFile / Streamlit UploadedFile)
# ---------------------------------------------------------------------------

def load_uploaded_files(uploaded_files: Iterable) -> List[Document]:
    """
    Load documents from in-memory uploaded file objects.

    Expects each item to expose `.name` and `.getvalue()` (Streamlit's
    UploadedFile) or `.filename` / `.file.read()` (FastAPI's UploadFile).

    Args:
        uploaded_files: iterable of uploaded file objects.

    Returns:
        List of Document objects across all uploaded files.

    Raises:
        UnsupportedFileTypeError: if a file's extension isn't .pdf or .txt.
        ValueError: if no documents could be extracted from any file.
    """
    documents: List[Document] = []

    for uploaded_file in uploaded_files:
        file_name = getattr(uploaded_file, "name", None) or getattr(uploaded_file, "filename", None)
        if file_name is None:
            raise ValueError("Uploaded file object has no 'name' or 'filename' attribute")

        if hasattr(uploaded_file, "getvalue"):
            file_bytes = uploaded_file.getvalue()
        elif hasattr(uploaded_file, "file"):
            file_bytes = uploaded_file.file.read()
        else:
            raise ValueError(f"Don't know how to read bytes from uploaded file: {file_name}")

        extension = os.path.splitext(file_name)[1].lower()

        if extension == ".pdf":
            documents.extend(_pdf_bytes_to_documents(file_bytes, file_name))
        elif extension == ".txt":
            documents.extend(_txt_bytes_to_documents(file_bytes, file_name))
        else:
            raise UnsupportedFileTypeError(
                f"Unsupported file type '{extension}' for file '{file_name}'. "
                f"Supported types: {sorted(SUPPORTED_EXTENSIONS)}"
            )

    if not documents:
        raise ValueError("No extractable text found in the uploaded files")

    return documents


# ---------------------------------------------------------------------------
# Path 2: files on disk
# ---------------------------------------------------------------------------
def load_file(file_path: str) -> List[Document]:
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{extension}' for file '{path.name}'. "
            f"Supported types: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "rb") as f:
        file_bytes = f.read()

    if extension == ".pdf":
        return _pdf_bytes_to_documents(file_bytes, path.name)
    else:  # ".txt"
        return _txt_bytes_to_documents(file_bytes, path.name)


def load_files(file_paths: List[str]) -> List[Document]:
    """
    Load multiple files from disk, aggregating all Documents into one list.

    A failure on one file raises immediately rather than silently skipping —
    for an ingestion pipeline it's better to know a file failed than to
    quietly index a partial batch.
    """
    all_documents: List[Document] = []

    for file_path in file_paths:
        all_documents.extend(load_file(file_path))

    return all_documents


def load_directory(directory_path: str) -> List[Document]:
    """
    Load every supported file (.pdf, .txt) found directly inside a directory
    (non-recursive). Useful for bulk/manual ingestion during development.
    """
    dir_path = Path(directory_path)

    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory_path}")

    file_paths = [
        str(p) for p in sorted(dir_path.iterdir())
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    return load_files(file_paths)


async def load_fastapi_uploads(files: Iterable) -> List[Document]:
    """
    Load documents from FastAPI UploadFile objects specifically. Uses
    `await file.read()` — the correct async-safe way to read an
    UploadFile — rather than `.file.read()`, so it won't block the event
    loop on large files.
    """
    documents: List[Document] = []

    for uploaded_file in files:
        file_bytes = await uploaded_file.read()
        extension = os.path.splitext(uploaded_file.filename)[1].lower()

        if extension == ".pdf":
            documents.extend(_pdf_bytes_to_documents(file_bytes, uploaded_file.filename))
        elif extension == ".txt":
            documents.extend(_txt_bytes_to_documents(file_bytes, uploaded_file.filename))
        else:
            raise UnsupportedFileTypeError(
                f"Unsupported file type '{extension}' for file '{uploaded_file.filename}'. "
                f"Supported types: {sorted(SUPPORTED_EXTENSIONS)}"
            )

    if not documents:
        raise ValueError("No extractable text found in the uploaded files")

    return documents
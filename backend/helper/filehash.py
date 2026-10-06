import hashlib

def compute_file_hash(file_bytes: bytes) -> str:
    """Short, stable hash of file content — used to detect identical files
    and to generate deterministic chunk IDs."""
    return hashlib.sha256(file_bytes).hexdigest()[:12]
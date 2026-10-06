from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends, Request
from ingestion.pipeline import ingestion,ingest_uploaded_files
from model.ingestion import IngestionRequest, IngestionResponse
from core.auth import AuthenticatedUser, require_admin
from core.rate_limit import limiter

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB

async def _validate_file_size(file: UploadFile) -> None:
    """
    Check file size without fully loading it into memory first — reads in
    chunks until either the limit is exceeded or the file ends, then
    resets the read pointer so the real ingestion logic can read it fresh.
    """
    size = 0
    chunk_size = 1024 * 1024  # 1MB at a time
    while chunk := await file.read(chunk_size):
        size += len(chunk)
        if size > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File '{file.filename}' exceeds the {MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB size limit.",
            )
    await file.seek(0)

@router.post("", response_model=IngestionResponse, status_code=status.HTTP_201_CREATED)
def ingestion_api(payload: IngestionRequest) -> IngestionResponse:
    result = ingestion(payload.file_path)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.detail)
    return result

from db.audit import log_action

@router.post("/upload", response_model=IngestionResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
async def ingestion_upload_api(
    request: Request,
    files: list[UploadFile] = File(...),
    user: AuthenticatedUser = Depends(require_admin),
) -> IngestionResponse:
    for file in files:
        await _validate_file_size(file)
    result = await ingest_uploaded_files(files, owner_id=user.user_id)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.detail)

    log_action(
        actor_id=user.user_id, actor_email=user.email, action="document_upload",
        target=", ".join(f.source for f in (result.files or [])),
        metadata={"num_chunks": result.num_chunks, "file_hashes": [f.file_hash for f in (result.files or [])]},
    )
    return result
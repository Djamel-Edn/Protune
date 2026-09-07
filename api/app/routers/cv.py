"""CV upload and text extraction."""

from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from app.errors import FILE_TOO_LARGE, INVALID_PDF, ProtuneError
from app.schemas.cv import CvParseResponse
from app.services.cv_parser import extract_text

router = APIRouter(prefix="/cv", tags=["cv"])

# Vercel rejects request bodies over 4.5 MB before they reach this handler, so
# the cap sits below that: a clear error beats a platform-level failure.
MAX_UPLOAD_BYTES = 4 * 1024 * 1024
_CHUNK = 64 * 1024

# Annotated rather than a default argument: a call in a default trips ruff B008.
CvUpload = Annotated[UploadFile, File(description="The CV, as a PDF")]


async def _read_capped(upload: UploadFile) -> bytes:
    """Read the upload, refusing anything over the cap without buffering it all."""
    chunks: list[bytes] = []
    total = 0
    while chunk := await upload.read(_CHUNK):
        total += len(chunk)
        if total > MAX_UPLOAD_BYTES:
            raise ProtuneError(
                FILE_TOO_LARGE,
                f"This file is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
                status_code=413,
            )
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("/parse", response_model=CvParseResponse)
async def parse_cv(file: CvUpload) -> CvParseResponse:
    data = await _read_capped(file)

    if not data:
        raise ProtuneError(INVALID_PDF, "The uploaded file is empty.")

    extracted = extract_text(data)
    return CvParseResponse(
        raw_text=extracted.raw_text,
        page_count=extracted.page_count,
        character_count=len(extracted.raw_text),
        truncated=extracted.truncated,
    )

"""Domain errors and their HTTP representation.

Error codes are part of the public API contract: the frontend branches on
`code`, never on the human-readable message.
"""

from fastapi import Request
from fastapi.responses import JSONResponse


class ProtuneError(Exception):
    """An error worth showing to the user, with a stable machine-readable code."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


# Contract codes — see docs/PLAN.md §5.
INVALID_PDF = "INVALID_PDF"
PARSE_FAILED = "PARSE_FAILED"
FILE_TOO_LARGE = "FILE_TOO_LARGE"
RATE_LIMITED = "RATE_LIMITED"
QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
SCRAPE_FAILED = "SCRAPE_FAILED"


async def protune_error_handler(_: Request, exc: ProtuneError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )

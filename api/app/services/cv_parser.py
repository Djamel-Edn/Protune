"""Deterministic text extraction from CV files.

This layer is intentionally free of any LLM call: it either reads the PDF's
text layer or it fails with a precise reason. Turning that text into a
structured CV is the generation pipeline's job, which keeps uploads fast and
this module exhaustively testable.
"""

import io
import re
from dataclasses import dataclass

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.errors import INVALID_PDF, PARSE_FAILED, ProtuneError

# A CV beyond this length is almost certainly not a CV; the cap also bounds
# what downstream prompts have to pay for.
MAX_CHARACTERS = 20_000

# Below this, the document has no usable text layer — typically a scan.
MIN_MEANINGFUL_CHARACTERS = 120

_WHITESPACE = re.compile(r"[ \t ]+")
_BLANK_LINES = re.compile(r"\n{3,}")


@dataclass(frozen=True)
class ExtractedCv:
    raw_text: str
    page_count: int
    truncated: bool


def _normalise(text: str) -> str:
    """Collapse the ragged whitespace PDF extraction produces."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _WHITESPACE.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    return _BLANK_LINES.sub("\n\n", text).strip()


def extract_text(data: bytes) -> ExtractedCv:
    """Extract the text layer of a PDF CV.

    Raises ProtuneError with INVALID_PDF when the bytes are not a readable PDF,
    and PARSE_FAILED when the PDF opens but carries no usable text.
    """
    if not data.startswith(b"%PDF-"):
        raise ProtuneError(
            INVALID_PDF,
            "That file is not a PDF. Export your CV as a PDF and try again.",
            status_code=415,
        )

    try:
        reader = PdfReader(io.BytesIO(data))
    except (PdfReadError, ValueError, OSError) as exc:
        raise ProtuneError(
            INVALID_PDF, "This PDF could not be opened — it may be corrupted."
        ) from exc

    if reader.is_encrypted:
        # An owner-password-only PDF opens with an empty user password.
        try:
            opened = reader.decrypt("")
        except (NotImplementedError, PdfReadError):
            opened = 0
        if not opened:
            raise ProtuneError(
                INVALID_PDF,
                "This PDF is password-protected. Remove the password and try again.",
            )

    try:
        pages = [page.extract_text() or "" for page in reader.pages]
    except (PdfReadError, ValueError, KeyError) as exc:
        raise ProtuneError(PARSE_FAILED, "The text of this PDF could not be read.") from exc

    text = _normalise("\n".join(pages))

    if len(text) < MIN_MEANINGFUL_CHARACTERS:
        raise ProtuneError(
            PARSE_FAILED,
            "No text could be read from this PDF. If it is a scan, export a text-based "
            "PDF instead — an image of a CV cannot be analysed.",
            status_code=422,
        )

    truncated = len(text) > MAX_CHARACTERS
    return ExtractedCv(
        raw_text=text[:MAX_CHARACTERS],
        page_count=len(reader.pages),
        truncated=truncated,
    )

"""Fetches the text of a job posting from its URL.

Uses r.jina.ai, which renders the page and returns readable text. It needs no
API key, and it was already the approach proven in the n8n prototype.
"""

import logging

import httpx

from app.errors import SCRAPE_FAILED, ProtuneError

logger = logging.getLogger(__name__)

_READER = "https://r.jina.ai/"
_TIMEOUT = httpx.Timeout(45.0, connect=10.0)

# Postings are truncated before they reach a prompt: beyond this, the extra text
# is navigation and legal boilerplate, and it is paid for on every call.
MAX_CHARACTERS = 4_000


def _validate(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        raise ProtuneError(SCRAPE_FAILED, "That does not look like a job posting URL.")
    return url


async def fetch_posting(url: str, transport: httpx.AsyncBaseTransport | None = None) -> str:
    """Return the readable text of a job posting page."""
    url = _validate(url)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, transport=transport) as client:
            response = await client.get(f"{_READER}{url}", follow_redirects=True)
    except httpx.HTTPError as exc:
        logger.warning("Reader unreachable for %s: %s", url, exc)
        raise ProtuneError(
            SCRAPE_FAILED,
            "That page could not be read. Paste the posting text instead.",
            status_code=502,
        ) from exc

    if response.status_code != 200:
        logger.warning("Reader returned %s for %s", response.status_code, url)
        raise ProtuneError(
            SCRAPE_FAILED,
            "That page could not be read — it may require a login. "
            "Paste the posting text instead.",
            status_code=502,
        )

    text = response.text.strip()
    if len(text) < 200:
        raise ProtuneError(
            SCRAPE_FAILED,
            "Almost nothing could be read from that page. Paste the posting text instead.",
            status_code=422,
        )
    return text[:MAX_CHARACTERS]

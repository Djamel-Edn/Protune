"""Scraper tests. No network: every call goes through a MockTransport."""

import httpx
import pytest

from app.errors import SCRAPE_FAILED, ProtuneError
from app.services.scraper import MAX_CHARACTERS, fetch_posting

POSTING = "Data Engineer apprenticeship at Servier. " * 20


def _transport(response: httpx.Response) -> httpx.MockTransport:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return response

    transport = httpx.MockTransport(handler)
    transport.captured = captured  # type: ignore[attr-defined]
    return transport


async def test_returns_the_page_text():
    text = await fetch_posting(
        "https://example.com/job", _transport(httpx.Response(200, text=POSTING))
    )
    assert "Servier" in text


async def test_the_url_is_passed_to_the_reader():
    transport = _transport(httpx.Response(200, text=POSTING))
    await fetch_posting("https://example.com/job", transport)
    assert "r.jina.ai/https://example.com/job" in str(transport.captured[0].url)  # type: ignore[attr-defined]


@pytest.mark.parametrize("url", ["not-a-url", "ftp://example.com", "", "   "])
async def test_rejects_anything_that_is_not_an_http_url(url):
    with pytest.raises(ProtuneError) as caught:
        await fetch_posting(url, _transport(httpx.Response(200, text=POSTING)))
    assert caught.value.code == SCRAPE_FAILED


async def test_a_login_wall_suggests_pasting_the_text():
    with pytest.raises(ProtuneError) as caught:
        await fetch_posting("https://example.com/job", _transport(httpx.Response(403)))
    assert "paste" in caught.value.message.lower()


async def test_an_almost_empty_page_is_refused():
    with pytest.raises(ProtuneError) as caught:
        await fetch_posting("https://example.com/job", _transport(httpx.Response(200, text="Job")))
    assert caught.value.status_code == 422


async def test_a_very_long_posting_is_truncated():
    text = await fetch_posting(
        "https://example.com/job", _transport(httpx.Response(200, text="x" * 50_000))
    )
    assert len(text) == MAX_CHARACTERS


async def test_an_unreachable_reader_is_reported_cleanly():
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route", request=request)

    with pytest.raises(ProtuneError) as caught:
        await fetch_posting("https://example.com/job", httpx.MockTransport(boom))
    assert caught.value.code == SCRAPE_FAILED

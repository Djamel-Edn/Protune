"""Tests for the streamed generation endpoint.

Gemini and the scraper are replaced at the router level, so nothing here
touches the network or spends quota.
"""

import json

import pytest
from fastapi.testclient import TestClient

from app.errors import QUOTA_EXCEEDED, SCRAPE_FAILED, ProtuneError
from app.main import app
from app.routers import generate as generate_router
from app.schemas.generation import AdaptedCv, CoverLetter, CvProject, OfferAnalysis

client = TestClient(app)

CV = "Djamel Dib. Engineering student at ESIGELEC, AI and Big Data. Python, SQL, Docker."

ANALYSIS = OfferAnalysis(
    role="Data Engineer",
    company="Servier",
    language="French",
    key_skills=["Python"],
    ats_keywords=["data engineer"],
)
LETTER = CoverLetter(paragraphs=["Premier paragraphe.", "Second paragraphe."])
ADAPTED = AdaptedCv(
    headline="Alternant Data Engineer",
    summary="Resume.",
    projects=[CvProject(title="Datathon", description="Premier prix.")],
    skills=["Python"],
)


class FakeGemini:
    """Stands in for GeminiClient, optionally failing at a chosen stage."""

    def __init__(self, settings, fail_at: str | None = None, error: ProtuneError | None = None):
        self.fail_at = fail_at
        self.error = error or ProtuneError(QUOTA_EXCEEDED, "Quota reached.", 429)

    def _maybe_fail(self, stage: str) -> None:
        if self.fail_at == stage:
            raise self.error

    async def analyse_offer(self, offer_text):
        self._maybe_fail("analyse")
        return ANALYSIS

    async def write_letter(self, cv_text, analysis, reference_letter=""):
        self._maybe_fail("letter")
        return LETTER

    async def adapt_cv(self, cv_text, analysis):
        self._maybe_fail("cv")
        return ADAPTED


@pytest.fixture
def fake_gemini(monkeypatch):
    def install(**kwargs):
        monkeypatch.setattr(
            generate_router, "GeminiClient", lambda settings: FakeGemini(settings, **kwargs)
        )

    install()
    return install


def parse_stream(text: str) -> list[tuple[str, dict]]:
    """Turn a raw SSE body into (event name, payload) pairs."""
    events = []
    for block in text.strip().split("\n\n"):
        lines = block.splitlines()
        name = next(line[7:] for line in lines if line.startswith("event: "))
        data = next(line[6:] for line in lines if line.startswith("data: "))
        events.append((name, json.loads(data)))
    return events


def _post(**overrides):
    payload = {"cv_text": CV, "offer_text": "Alternance Data Engineer chez Servier. " * 5}
    payload.update(overrides)
    return client.post("/api/v1/generate", json=payload)


def test_streams_every_stage_in_order(fake_gemini):
    response = _post()
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    names = [name for name, _ in parse_stream(response.text)]
    assert names.index("analysis") < names.index("letter") < names.index("cv")
    assert names[-1] == "done"


def test_each_payload_is_the_typed_result(fake_gemini):
    events = dict(parse_stream(_post().text))
    assert events["analysis"]["company"] == "Servier"
    assert events["letter"]["paragraphs"][0] == "Premier paragraphe."
    assert events["cv"]["projects"][0]["title"] == "Datathon"
    assert events["done"]["duration_ms"] >= 0


def test_pasted_text_skips_the_scraper(fake_gemini):
    steps = [p for name, p in parse_stream(_post().text) if name == "step"]
    assert {"step": "read", "status": "running"} not in steps
    assert {"step": "read", "status": "done"} in steps


def test_a_url_is_scraped(fake_gemini, monkeypatch):
    seen = {}

    async def fake_fetch(url, transport=None):
        seen["url"] = url
        return "Alternance Data Engineer chez Servier. " * 5

    monkeypatch.setattr(generate_router, "fetch_posting", fake_fetch)
    events = parse_stream(_post(offer_text="", offer_url="https://example.com/job").text)
    assert seen["url"] == "https://example.com/job"
    assert ("step", {"step": "read", "status": "running"}) in events


def test_a_failure_mid_stream_arrives_as_an_error_event(fake_gemini):
    fake_gemini(fail_at="letter")
    events = parse_stream(_post().text)
    names = [name for name, _ in events]

    # The analysis already reached the client and must not be thrown away.
    assert "analysis" in names
    assert names[-1] == "error"
    assert "done" not in names
    assert dict(events)["error"]["code"] == QUOTA_EXCEEDED


def test_a_scrape_failure_is_reported_as_an_event(fake_gemini, monkeypatch):
    async def boom(url, transport=None):
        raise ProtuneError(SCRAPE_FAILED, "That page could not be read.", 502)

    monkeypatch.setattr(generate_router, "fetch_posting", boom)
    events = dict(parse_stream(_post(offer_text="", offer_url="https://example.com/x").text))
    assert events["error"]["code"] == SCRAPE_FAILED


def test_an_unexpected_crash_does_not_leak_internals(fake_gemini, monkeypatch):
    class Exploding(FakeGemini):
        async def analyse_offer(self, offer_text):
            raise RuntimeError("connection string postgres://user:pa55w0rd@host/db")

    monkeypatch.setattr(generate_router, "GeminiClient", lambda settings: Exploding(settings))
    events = dict(parse_stream(_post().text))
    assert events["error"]["code"] == "INTERNAL"
    assert "pa55w0rd" not in json.dumps(events)


def test_a_request_without_any_posting_is_refused_before_streaming():
    response = _post(offer_text="", offer_url="")
    assert response.status_code == 422


def test_a_request_without_a_cv_is_refused_before_streaming():
    response = _post(cv_text="too short")
    assert response.status_code == 422

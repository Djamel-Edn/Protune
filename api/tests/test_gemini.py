"""Gemini client tests. No network: every call goes through a MockTransport."""

import json

import httpx
import pytest

from app.config import Settings
from app.errors import QUOTA_EXCEEDED, RATE_LIMITED, ProtuneError
from app.services import gemini
from app.services.gemini import GeminiClient


def _settings(**overrides) -> Settings:
    return Settings(gemini_api_key="test-key", **overrides)


def _reply(payload: dict, status: int = 200) -> httpx.Response:
    body = {"candidates": [{"content": {"parts": [{"text": json.dumps(payload)}]}}]}
    return httpx.Response(status, json=body)


def _transport(*responses: httpx.Response) -> httpx.MockTransport:
    """Replays the given responses in order, repeating the last one."""
    queue = list(responses)
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return queue.pop(0) if len(queue) > 1 else queue[0]

    transport = httpx.MockTransport(handler)
    transport.captured = captured  # type: ignore[attr-defined]
    return transport


@pytest.fixture(autouse=True)
def _no_real_backoff(monkeypatch):
    monkeypatch.setattr(gemini, "_BACKOFF_SECONDS", (0.0, 0.0))


ANALYSIS = {
    "role": "Data Engineer",
    "company": "Servier",
    "location": "Paris",
    "sector": "Pharmaceutical",
    "contract_type": "Apprenticeship",
    "key_skills": ["Python", "Spark"],
    "ats_keywords": ["data engineer", "airflow"],
}


async def test_analyse_offer_returns_a_typed_analysis():
    client = GeminiClient(_settings(), _transport(_reply(ANALYSIS)))
    analysis = await client.analyse_offer("Alternance Data Engineer chez Servier")
    assert analysis.company == "Servier"
    assert analysis.key_skills == ["Python", "Spark"]


async def test_the_api_key_travels_in_a_header_not_the_url():
    transport = _transport(_reply(ANALYSIS))
    await GeminiClient(_settings(), transport).analyse_offer("...")
    request = transport.captured[0]  # type: ignore[attr-defined]
    assert request.headers["x-goog-api-key"] == "test-key"
    assert "test-key" not in str(request.url)


async def test_the_request_pins_a_response_schema():
    transport = _transport(_reply(ANALYSIS))
    await GeminiClient(_settings(), transport).analyse_offer("...")
    body = json.loads(transport.captured[0].content)  # type: ignore[attr-defined]
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert "role" in body["generationConfig"]["responseSchema"]["properties"]


async def test_a_rate_limit_is_retried_then_succeeds():
    transport = _transport(httpx.Response(429, json={}), _reply(ANALYSIS))
    analysis = await GeminiClient(_settings(), transport).analyse_offer("...")
    assert analysis.company == "Servier"
    assert len(transport.captured) == 2  # type: ignore[attr-defined]


async def test_persistent_rate_limiting_gives_up_with_a_clear_error():
    transport = _transport(httpx.Response(429, json={}))
    with pytest.raises(ProtuneError) as caught:
        await GeminiClient(_settings(), transport).analyse_offer("...")
    assert caught.value.code == RATE_LIMITED
    assert len(transport.captured) == 3  # type: ignore[attr-defined]


async def test_a_rejected_key_is_not_retried_and_never_leaks():
    transport = _transport(httpx.Response(403, json={"error": {"message": "API key not valid"}}))
    with pytest.raises(ProtuneError) as caught:
        await GeminiClient(_settings(), transport).analyse_offer("...")
    assert caught.value.code == QUOTA_EXCEEDED
    assert "key" not in caught.value.message.lower()
    assert len(transport.captured) == 1  # type: ignore[attr-defined]


async def test_an_exhausted_quota_says_so():
    transport = _transport(
        httpx.Response(400, json={"error": {"message": "Quota exceeded for requests"}})
    )
    with pytest.raises(ProtuneError) as caught:
        await GeminiClient(_settings(), transport).analyse_offer("...")
    assert caught.value.code == QUOTA_EXCEEDED
    assert caught.value.status_code == 429


async def test_fenced_json_is_still_parsed():
    """responseSchema should prevent this, but the prototype was bitten by it."""
    fenced = {
        "candidates": [{"content": {"parts": [{"text": '```json\n{"paragraphs":["a"]}\n```'}]}}]
    }
    transport = _transport(httpx.Response(200, json=fenced))
    letter = await GeminiClient(_settings(), transport).write_letter("cv", gemini.OfferAnalysis())
    assert letter.paragraphs == ["a"]


async def test_unparseable_output_becomes_a_clean_error():
    broken = {"candidates": [{"content": {"parts": [{"text": "I cannot help with that."}]}}]}
    transport = _transport(httpx.Response(200, json=broken))
    with pytest.raises(ProtuneError):
        await GeminiClient(_settings(), transport).analyse_offer("...")


async def test_a_blocked_response_becomes_a_clean_error():
    transport = _transport(httpx.Response(200, json={"candidates": []}))
    with pytest.raises(ProtuneError):
        await GeminiClient(_settings(), transport).analyse_offer("...")


async def test_a_missing_key_fails_before_any_request():
    transport = _transport(_reply(ANALYSIS))
    with pytest.raises(ProtuneError) as caught:
        await GeminiClient(Settings(gemini_api_key=""), transport).analyse_offer("...")
    assert caught.value.status_code == 503
    assert transport.captured == []  # type: ignore[attr-defined]


async def test_a_reference_letter_reaches_the_prompt():
    transport = _transport(_reply({"paragraphs": ["one"]}))
    await GeminiClient(_settings(), transport).write_letter(
        "cv text", gemini.OfferAnalysis(company="Servier"), reference_letter="My old letter."
    )
    prompt = json.loads(transport.captured[0].content)["contents"][0]["parts"][0]["text"]  # type: ignore[attr-defined]
    assert "My old letter." in prompt
    assert "Servier" in prompt


async def test_without_a_reference_letter_the_prompt_says_so():
    transport = _transport(_reply({"paragraphs": ["one"]}))
    await GeminiClient(_settings(), transport).write_letter("cv", gemini.OfferAnalysis())
    prompt = json.loads(transport.captured[0].content)["contents"][0]["parts"][0]["text"]  # type: ignore[attr-defined]
    assert "no sample letter" in prompt


async def test_adapt_cv_returns_projects():
    payload = {
        "headline": "Data Engineer",
        "summary": "Summary.",
        "projects": [{"title": "Datathon", "description": "First place."}],
        "skills": ["Python"],
    }
    client = GeminiClient(_settings(), _transport(_reply(payload)))
    adapted = await client.adapt_cv("cv text", gemini.OfferAnalysis())
    assert adapted.projects[0].title == "Datathon"

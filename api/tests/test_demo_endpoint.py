"""The quota endpoint, and the quota check guarding /generate."""

from fastapi.testclient import TestClient

from app.errors import RATE_LIMITED, ProtuneError
from app.main import app
from app.routers import demo as demo_router
from app.routers import generate as generate_router
from app.services.rate_limit import Quota

client = TestClient(app)


def test_quota_reports_that_nothing_is_enforced_without_upstash():
    body = client.get("/api/v1/demo/quota").json()
    assert body["limit"] == 3
    assert body["enforced"] is False
    assert body["resets_at"].endswith("+00:00")


def test_quota_reads_the_visitor_behind_the_proxy(monkeypatch):
    seen = {}

    async def fake_peek(ip, settings, transport=None):
        seen["ip"] = ip
        return Quota(remaining=1, limit=3, resets_at="2026-09-08T00:00:00+00:00", enforced=True)

    monkeypatch.setattr(demo_router, "peek", fake_peek)
    body = client.get("/api/v1/demo/quota", headers={"x-forwarded-for": "9.9.9.9, 10.0.0.1"}).json()
    assert seen["ip"] == "9.9.9.9"
    assert body == {
        "remaining": 1,
        "limit": 3,
        "resets_at": "2026-09-08T00:00:00+00:00",
        "enforced": True,
    }


def test_a_spent_quota_refuses_generate_before_the_stream_opens(monkeypatch):
    """The refusal must be a real status code, not an event inside a 200."""

    async def spent(ip, settings, transport=None):
        raise ProtuneError(RATE_LIMITED, "You have used your 3 generations for today.", 429)

    monkeypatch.setattr(generate_router, "consume", spent)
    response = client.post(
        "/api/v1/generate",
        json={"cv_text": "x" * 60, "offer_text": "y" * 60},
    )
    assert response.status_code == 429
    assert response.json()["code"] == RATE_LIMITED
    assert not response.headers["content-type"].startswith("text/event-stream")

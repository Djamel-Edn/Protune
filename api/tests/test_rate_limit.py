"""Rate limiter tests. Upstash is replaced by a MockTransport throughout."""

import httpx
import pytest

from app.config import Settings
from app.errors import QUOTA_EXCEEDED, RATE_LIMITED, ProtuneError
from app.services.rate_limit import Quota, client_ip, consume, hash_ip, peek


def _settings(**overrides) -> Settings:
    base = {
        "upstash_redis_rest_url": "https://fake.upstash.io",
        "upstash_redis_rest_token": "token",
        "ip_hash_salt": "pepper",
    }
    base.update(overrides)
    return Settings(**base)


def _redis(*results: int) -> httpx.MockTransport:
    """Answers a pipeline call with the given results, in order."""
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json=[{"result": value} for value in results])

    transport = httpx.MockTransport(handler)
    transport.captured = captured  # type: ignore[attr-defined]
    return transport


# --- hashing and address extraction -----------------------------------------


def test_the_hash_is_salted_so_the_ipv4_space_cannot_be_walked():
    assert hash_ip("1.2.3.4", "pepper") != hash_ip("1.2.3.4", "other-pepper")


def test_the_same_visitor_hashes_consistently():
    assert hash_ip("1.2.3.4", "pepper") == hash_ip("1.2.3.4", "pepper")


def test_the_raw_address_never_appears_in_the_hash():
    assert "1.2.3.4" not in hash_ip("1.2.3.4", "pepper")


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        ({"x-forwarded-for": "9.9.9.9, 10.0.0.1, 10.0.0.2"}, "9.9.9.9"),
        ({"x-forwarded-for": "  9.9.9.9  "}, "9.9.9.9"),
        ({"x-real-ip": "8.8.8.8"}, "8.8.8.8"),
        ({}, "unknown"),
    ],
)
def test_the_client_address_is_read_from_the_proxy_headers(headers, expected):
    assert client_ip(headers) == expected


# --- consuming --------------------------------------------------------------


async def test_a_first_generation_is_allowed_and_counted():
    quota = await consume("1.2.3.4", _settings(), _redis(1, 1, 1, 1))
    assert quota.remaining == 2
    assert quota.enforced


async def test_both_counters_are_incremented_in_one_round_trip():
    transport = _redis(1, 1, 1, 1)
    await consume("1.2.3.4", _settings(), transport)
    commands = transport.captured[0].content.decode()  # type: ignore[attr-defined]
    assert len(transport.captured) == 1  # type: ignore[attr-defined]
    assert "demo:ip:" in commands
    assert "demo:global:" in commands
    assert "EXPIRE" in commands


async def test_the_raw_address_is_never_sent_to_the_store():
    transport = _redis(1, 1, 1, 1)
    await consume("203.0.113.7", _settings(), transport)
    assert "203.0.113.7" not in transport.captured[0].content.decode()  # type: ignore[attr-defined]


async def test_a_visitor_over_their_allowance_is_refused():
    with pytest.raises(ProtuneError) as caught:
        await consume("1.2.3.4", _settings(), _redis(4, 1, 4, 1))
    assert caught.value.code == RATE_LIMITED
    assert caught.value.status_code == 429


async def test_the_global_ceiling_wins_over_the_personal_one():
    """A fresh visitor still gets a clear answer once the shared quota is spent."""
    with pytest.raises(ProtuneError) as caught:
        await consume("1.2.3.4", _settings(), _redis(1, 1, 999, 1))
    assert caught.value.code == QUOTA_EXCEEDED
    assert "own free Gemini key" in caught.value.message


async def test_an_unreachable_limiter_lets_the_request_through():
    """Losing the counter must not take the demo down with it."""

    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("upstash unreachable", request=request)

    quota = await consume("1.2.3.4", _settings(), httpx.MockTransport(boom))
    assert quota.enforced is False


async def test_without_upstash_the_limiter_says_it_is_not_enforcing():
    quota = await consume("1.2.3.4", Settings(), _redis(1, 1, 1, 1))
    assert quota == Quota(3, 3, quota.resets_at, False)


# --- peeking ----------------------------------------------------------------


async def test_peeking_reports_what_is_left_without_spending_it():
    transport = _redis(2)
    quota = await peek("1.2.3.4", _settings(), transport)
    assert quota.remaining == 1
    assert "GET" in transport.captured[0].content.decode()  # type: ignore[attr-defined]
    assert "INCR" not in transport.captured[0].content.decode()  # type: ignore[attr-defined]


async def test_peeking_a_spent_allowance_reports_zero_not_a_negative():
    quota = await peek("1.2.3.4", _settings(), _redis(9))
    assert quota.remaining == 0

"""Daily quotas for the public demo.

Two counters, both in Upstash Redis so they survive the serverless runtime
throwing instances away: one per visitor, one for everyone combined. The
global one exists because the Gemini free tier is a shared, exhaustible
resource — without it a single busy night empties the day's allowance and the
demo is dead for whoever looks next.

IP addresses are never stored. Only a salted hash is, which is enough to count
against and useless to anyone reading the database.
"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

import httpx

from app.config import Settings
from app.errors import QUOTA_EXCEEDED, RATE_LIMITED, ProtuneError

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(5.0, connect=3.0)
_DAY_SECONDS = 60 * 60 * 24


@dataclass(frozen=True)
class Quota:
    remaining: int
    limit: int
    resets_at: str
    enforced: bool


def _today() -> str:
    return date.today().isoformat()


def _resets_at() -> str:
    tomorrow = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )
    return tomorrow.isoformat()


def hash_ip(ip: str, salt: str) -> str:
    """Salted so the hashes cannot be reversed by walking the IPv4 space.

    Four billion addresses is nothing to brute-force; the salt is the only
    thing making this hash worth anything.
    """
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()[:32]


def client_ip(headers: dict[str, str]) -> str:
    """The visitor's address, as the proxy in front of us reports it."""
    forwarded = headers.get("x-forwarded-for", "")
    if forwarded:
        # The left-most entry is the original client; the rest are proxies.
        return forwarded.split(",")[0].strip()
    return headers.get("x-real-ip", "").strip() or "unknown"


async def _pipeline(
    settings: Settings, commands: list[list[str]], transport: httpx.AsyncBaseTransport | None
) -> list[int]:
    """Run several Redis commands in one round trip, returning their results."""
    async with httpx.AsyncClient(timeout=_TIMEOUT, transport=transport) as client:
        response = await client.post(
            f"{settings.upstash_redis_rest_url.rstrip('/')}/pipeline",
            json=commands,
            headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"},
        )
    response.raise_for_status()
    return [int(entry.get("result") or 0) for entry in response.json()]


async def consume(
    ip: str, settings: Settings, transport: httpx.AsyncBaseTransport | None = None
) -> Quota:
    """Count one generation against both quotas, refusing if either is spent."""
    if not settings.rate_limiting_enabled:
        return Quota(settings.demo_daily_limit, settings.demo_daily_limit, _resets_at(), False)

    day = _today()
    per_ip = f"demo:ip:{hash_ip(ip, settings.ip_hash_salt)}:{day}"
    global_key = f"demo:global:{day}"

    try:
        used, _, used_globally, _ = await _pipeline(
            settings,
            [
                ["INCR", per_ip],
                ["EXPIRE", per_ip, str(_DAY_SECONDS), "NX"],
                ["INCR", global_key],
                ["EXPIRE", global_key, str(_DAY_SECONDS), "NX"],
            ],
            transport,
        )
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        # Letting a generation through beats taking the demo down because a
        # counter is unreachable.
        logger.warning("Rate limiter unavailable, allowing the request: %s", exc)
        return Quota(settings.demo_daily_limit, settings.demo_daily_limit, _resets_at(), False)

    if used_globally > settings.demo_global_daily_limit:
        raise ProtuneError(
            QUOTA_EXCEEDED,
            "The shared daily demo quota is spent. It resets at midnight UTC — "
            "or run Protune yourself with your own free Gemini key.",
            status_code=429,
        )

    if used > settings.demo_daily_limit:
        raise ProtuneError(
            RATE_LIMITED,
            f"You have used your {settings.demo_daily_limit} generations for today. "
            "The counter resets at midnight UTC.",
            status_code=429,
        )

    return Quota(
        remaining=max(0, settings.demo_daily_limit - used),
        limit=settings.demo_daily_limit,
        resets_at=_resets_at(),
        enforced=True,
    )


async def peek(
    ip: str, settings: Settings, transport: httpx.AsyncBaseTransport | None = None
) -> Quota:
    """Read the visitor's remaining allowance without spending any of it."""
    if not settings.rate_limiting_enabled:
        return Quota(settings.demo_daily_limit, settings.demo_daily_limit, _resets_at(), False)

    key = f"demo:ip:{hash_ip(ip, settings.ip_hash_salt)}:{_today()}"
    try:
        (used,) = await _pipeline(settings, [["GET", key]], transport)
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        logger.warning("Rate limiter unavailable while reading quota: %s", exc)
        return Quota(settings.demo_daily_limit, settings.demo_daily_limit, _resets_at(), False)

    return Quota(
        remaining=max(0, settings.demo_daily_limit - used),
        limit=settings.demo_daily_limit,
        resets_at=_resets_at(),
        enforced=True,
    )

"""Gemini client for the generation pipeline.

Two deliberate differences from the n8n prototype this was ported from:

- responses are requested with `responseSchema`, so the model returns parseable
  JSON by construction. The prototype asked for JSON in prose and then stripped
  ```json fences from the answer, which failed whenever the model phrased itself
  differently.
- the candidate's profile is no longer baked into the prompts. It arrives as CV
  text, which is what makes this multi-tenant rather than personal.
"""

import asyncio
import json
import logging
import re
from typing import Any

import httpx

from app.config import Settings
from app.errors import QUOTA_EXCEEDED, RATE_LIMITED, ProtuneError
from app.prompts import render
from app.schemas.generation import (
    ADAPTED_CV_SCHEMA,
    ANALYSIS_SCHEMA,
    LETTER_SCHEMA,
    AdaptedCv,
    CoverLetter,
    OfferAnalysis,
)

logger = logging.getLogger(__name__)

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
_TIMEOUT = httpx.Timeout(90.0, connect=10.0)

# The free tier allows 15 requests per minute; a burst of retries would make a
# rate limit worse, so back off rather than hammer.
_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = (2.0, 6.0)

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _strip_fences(text: str) -> str:
    """Defensive fallback: responseSchema should make this a no-op."""
    return _FENCE.sub("", text).strip()


class GeminiClient:
    """Wraps the three generation calls. One instance per request is fine."""

    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self._settings = settings
        self._transport = transport

    async def _generate(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        if not self._settings.gemini_api_key:
            raise ProtuneError(
                QUOTA_EXCEEDED,
                "The generator is not configured on this deployment.",
                status_code=503,
            )

        url = f"{_BASE_URL}/{self._settings.gemini_model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": schema,
            },
        }
        # The key travels in a header, never in the URL: URLs end up in logs.
        headers = {"x-goog-api-key": self._settings.gemini_api_key}

        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=_TIMEOUT, transport=self._transport) as client:
            for attempt in range(_MAX_ATTEMPTS):
                try:
                    response = await client.post(url, json=payload, headers=headers)
                except httpx.HTTPError as exc:
                    last_error = exc
                else:
                    if response.status_code == 200:
                        return self._extract(response.json())
                    if response.status_code not in (429, 500, 503):
                        self._raise_for(response)
                    last_error = httpx.HTTPStatusError(
                        f"Gemini returned {response.status_code}",
                        request=response.request,
                        response=response,
                    )

                if attempt < _MAX_ATTEMPTS - 1:
                    await asyncio.sleep(_BACKOFF_SECONDS[attempt])

        logger.warning("Gemini unavailable after %s attempts: %s", _MAX_ATTEMPTS, last_error)
        raise ProtuneError(
            RATE_LIMITED,
            "The generator is busy right now. Try again in a minute.",
            status_code=503,
        )

    @staticmethod
    def _raise_for(response: httpx.Response) -> None:
        detail = ""
        try:
            detail = response.json().get("error", {}).get("message", "")
        except ValueError:
            detail = response.text[:200]

        if response.status_code in (401, 403):
            logger.error("Gemini rejected the API key: %s", detail)
            raise ProtuneError(
                QUOTA_EXCEEDED,
                "The generator is not configured correctly on this deployment.",
                status_code=503,
            )
        if "quota" in detail.lower():
            raise ProtuneError(
                QUOTA_EXCEEDED,
                "The daily generation quota has been reached. Try again tomorrow.",
                status_code=429,
            )
        logger.error("Gemini error %s: %s", response.status_code, detail)
        raise ProtuneError(
            RATE_LIMITED, "The generator failed to answer. Try again.", status_code=502
        )

    @staticmethod
    def _extract(body: dict[str, Any]) -> dict[str, Any]:
        try:
            text = body["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            # A blocked or empty candidate lands here.
            raise ProtuneError(
                RATE_LIMITED, "The generator returned nothing usable. Try again.", 502
            ) from exc
        try:
            return json.loads(_strip_fences(text))
        except json.JSONDecodeError as exc:
            logger.error("Gemini returned unparseable JSON: %s", text[:300])
            raise ProtuneError(
                RATE_LIMITED, "The generator returned a malformed answer. Try again.", 502
            ) from exc

    async def analyse_offer(self, offer_text: str) -> OfferAnalysis:
        data = await self._generate(render("analyse_offer", offer_text=offer_text), ANALYSIS_SCHEMA)
        return OfferAnalysis.model_validate(data)

    async def write_letter(
        self, cv_text: str, analysis: OfferAnalysis, reference_letter: str = ""
    ) -> CoverLetter:
        style = (
            "A LETTER THE CANDIDATE WROTE BEFORE. Match its tone and rhythm, "
            f"never its content:\n{reference_letter}"
            if reference_letter.strip()
            else "The candidate gave no sample letter. Write plainly and specifically, "
            "in the register of the posting itself."
        )
        data = await self._generate(
            render(
                "write_letter",
                cv_text=cv_text,
                analysis=analysis.model_dump_json(indent=2),
                style_guidance=style,
                language=analysis.language or "English",
            ),
            LETTER_SCHEMA,
        )
        return CoverLetter.model_validate(data)

    async def adapt_cv(self, cv_text: str, analysis: OfferAnalysis) -> AdaptedCv:
        data = await self._generate(
            render(
                "adapt_cv",
                cv_text=cv_text,
                analysis=analysis.model_dump_json(indent=2),
                language=analysis.language or "English",
            ),
            ADAPTED_CV_SCHEMA,
        )
        return AdaptedCv.model_validate(data)

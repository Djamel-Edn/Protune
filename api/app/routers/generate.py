"""The generation pipeline, streamed as server-sent events.

Generation takes fifteen to thirty seconds across three sequential model calls.
Streaming is not decoration: a dead progress bar for that long loses the user.
Each stage is published the moment it completes, so the letter is on screen
while the CV is still being written.

The endpoint is a POST, so browsers cannot consume it with EventSource, which
is GET-only. The frontend reads the body stream directly.
"""

import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.config import Settings, SettingsDep
from app.errors import ProtuneError
from app.schemas.generation import GenerateRequest
from app.services.gemini import GeminiClient
from app.services.scraper import fetch_posting

logger = logging.getLogger(__name__)

router = APIRouter(tags=["generate"])


def _event(name: str, payload: dict[str, Any]) -> str:
    return f"event: {name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _step(step: str, status: str) -> str:
    return _event("step", {"step": step, "status": status})


async def _run(request: GenerateRequest, settings: Settings) -> AsyncIterator[str]:
    started = time.monotonic()
    client = GeminiClient(settings)

    try:
        if request.offer_text.strip():
            offer_text = request.offer_text.strip()
        else:
            yield _step("read", "running")
            offer_text = await fetch_posting(request.offer_url)
        yield _step("read", "done")

        yield _step("analyse", "running")
        analysis = await client.analyse_offer(offer_text)
        yield _event("analysis", analysis.model_dump())
        yield _step("analyse", "done")

        yield _step("letter", "running")
        letter = await client.write_letter(request.cv_text, analysis, request.reference_letter)
        yield _event("letter", letter.model_dump())
        yield _step("letter", "done")

        yield _step("cv", "running")
        adapted = await client.adapt_cv(request.cv_text, analysis)
        yield _event("cv", adapted.model_dump())
        yield _step("cv", "done")

        yield _event(
            "done",
            {
                "duration_ms": int((time.monotonic() - started) * 1000),
                "model": settings.gemini_model,
            },
        )
    except ProtuneError as exc:
        # The response has already begun, so its status code is fixed at 200:
        # a failure has to travel as an event or the client sees a truncated
        # stream and no reason for it.
        yield _event("error", {"code": exc.code, "message": exc.message})
    except Exception:
        logger.exception("Generation failed unexpectedly")
        yield _event(
            "error",
            {"code": "INTERNAL", "message": "Generation failed. Please try again."},
        )


@router.post("/generate")
async def generate(request: GenerateRequest, settings: SettingsDep) -> StreamingResponse:
    return StreamingResponse(
        _run(request, settings),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )

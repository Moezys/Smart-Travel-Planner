"""Async webhook delivery — fire-and-forget, never blocks the HTTP response.

Supports Discord embeds natively (detected by URL containing
'discord.com/api/webhooks').  Any other URL receives a generic JSON payload.

Retry policy: 2 attempts, 1-second wait between them, 10-second per-request
timeout.  All failures are logged with structured fields and silently swallowed
so a dead webhook can never take down the user-facing response.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(10.0)
_DISCORD_BLUE = 0x0EA5E9  # brand-500


# --------------------------------------------------------------------------- #
# Payload builders                                                             #
# --------------------------------------------------------------------------- #

def _cost_usd(
    cheap_in: int, cheap_out: int, strong_in: int, strong_out: int
) -> float:
    # Gemma-4-31b-it approximate pricing ($/1M tokens)
    IN_PRICE, OUT_PRICE = 0.14, 0.28
    return (
        (cheap_in + strong_in) * IN_PRICE
        + (cheap_out + strong_out) * OUT_PRICE
    ) / 1_000_000


def _discord_payload(
    question: str,
    answer: str,
    usage: dict,
    tool_names: list[str],
) -> dict:
    total_tokens = usage.get("total_in", 0) + usage.get("total_out", 0)
    cost = _cost_usd(
        usage.get("cheap_in", 0), usage.get("cheap_out", 0),
        usage.get("strong_in", 0), usage.get("strong_out", 0),
    )
    # Discord embed description cap is 4096 chars
    desc = answer[:3900] + ("…" if len(answer) > 3900 else "")
    return {
        "username": "Smart Travel Planner",
        "embeds": [
            {
                "title": f"🗺️ {question[:250]}",
                "description": desc,
                "color": _DISCORD_BLUE,
                "fields": [
                    {
                        "name": "Tools used",
                        "value": ", ".join(tool_names) or "none",
                        "inline": True,
                    },
                    {
                        "name": "Tokens",
                        "value": f"{total_tokens:,}",
                        "inline": True,
                    },
                    {
                        "name": "Est. cost",
                        "value": f"${cost:.5f}",
                        "inline": True,
                    },
                ],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ],
    }


def _generic_payload(
    question: str,
    answer: str,
    usage: dict,
    tool_names: list[str],
) -> dict:
    return {
        "event": "trip_recommendation",
        "question": question,
        "answer": answer,
        "tools_used": tool_names,
        "token_usage": usage,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# --------------------------------------------------------------------------- #
# HTTP delivery with retry                                                     #
# --------------------------------------------------------------------------- #

@retry(
    stop=stop_after_attempt(2),
    wait=wait_fixed(1),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    reraise=True,
)
async def _post(url: str, payload: dict) -> None:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()


# --------------------------------------------------------------------------- #
# Public API                                                                   #
# --------------------------------------------------------------------------- #

async def fire_webhook(
    url: str,
    question: str,
    answer: str,
    usage: dict,
    tool_names: list[str],
) -> None:
    """Deliver the trip plan to *url*.  All errors are logged, never raised."""
    is_discord = "discord.com/api/webhooks" in url
    payload = (
        _discord_payload(question, answer, usage, tool_names)
        if is_discord
        else _generic_payload(question, answer, usage, tool_names)
    )
    try:
        await _post(url, payload)
        logger.info(
            "webhook.sent url=%s tokens=%s",
            url, usage.get("total_in", 0) + usage.get("total_out", 0),
        )
    except httpx.HTTPStatusError as exc:
        logger.error(
            "webhook.http_error status=%s url=%s body=%.200s",
            exc.response.status_code, url, exc.response.text,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("webhook.failed error=%r url=%s", exc, url)


def schedule_webhook(
    url: str | None,
    question: str,
    answer: str,
    usage: dict,
    tool_names: list[str],
) -> None:
    """Create a background asyncio task for webhook delivery.

    Safe to call from any async context.  Returns immediately; the HTTP
    request runs after the caller's coroutine yields.
    """
    if not url:
        return
    asyncio.create_task(
        fire_webhook(url, question, answer, usage, tool_names)
    )

"""Async Voyage embeddings client.

The client itself is a process-wide singleton (``lru_cache``) so we don't
re-handshake TLS on every call. ``embed_texts`` batches inputs to stay
under Voyage's per-request token / item limits and returns a list of
vectors in the same order as the inputs.

Rate-limit handling
-------------------
Voyage's free tier (no payment method on file) is **3 RPM and 10k TPM**.
Without throttling, a 1000-chunk ingest will burst into ``RateLimitError``
within seconds. To be friendly to free-tier users we:

  1. Cap the batch token count to fit one minute's allowance (with margin).
  2. Keep concurrent requests at 1 (the SDK is already async, but parallel
     calls just race each other into the same RPM bucket).
  3. Sleep ``min_seconds_between_calls`` (defaults to 21s ≈ 60s/3RPM)
     between batches.
  4. Retry on ``RateLimitError`` with exponential backoff in case the
     server's window is slightly out of sync with ours.

The throttle is dynamic: ``settings.voyage_free_tier`` toggles it. Users
who have added a payment method on the Voyage dashboard set
``VOYAGE_FREE_TIER=false`` and the throttle drops out — restoring native
throughput.
"""

from __future__ import annotations

import asyncio
import time
from functools import lru_cache
from typing import Literal

import voyageai
from voyageai.error import RateLimitError

from app.config import get_settings


# Free tier ceilings: 3 RPM AND 10K TPM (binding ANDed). With both
# constraints active, the safe envelope is ~3000 tokens per request,
# spaced ~22 s apart -> ~3 RPM and ~8200 TPM. Going wider on either
# axis trips the other one within seconds.
_FREE_TIER_BATCH_TOKENS = 3000
_FREE_TIER_BATCH_ITEMS = 12
_FREE_TIER_MIN_SECONDS = 22.0

_PAID_TIER_BATCH_ITEMS = 96
_PAID_TIER_MIN_SECONDS = 0.0

_MAX_RETRIES = 5
_RETRY_BACKOFF_SECS = 5.0


@lru_cache(maxsize=1)
def get_voyage_client() -> voyageai.AsyncClient:
    settings = get_settings()
    api_key = settings.voyage_api_key.get_secret_value()
    if not api_key:
        raise RuntimeError(
            "VOYAGE_API_KEY is empty — set it in .env before running ingest.",
        )
    return voyageai.AsyncClient(api_key=api_key)


def _est_tokens(text: str) -> int:
    return max(1, int(round(len(text.split()) * 1.3)))


def _pack_batches(texts: list[str], free_tier: bool) -> list[list[str]]:
    """Pack texts into batches that fit both item and token caps."""
    if free_tier:
        max_items = _FREE_TIER_BATCH_ITEMS
        max_tokens = _FREE_TIER_BATCH_TOKENS
    else:
        max_items = _PAID_TIER_BATCH_ITEMS
        max_tokens = 100_000  # Voyage cap is 120k

    batches: list[list[str]] = []
    cur: list[str] = []
    cur_tokens = 0
    for t in texts:
        tt = _est_tokens(t)
        if cur and (len(cur) >= max_items or cur_tokens + tt > max_tokens):
            batches.append(cur)
            cur, cur_tokens = [], 0
        cur.append(t)
        cur_tokens += tt
    if cur:
        batches.append(cur)
    return batches


async def _embed_batch(
    client: voyageai.AsyncClient,
    texts: list[str],
    *,
    input_type: Literal["document", "query"],
) -> list[list[float]]:
    settings = get_settings()
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            res = await client.embed(
                texts=texts,
                model=settings.voyage_model,
                input_type=input_type,
                output_dimension=settings.voyage_dim,
            )
            return res.embeddings
        except RateLimitError as exc:
            last_exc = exc
            wait = _RETRY_BACKOFF_SECS * (2 ** attempt)
            print(f"      [rate-limited] sleeping {wait:.0f}s "
                  f"(attempt {attempt + 1}/{_MAX_RETRIES})")
            await asyncio.sleep(wait)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt == _MAX_RETRIES - 1:
                break
            await asyncio.sleep(_RETRY_BACKOFF_SECS * (2 ** attempt))
    assert last_exc is not None
    raise last_exc


async def embed_texts(
    texts: list[str],
    *,
    input_type: Literal["document", "query"] = "document",
) -> list[list[float]]:
    """Embed a list of strings, batching + throttling internally.

    Order is preserved. On free tier this serializes calls and inserts
    sleeps between them so we do not blow the 3 RPM ceiling.
    """
    if not texts:
        return []
    settings = get_settings()
    client = get_voyage_client()
    free_tier = settings.voyage_free_tier
    min_gap = _FREE_TIER_MIN_SECONDS if free_tier else _PAID_TIER_MIN_SECONDS

    batches = _pack_batches(texts, free_tier=free_tier)
    out: list[list[float]] = []
    last_call_t = 0.0
    for i, batch in enumerate(batches, 1):
        # Honour the per-call cooldown.
        if min_gap > 0:
            elapsed = time.monotonic() - last_call_t
            if last_call_t > 0 and elapsed < min_gap:
                await asyncio.sleep(min_gap - elapsed)
        if free_tier:
            print(f"      batch {i}/{len(batches)} ({len(batch)} items)")
        out.extend(await _embed_batch(client, batch, input_type=input_type))
        last_call_t = time.monotonic()
    return out


async def embed_query(text: str) -> list[float]:
    """Convenience wrapper for the single-query case used at retrieval time."""
    [vec] = await embed_texts([text], input_type="query")
    return vec

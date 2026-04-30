"""Async Wikivoyage fetcher.

Uses the MediaWiki TextExtracts extension to fetch plain-text article
content with section headers preserved (``exsectionformat=wiki``). That's
exactly what the chunker downstream wants: clean text with ``==Section==``
markers it can split on.

API docs: https://en.wikivoyage.org/w/api.php?action=help&modules=query%2Bextracts
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import quote

import httpx

from app.config import get_settings


_API_URL = "https://en.wikivoyage.org/w/api.php"
_MAX_RETRIES = 3
_RETRY_BACKOFF_SECS = 1.5
_REQUEST_TIMEOUT = 30.0


@dataclass(slots=True, frozen=True)
class FetchedPage:
    title: str
    url: str
    text: str
    fetched_at: datetime


def _page_url(title: str) -> str:
    return f"https://en.wikivoyage.org/wiki/{quote(title.replace(' ', '_'))}"


async def fetch_page(client: httpx.AsyncClient, title: str) -> FetchedPage:
    """Fetch a single Wikivoyage page as plain text with section markers."""
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "extracts",
        "explaintext": "1",
        "exsectionformat": "wiki",
        "redirects": "1",
        "titles": title,
    }

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = await client.get(_API_URL, params=params, timeout=_REQUEST_TIMEOUT)
            resp.raise_for_status()
            payload = resp.json()
            break
        except (httpx.HTTPError, ValueError) as exc:
            last_exc = exc
            if attempt == _MAX_RETRIES - 1:
                raise
            await asyncio.sleep(_RETRY_BACKOFF_SECS * (2 ** attempt))
    else:
        assert last_exc is not None
        raise last_exc

    pages = payload.get("query", {}).get("pages", [])
    if not pages:
        raise ValueError(f"No page returned for title={title!r}")

    page = pages[0]
    if page.get("missing"):
        raise ValueError(f"Wikivoyage page not found: {title!r}")

    extract = page.get("extract", "").strip()
    if not extract:
        raise ValueError(f"Empty extract for {title!r}")

    return FetchedPage(
        title=page.get("title", title),
        url=_page_url(page.get("title", title)),
        text=extract,
        fetched_at=datetime.now(timezone.utc),
    )


async def fetch_pages(titles: list[str], *, concurrency: int = 4) -> list[FetchedPage]:
    """Fetch many titles concurrently with a small semaphore."""
    semaphore = asyncio.Semaphore(concurrency)
    results: list[FetchedPage] = []

    user_agent = get_settings().wikivoyage_user_agent
    async with httpx.AsyncClient(headers={"User-Agent": user_agent}) as client:

        async def _one(title: str) -> FetchedPage | None:
            async with semaphore:
                try:
                    return await fetch_page(client, title)
                except Exception as exc:  # noqa: BLE001
                    print(f"  [WARN] {title!r}: {exc}")
                    return None

        tasks = [_one(t) for t in titles]
        for fut in asyncio.as_completed(tasks):
            page = await fut
            if page is not None:
                results.append(page)

    return results

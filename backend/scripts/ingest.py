"""End-to-end RAG ingest: fetch -> chunk -> embed -> persist.

Idempotent — re-running it deletes existing documents/chunks for each
destination and re-inserts. We rely on FK ``ON DELETE CASCADE`` to clear
the chunks when a document is removed.

Run with:
    uv run python -m scripts.ingest
"""

from __future__ import annotations

import asyncio
import sys
import time

import httpx

# psycopg's async driver doesn't work with the default ProactorEventLoop
# on Windows. Switch to the selector-based loop before anything imports
# the engine.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import session_scope
from app.models import Chunk, Destination, Document
from app.services.chunking import (
    TextChunk,
    chunk_document,
    filter_sections,
    reorder_by_priority,
)
from app.services.embeddings import embed_texts
from app.services.wikivoyage import FetchedPage, fetch_page
from scripts.destinations import SEEDS, DestinationSeed


# After section filtering (logistics dropped), cap each page so the
# chunk count stays inside the free-tier rate budget. 15K chars after
# filtering is roughly the See/Do/Understand/Eat/Drink prose for a
# typical Wikivoyage destination article.
MAX_CHARS_PER_PAGE = 15_000


async def _upsert_destination(session: AsyncSession, seed: DestinationSeed) -> Destination:
    stmt = select(Destination).where(
        Destination.name == seed.name,
        Destination.country == seed.country,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        existing.region = seed.region
        existing.archetype = seed.archetype
        return existing
    dest = Destination(
        name=seed.name, country=seed.country,
        region=seed.region, archetype=seed.archetype,
    )
    session.add(dest)
    await session.flush()  # populate dest.id
    return dest


async def _wipe_documents(session: AsyncSession, destination_id: int) -> None:
    """Hard-delete the destination's existing documents (and their chunks)."""
    await session.execute(
        delete(Document).where(Document.destination_id == destination_id),
    )


async def _persist_one(
    session: AsyncSession,
    destination: Destination,
    page: FetchedPage,
    chunks: list[TextChunk],
    embeddings: list[list[float]],
) -> None:
    doc = Document(
        destination_id=destination.id,
        source="wikivoyage",
        source_url=page.url,
        title=page.title,
        raw_text=page.text,
        fetched_at=page.fetched_at,
    )
    session.add(doc)
    await session.flush()

    rows: list[Chunk] = []
    for ch, vec in zip(chunks, embeddings, strict=True):
        rows.append(Chunk(
            document_id=doc.id,
            chunk_index=ch.chunk_index,
            section=ch.section,
            text=ch.text,
            token_count=ch.token_count,
            embedding=vec,
        ))
    session.add_all(rows)


async def _fetch_all(
    seeds: list[DestinationSeed],
) -> list[tuple[DestinationSeed, list[FetchedPage]]]:
    """Fetch all pages for all seeds, preserving the seed -> pages mapping.

    We make one ``(seed, title)`` task per page so the seed binding is
    captured explicitly — no URL-string heuristics are needed to put the
    fetched page back with its seed.
    """
    user_agent = get_settings().wikivoyage_user_agent
    semaphore = asyncio.Semaphore(4)
    groups: dict[int, list[FetchedPage]] = {id(s): [] for s in seeds}

    async with httpx.AsyncClient(headers={"User-Agent": user_agent}) as client:

        async def _one(seed: DestinationSeed, title: str) -> None:
            async with semaphore:
                try:
                    page = await fetch_page(client, title)
                except Exception as exc:  # noqa: BLE001
                    print(f"  [WARN] {seed.name}/{title!r}: {exc}")
                    return
                groups[id(seed)].append(page)

        tasks = [
            _one(seed, title)
            for seed in seeds
            for title in seed.wikivoyage_pages
        ]
        await asyncio.gather(*tasks)

    return [(seed, groups[id(seed)]) for seed in seeds]


async def main() -> None:
    t0 = time.perf_counter()
    seeds = list(SEEDS)
    print(f"[1/4] fetching {sum(len(s.wikivoyage_pages) for s in seeds)} "
          f"Wikivoyage pages across {len(seeds)} destinations ...")
    groups = await _fetch_all(seeds)
    fetched = sum(len(p) for _, p in groups)
    print(f"      got {fetched} pages back")

    # Pipeline:
    #   raw -> drop logistics H2s -> reorder so See/Do/Eat lead -> cap by
    #   char budget -> section-aware chunk
    # The raw_text column keeps the unmodified original so we can re-chunk
    # later without re-fetching.
    print(f"[2/4] filter + reorder + chunk (cap={MAX_CHARS_PER_PAGE} chars) ...")
    work: list[tuple[DestinationSeed, FetchedPage, list[TextChunk]]] = []
    total_chunks = 0
    for seed, pages in groups:
        for page in pages:
            body = filter_sections(page.text)
            body = reorder_by_priority(body)
            if MAX_CHARS_PER_PAGE and len(body) > MAX_CHARS_PER_PAGE:
                body = body[:MAX_CHARS_PER_PAGE]
            # Use the page title (e.g. "Bali") as the breadcrumb prefix —
            # not the seed name — so a sub-page under Ubud's seed reads
            # "Bali > See" rather than the misleading "Ubud > See".
            chunks = chunk_document(body, destination_name=page.title)
            if not chunks:
                print(f"  [WARN] {seed.name}/{page.title}: 0 chunks (empty?)")
                continue
            work.append((seed, page, chunks))
            total_chunks += len(chunks)
    print(f"      produced {total_chunks} chunks across {len(work)} documents")

    # Embed in one big call (Voyage batches internally).
    print(f"[3/4] embedding {total_chunks} chunks via Voyage ...")
    flat_texts = [c.text for _, _, chunks in work for c in chunks]
    flat_vecs = await embed_texts(flat_texts, input_type="document")
    print(f"      received {len(flat_vecs)} vectors of dim "
          f"{len(flat_vecs[0]) if flat_vecs else 0}")

    # Slice the flat embedding list back to per-document.
    sliced: list[list[list[float]]] = []
    cursor = 0
    for _, _, chunks in work:
        sliced.append(flat_vecs[cursor : cursor + len(chunks)])
        cursor += len(chunks)

    # Persist.
    print("[4/4] persisting to Postgres ...")
    async with session_scope() as session:
        for seed in seeds:
            dest = await _upsert_destination(session, seed)
            await _wipe_documents(session, dest.id)
        await session.flush()

        for (seed, page, chunks), vecs in zip(work, sliced, strict=True):
            stmt = select(Destination).where(
                Destination.name == seed.name,
                Destination.country == seed.country,
            )
            dest = (await session.execute(stmt)).scalar_one()
            await _persist_one(session, dest, page, chunks, vecs)

        await session.commit()

    elapsed = time.perf_counter() - t0
    print(f"\ndone in {elapsed:.1f}s — {fetched} docs, {total_chunks} chunks")


if __name__ == "__main__":
    asyncio.run(main())

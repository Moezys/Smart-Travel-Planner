"""Retrieval entry-point.

The agent's RAG tool calls ``retrieve(query, k)``. Internally:
  1. Voyage embeds the query (``input_type="query"``).
  2. pgvector ranks chunks by cosine distance against the query vector.
  3. The top-k chunks plus their (destination, document) breadcrumbs are
     returned as Pydantic models.

Cosine distance is ``embedding <=> query`` in pgvector — smaller is more
similar, so we sort ASC and convert to a similarity score in [0, 1] for
human-readable output.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Chunk, Destination, Document
from app.services.embeddings import embed_query


class RetrievedChunk(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: int
    destination: str
    country: str
    archetype: str | None
    document_title: str
    section: str | None
    text: str
    similarity: float = Field(ge=0.0, le=1.0)


async def retrieve(
    session: AsyncSession,
    query: str,
    *,
    k: int = 5,
    archetype_filter: str | None = None,
) -> list[RetrievedChunk]:
    """Top-k cosine-similarity retrieval over the chunks table.

    Parameters
    ----------
    session :
        Caller-provided async session (so the agent or a route handler can
        keep retrieval inside its own transaction).
    query :
        Natural-language query string.
    k :
        Number of chunks to return.
    archetype_filter :
        Optional travel-style filter (``"Adventure"``, ``"Culture"``, ...).
        Useful when the agent has already classified intent and wants to
        bias retrieval toward matching destinations.
    """
    qvec = await embed_query(query)
    distance = Chunk.embedding.cosine_distance(qvec)

    stmt = (
        select(
            Chunk.id,
            Chunk.section,
            Chunk.text,
            Document.title.label("document_title"),
            Destination.name.label("destination"),
            Destination.country,
            Destination.archetype,
            distance.label("distance"),
        )
        .join(Document, Chunk.document_id == Document.id)
        .join(Destination, Document.destination_id == Destination.id)
        .order_by(distance.asc())
        .limit(k)
    )
    if archetype_filter:
        stmt = stmt.where(Destination.archetype == archetype_filter)

    rows = (await session.execute(stmt)).all()
    return [
        RetrievedChunk(
            chunk_id=r.id,
            destination=r.destination,
            country=r.country,
            archetype=r.archetype,
            document_title=r.document_title,
            section=r.section,
            text=r.text,
            # Cosine distance is 0..2 for unit vectors. Voyage returns
            # already-L2-normalised vectors so distance lives in [0, 2];
            # similarity = 1 - distance/2 keeps it in [0, 1].
            similarity=max(0.0, min(1.0, 1.0 - float(r.distance) / 2.0)),
        )
        for r in rows
    ]

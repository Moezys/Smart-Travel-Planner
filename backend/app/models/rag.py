"""ORM models for the RAG pipeline.

    Destination ── 1:N ── Document ── 1:N ── Chunk(embedding)

A Destination is a place the agent can reason about (Rome, Bali, ...).
Each destination has one or more raw source Documents (Wikivoyage main
article, district sub-pages, etc.). Each Document is split into Chunks,
and each Chunk carries a Voyage embedding stored as a pgvector column.

The embedding column dimension is read from settings (``voyage_dim``) at
import time so the schema and the embedding API call agree.
"""

from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import get_settings
from app.models.base import Base


_EMBED_DIM = get_settings().voyage_dim


class Destination(Base):
    __tablename__ = "destinations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    country: Mapped[str] = mapped_column(String(80), nullable=False)
    region: Mapped[str] = mapped_column(String(40), nullable=False)
    archetype: Mapped[str | None] = mapped_column(String(20), nullable=True)

    documents: Mapped[list["Document"]] = relationship(
        back_populates="destination", cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("name", "country", name="uq_destinations_name_country"),
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    destination_id: Mapped[int] = mapped_column(
        ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    source: Mapped[str] = mapped_column(String(40), nullable=False)  # e.g. "wikivoyage"
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    destination: Mapped[Destination] = relationship(back_populates="documents")
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("source", "source_url", name="uq_documents_source_url"),
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[str | None] = mapped_column(String(200), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(_EMBED_DIM), nullable=False)

    document: Mapped[Document] = relationship(back_populates="chunks")

    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index",
                         name="uq_chunks_document_chunk_index"),
        # Approximate-NN index on the embedding column. Cosine distance
        # matches Voyage's normalised output. lists=100 is a safe default
        # for our ~500-row scale; bump if we grow past ~50k chunks.
        Index(
            "ix_chunks_embedding_cosine",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

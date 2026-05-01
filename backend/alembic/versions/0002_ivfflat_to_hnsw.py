"""Replace IVFFlat index with HNSW on chunks.embedding.

IVFFlat needs data at CREATE INDEX time to build its centroids; when the
index is created by an Alembic migration on an empty table the centroids
are garbage and the index returns near-empty results.  HNSW builds the
graph incrementally as rows are inserted so it works correctly regardless
of whether data exists when the index is created.

Revision ID: 0002_ivfflat_to_hnsw
Revises: 0001_initial_rag
Create Date: 2026-05-01
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "0002_ivfflat_to_hnsw"
down_revision: Union[str, Sequence[str], None] = "0001_initial_rag"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chunks_embedding_cosine")
    op.execute(
        "CREATE INDEX ix_chunks_embedding_cosine "
        "ON chunks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chunks_embedding_cosine")
    op.execute(
        "CREATE INDEX ix_chunks_embedding_cosine "
        "ON chunks USING ivfflat (embedding vector_cosine_ops) "
        "WITH (lists = 100)"
    )

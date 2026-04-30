# Smart Travel Planner — backend

Async FastAPI + LangGraph agent + pgvector RAG. This README covers the
backend only — the full project README lives at the repo root.

## Quick start

```bash
# 1. Postgres + pgvector
docker compose up -d                     # host port 5433 -> container 5432
# 2. Apply migrations
uv run alembic upgrade head              # creates extension + tables
# 3. Train + persist the ML classifier (optional — already saved)
uv run jupyter nbconvert --execute notebook/notebook.ipynb
# 4. Ingest the RAG corpus
uv run python -m scripts.ingest          # ~15 min on Voyage free tier
# 5. Sanity-check retrieval
uv run python -m scripts.eval_rag
```

`uv sync` installs runtime + dev dependencies. Copy `.env.example` to
`.env` and fill in `VOYAGE_API_KEY` before running the ingest.

## Layout

```
backend/
  app/
    config.py           # pydantic-settings — single source of truth
    db.py               # async engine + sessionmaker singletons
    models/             # SQLAlchemy ORM (Destination, Document, Chunk)
    services/
      chunking.py       # section-aware splitter
      embeddings.py     # async Voyage client + free-tier throttle
      rag.py            # retrieve(query, k) — top-k cosine retrieval
      wikivoyage.py     # async MediaWiki TextExtracts fetcher
  scripts/
    destinations.py     # 13 destinations × 22 Wikivoyage pages
    ingest.py           # fetch -> chunk -> embed -> persist
    eval_rag.py         # 12 hand-written sanity-check queries
  alembic/              # migrations
  data/                 # destinations.csv + dataset builder
  notebook/notebook.ipynb
  model/                # joblib classifier + results.csv
  docker-compose.yml
```

## Stage 1 — ML classifier

See `notebook/notebook.ipynb`. Six-class travel-style classifier
(Adventure, Relaxation, Culture, Budget, Luxury, Family) trained on a
1057-row dataset compiled from country baselines + place-name tags. The
notebook documents leakage avoidance (drop `name`, `country`,
`sub_region`), three-classifier comparison with stratified 5-fold CV,
GridSearchCV tuning, per-class metrics, and persistence to
`model/travel_style_classifier.joblib`.

## Stage 2 — RAG over Wikivoyage

### Corpus

13 destinations covering all 6 archetypes (3 Adventure, 3 Relaxation,
3 Culture, 2 Luxury, 1 Budget, 1 Family). Each destination has 1–2
Wikivoyage pages — 22 documents in total, well within the 20–30 spec
range.

| Archetype  | Destinations                              |
| ---------- | ----------------------------------------- |
| Adventure  | Reykjavik, Banff, El Calafate             |
| Relaxation | Ubud, Malé, Mykonos                       |
| Culture    | Rome, Kyoto, Marrakech                    |
| Luxury     | Dubai, St. Moritz                         |
| Budget     | Hanoi                                     |
| Family     | Orlando                                   |

Source: Wikivoyage MediaWiki API (`prop=extracts&explaintext=1&exsectionformat=wiki`).
That endpoint returns plain text with `==Section==` markers preserved,
which is exactly the input shape the chunker wants. Fetcher is async,
respects Wikimedia's User-Agent policy (configurable via
`WIKIVOYAGE_USER_AGENT`), and retries with exponential backoff.

### Chunking strategy

Two-pass, section-aware splitter (`app/services/chunking.py`):

1. **Split on section headers** (`==H2==`, `===H3===`, `====H4====`).
   Each section becomes a candidate chunk. The breadcrumb path
   (`Rome > See > Ancient Rome`) is preserved.
2. **Token budget per chunk** — if the section fits inside the budget
   (default 400 tokens) it goes in whole; if not, a sliding window splits
   it with overlap (default 60 tokens).
3. **Breadcrumb prefix** — every chunk is written as
   `"<destination> > <section path>\n\n<body>"` so the retriever has the
   structural context the body would otherwise lose.

**Why these defaults?**

- **`target_tokens=400`** — Voyage's `voyage-4-large` performs best on
  inputs in the 200–600-token range; smaller chunks lose context, larger
  chunks dilute the topic. Wikivoyage's "See", "Do", "Eat" sections
  cluster around 200–800 tokens, so 400 lets most sections go in whole
  while still windowing the long ones.
- **`overlap_tokens=60`** — ~15% of the chunk size. Enough to catch
  cross-boundary references ("the trail mentioned above") without
  ballooning chunk count.
- **Token estimation** — `len(text.split()) * 1.3`. Voyage doesn't
  publish a tokenizer; this approximation is good to ±10% on English
  prose and the chunker only needs ballpark sizing.

### Embedding

`voyage-4-large` at 1024 dimensions (`output_dimension=1024`,
`input_type="document"` for ingest, `input_type="query"` at retrieval).
Stored as `pgvector` `Vector(1024)` columns. Distance metric is
**cosine** — Voyage returns L2-normalised vectors so cosine and dot are
equivalent.

The embedder (`app/services/embeddings.py`) auto-throttles when
`VOYAGE_FREE_TIER=true` (default) — 24 items per batch, 21 s between
calls — to fit the free tier's 3 RPM / 10K TPM ceiling. Set
`VOYAGE_FREE_TIER=false` after adding a payment method on the Voyage
dashboard for native throughput.

### Retrieval

`app/services/rag.py:retrieve(session, query, k=5, archetype_filter=None)`
returns the top-k chunks ranked by cosine distance. The query is
embedded once per call (`input_type="query"`); ranking is done in
Postgres via `Chunk.embedding.cosine_distance(qvec)` which the ivfflat
index `ix_chunks_embedding_cosine` accelerates.

The optional `archetype_filter` is for the agent: once the LLM decides
the user wants Adventure or Relaxation, retrieval can be pre-filtered to
matching destinations before the cosine ranking — biasing the result set
toward the intent rather than re-ranking after the fact.

### Pre-flight evaluation

12 hand-written queries in `scripts/eval_rag.py`, one per destination.
Each query is a vague natural-language travel intent ("Quiet yoga and
rice-paddy walks in a tropical setting") with the destination(s) we
expect to surface in the top-5. Run with:

```bash
uv run python -m scripts.eval_rag
```

This is the gate before plugging RAG into the agent — if a clearly
on-topic query doesn't return its target destination, the chunking,
embedding model, or breadcrumb formatting is wrong, and we fix it before
the agent ever sees the corpus.

## Configuration

All env vars live in `.env` and are typed in `app/config.py`. Required:

| Var                | Purpose                                  |
| ------------------ | ---------------------------------------- |
| `VOYAGE_API_KEY`   | Voyage embeddings (ingest + retrieval)   |
| `DATABASE_URL`     | Async psycopg URL — runtime              |
| `DATABASE_URL_SYNC`| Sync psycopg URL — Alembic migrations    |

Optional overrides include `VOYAGE_MODEL`, `VOYAGE_DIM`,
`VOYAGE_FREE_TIER`, `WIKIVOYAGE_USER_AGENT`, `ML_MODEL_PATH`. See
`.env.example` for the full list.

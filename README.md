# Smart Travel Planner

AIE Bootcamp Week 4 capstone. A full-stack travel recommendation assistant powered by a LangGraph ReAct agent, pgvector RAG over Wikivoyage, and a six-class ML travel-style classifier.

---

## Quick start

### Docker (recommended — one command)

```bash
# Copy and fill in your API keys
cp backend/.env.example backend/.env

docker compose up --build
```

| Service  | URL                          |
| -------- | ---------------------------- |
| Frontend | http://localhost:3000        |
| Backend  | http://localhost:8000        |
| Postgres | localhost:5433 (host access) |

The backend container runs `alembic upgrade head` automatically on startup.
Data survives restarts via the named volume `stp_pgdata`.

### Local dev

```bash
# 1. Start Postgres only
cd backend && docker compose up -d

# 2. Backend
cd backend
uv sync
cp .env.example .env   # fill in keys
uv run alembic upgrade head
uv run python run.py   # http://localhost:8000

# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev            # http://localhost:5173
```

---

## Architecture

```
browser ──► nginx (port 3000)
              │
              ├─ /         React SPA (Vite + Tailwind v4)
              │
              └─ /api/ ──► FastAPI (port 8000)
                              │
                              └─ LangGraph ReAct agent
                                   ├─ rag_search         (pgvector cosine retrieval)
                                   ├─ classify_destination (scikit-learn classifier)
                                   └─ get_weather         (Open-Meteo)
```

**Two-model routing** — a cheap model handles all tool-selection and argument-extraction rounds; a strong model does final synthesis only. `MAX_TOOL_ROUNDS = 6` guards against infinite loops.

---

## Stages

### Stage 1 — ML classifier

Six-class travel-style classifier (Adventure, Relaxation, Culture, Budget, Luxury, Family) trained on a 1 057-row dataset. See `backend/notebook/notebook.ipynb` for the full write-up: leakage avoidance, three-classifier comparison with stratified 5-fold CV, GridSearchCV tuning, per-class metrics, and persistence to `backend/model/travel_style_classifier.joblib`.

### Stage 2 — RAG over Wikivoyage

**Corpus** — 13 destinations, 22 Wikivoyage documents, covering all 6 archetypes.

| Archetype  | Destinations                    |
| ---------- | ------------------------------- |
| Adventure  | Reykjavik, Banff, El Calafate   |
| Relaxation | Ubud, Malé, Mykonos             |
| Culture    | Rome, Kyoto, Marrakech          |
| Luxury     | Dubai, St. Moritz               |
| Budget     | Hanoi                           |
| Family     | Orlando                         |

**Chunking** — two-pass, section-aware splitter. Each Wikivoyage section becomes a candidate chunk (target 400 tokens, 60-token overlap on long sections). Every chunk is prefixed with a breadcrumb (`Rome > See > Ancient Rome`) so the retriever retains structural context.

**Embedding** — `voyage-4-large` at 1 024 dimensions, stored in pgvector. Distance metric is cosine (Voyage returns L2-normalised vectors). The HNSW index (`ix_chunks_embedding_hnsw`) is used at query time.

**Retrieval** — `rag.retrieve(session, query, k=5, archetype_filter=None)`. An optional archetype filter pre-narrows the candidate set before cosine ranking.

To ingest the corpus from scratch:

```bash
cd backend
uv run python -m scripts.ingest     # ~15 min on Voyage free tier
uv run python -m scripts.eval_rag   # 12 sanity-check queries
```

### Stage 3 — LangGraph ReAct agent

`backend/app/agent/graph.py`. State machine with three nodes:

- `tool_selection` — cheap model picks the next tool (or decides to stop)
- `tool_execution` — runs the selected LangChain tool
- `synthesis` — strong model writes the final response

### Stage 4 — Persistence

Every chat run is stored in `agent_runs` with full token counts. Each tool invocation is stored in `tool_calls`. Alembic manages the schema.

### Stage 5 — Auth

JWT-based auth (`python-jose`, `passlib[bcrypt]`). Register → login → Bearer token. Webhook URL stored per user.

### Stage 6 — Frontend

React 19 + TypeScript + Vite + Tailwind v4. Dark theme (`#0f1117` / `#161b25`).

- **Chat page** — suggestion chips, animated typing indicator, collapsible tool-call drawer, per-message token + cost footer
- **History page** — expandable run cards with colour-coded tool badges
- **Webhook modal** — save a Discord or generic HTTP URL; the backend delivers trip plans as rich embeds

### Stage 7 — Webhook delivery

`backend/app/services/webhook.py`. Fire-and-forget (`asyncio.create_task`). Two retries with 1 s backoff, 10 s timeout per attempt. Delivery failure never blocks the API response. Detects Discord webhook URLs and sends rich embeds; all other URLs receive generic JSON.

### Stage 8 — Docker

`docker compose up --build` at the repo root starts all three services. The backend container runs migrations on startup. Postgres data persists in the named volume `stp_pgdata`.

---

## Project layout

```
smart-travel-planner/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic/            migrations (0001–0004)
│   ├── app/
│   │   ├── config.py       pydantic-settings — single source of truth
│   │   ├── db.py           async engine + sessionmaker
│   │   ├── main.py         FastAPI app + lifespan
│   │   ├── agent/
│   │   │   ├── graph.py    LangGraph ReAct state machine
│   │   │   └── tools.py    rag_search, classify_destination, get_weather
│   │   ├── api/
│   │   │   ├── agent.py    POST /api/chat
│   │   │   ├── auth.py     POST /api/auth/register|login, GET|PATCH /api/auth/me
│   │   │   └── history.py  GET /api/history
│   │   ├── models/         SQLAlchemy ORM (User, AgentRun, ToolCall, Chunk …)
│   │   └── services/       auth, webhook, run_logger, rag, embeddings, classifier
│   ├── model/              travel_style_classifier.joblib
│   ├── scripts/            ingest.py, eval_rag.py
│   └── notebook/           notebook.ipynb (Stage 1 write-up)
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    └── src/
        ├── pages/          ChatPage, HistoryPage, AuthPage
        ├── components/     ChatMessage, ToolCallDrawer, WebhookSettings
        ├── contexts/       AuthContext (JWT + localStorage)
        └── lib/            api.ts, utils.ts
```

---

## Configuration

All env vars are declared and typed in `backend/app/config.py`. Copy `backend/.env.example` to `backend/.env` and fill in the required keys:

| Variable            | Required | Purpose                              |
| ------------------- | -------- | ------------------------------------ |
| `VOYAGE_API_KEY`    | yes      | Voyage embeddings (ingest + query)   |
| `GOOGLE_API_KEY`    | yes      | Gemma / Gemini models via AI Studio  |
| `JWT_SECRET_KEY`    | yes      | Sign and verify JWT tokens           |
| `DATABASE_URL`      | yes      | Async psycopg URL (runtime)          |
| `DATABASE_URL_SYNC` | yes      | Sync psycopg URL (Alembic)           |
| `LANGSMITH_API_KEY` | no       | LangSmith tracing (optional)         |

When running via Docker Compose the two `DATABASE_URL` vars are injected automatically — you do not need to change them in `.env`.

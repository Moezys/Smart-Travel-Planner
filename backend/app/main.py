"""FastAPI application entry point.

Lifespan manages the database engine: created once on startup, disposed
cleanly on shutdown.  All other singletons (ML model, embedder, LLM
clients) are lazily initialised with lru_cache inside their own modules.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agent, auth, history
from app.db import dispose_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await dispose_engine()


app = FastAPI(
    title="Smart Travel Planner",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(agent.router, prefix="/api", tags=["agent"])
app.include_router(history.router, prefix="/api", tags=["history"])


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok"}

"""Single source of truth for runtime configuration.

Every environment variable the app reads is declared here, typed, and
validated at startup. If a required key is missing the process refuses to
start — there are no scattered ``os.getenv`` calls anywhere else in the
codebase.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # --- Database ---
    # Async URL used by the FastAPI runtime (driver: psycopg v3, async mode).
    database_url: str = Field(
        default="postgresql+psycopg://stp:stp@localhost:5433/smart_travel_planner",
    )
    # Sync URL used by Alembic. We keep both so migrations don't need an
    # async runner.
    database_url_sync: str = Field(
        default="postgresql+psycopg://stp:stp@localhost:5433/smart_travel_planner",
    )

    # --- Voyage embeddings ---
    voyage_api_key: SecretStr = Field(default=SecretStr(""))
    voyage_model: str = "voyage-4-large"
    voyage_dim: int = 1024
    # Set to False once you've added a payment method on the Voyage
    # dashboard. Leaves throughput unthrottled. The free 200M-token
    # allowance still applies after enabling billing.
    voyage_free_tier: bool = True

    # --- Wikivoyage ingest ---
    # Wikimedia's bot policy (https://w.wiki/4wJS) requires a User-Agent
    # that identifies the project and gives a contact URL or email.
    # Generic UAs (httpx default, "MyApp/0.1 educational") get a 403.
    wikivoyage_user_agent: str = (
        "SmartTravelPlanner/0.1 "
        "(https://github.com/smart-travel-planner/smart-travel-planner; "
        "contact: stp-ingest@example.com)"
    )

    # --- ML classifier ---
    ml_model_path: Path = BACKEND_DIR / "model" / "travel_style_classifier.joblib"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide singleton settings instance.

    Cached so route handlers can take it as a FastAPI dependency without
    re-parsing the environment on every request.
    """
    return Settings()

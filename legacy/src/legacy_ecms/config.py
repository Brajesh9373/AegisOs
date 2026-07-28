from pathlib import Path
from functools import lru_cache
from urllib.parse import urlparse
from typing import Any

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_redis_url(url: str) -> tuple[str, int, str | None]:
    parsed = urlparse(url)
    return parsed.hostname or "localhost", parsed.port or 6379, parsed.password


class Settings(BaseSettings):
    """Runtime settings for the ECMS service.

    Reads ECMS_-prefixed env vars. Accepts ECMS_FALKORDB_URL as a convenience
    (parsed into host/port/password). Falls back to individual fields.
    """

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        env_prefix="ECMS_",
        extra="ignore",
    )

    # ── FalkorDB connection ──────────────────────────────────────────
    falkordb_url: str = Field(
        default="",
        description="Full FalkorDB URL: redis://[password@]host:port",
    )
    falkordb_host: str = "localhost"
    falkordb_port: int = 6379
    falkordb_database: str = "ecms"
    falkordb_password: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _resolve_url(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        url = str(data.get("falkordb_url", "") or "")
        if url:
            host, port, password = _parse_redis_url(url)
            data["falkordb_host"] = host
            data["falkordb_port"] = port
            if password and not data.get("falkordb_password"):
                data["falkordb_password"] = password
        return data

    redis_url: str = "redis://localhost:6380/0"

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    llm_model: str = "gpt-4o-mini"
    categorize_model: str | None = None
    categorize_api_key: str | None = None
    categorize_base_url: str | None = None
    llm_small_model: str | None = None
    embedding_model: str = "text-embedding-3-small"
    embedding_base_url: str | None = None
    embedding_dim: int = 1024
    graphiti_llm_client: str = "openai"
    graphiti_embedder: str = "openai"
    graphiti_response_format: str = "json_object"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_key: str = Field(default="ecms-secret-key", min_length=1)
    auth_enabled: bool = False
    rate_limit_per_minute: int = 60

    git_default_clone_path: str = "./data/repos"
    semantic_mode: str = "keyword"
    semantic_min_confidence: float = 0.70
    min_confidence_accept: float = 0.85
    min_confidence_ingest: float = 0.40
    min_confidence_semantic: float = 0.55
    schema_enforcement: str = "warn"
    structural_max_artifacts_per_file: int = Field(default=500, ge=1, le=10_000)
    structural_json_max_depth: int = Field(default=12, ge=1, le=100)
    structural_json_max_array_items: int = Field(default=50, ge=1, le=10_000)

    # ── Mem0 episodic memory ────────────────────────────────────────
    mem0_enabled: bool = False
    mem0_qdrant_host: str = ""
    mem0_qdrant_port: int = 6333
    mem0_qdrant_api_key: str | None = None
    mem0_qdrant_path: str = "./data/mem0_qdrant"
    mem0_home_path: str = "./data/mem0_home"
    mem0_promotion_threshold: float = 0.70
    mem0_consolidation_turns: int = 10
    mem0_decay_interval_hours: int = 24

    # ── Session backend ──────────────────────────────────────────────
    session_backend: str = "memory"  # "memory" | "redis"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()

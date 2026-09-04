"""Typed application settings and deployment profiles (SECTION 19/78/97)."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["AppSettings", "Profile", "get_settings", "reload_settings"]


def _split_csv(value: str) -> list[str]:
    """Split a comma-separated configuration value into a trimmed, non-empty list."""
    return [item.strip() for item in value.split(",") if item.strip()]


class Profile(StrEnum):
    """Deployment profile (SECTION 19)."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class AppSettings(BaseSettings):
    """Typed application settings loaded from ``ECMS_``-prefixed environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="ECMS_",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = Field(default="ecms", description="Canonical platform name.")
    environment: Profile = Field(
        default=Profile.DEVELOPMENT,
        description="Active deployment profile.",
    )
    debug: bool = Field(default=False, description="Enable verbose debug behaviour.")
    log_level: str = Field(default="INFO", description="Root logging level.")
    rate_limit_per_minute: int = Field(
        default=1000,
        description="Maximum requests per client per minute at the gateway.",
    )
    config_dir: str = Field(
        default="config",
        description="Directory containing layered configuration files.",
    )
    cors_allow_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://localhost:5174",
        description=(
            "Comma-separated list of trusted browser origins allowed to call the API "
            "(the Mission Control frontend). Set explicit origins in production."
        ),
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Whether cross-origin requests may include credentials (cookies/auth).",
    )
    cors_allow_methods: str = Field(
        default="*",
        description="Comma-separated list of HTTP methods permitted for cross-origin requests.",
    )
    cors_allow_headers: str = Field(
        default="*",
        description="Comma-separated list of request headers permitted for cross-origin requests.",
    )
    falkordb_url: str = Field(
        default="redis://localhost:6379",
        description="Redis URL for the FalkorDB graph database.",
    )
    falkordb_graph: str = Field(
        default="ecms",
        description="Graph name within FalkorDB.",
    )
    redis_url: str = Field(
        default="redis://localhost:6380/0",
        description="Redis URL for caches and durable snapshot jobs.",
    )
    s3_endpoint_url: str | None = Field(
        default=None,
        description="S3-compatible endpoint; use null for AWS S3.",
    )
    s3_public_endpoint_url: str | None = Field(
        default=None,
        description="Browser-reachable S3/CDN endpoint used for short-lived signed downloads.",
    )
    s3_region: str = Field(default="us-east-1", description="S3 region.")
    s3_bucket: str = Field(
        default="ecms-knowledge-graph",
        description="Bucket for immutable knowledge-graph snapshots.",
    )
    s3_access_key: str | None = Field(default=None, description="S3 access-key identifier.")
    s3_secret_key: str | None = Field(default=None, description="S3 secret access key.")
    knowledge_graph_renderer: Literal["d3", "cosmos"] = Field(
        default="d3",
        description="Organization knowledge-graph renderer; D3 remains the rollback path.",
    )
    knowledge_graph_cosmos_roles: str = Field(
        default="Super Admin,Administrator,Admin",
        description="Comma-separated roles enabled for a staged Cosmos rollout; use * for all.",
    )
    knowledge_graph_max_client_nodes: int = Field(
        default=100_000,
        ge=1,
        description="Largest node count qualified for an interactive browser snapshot.",
    )
    knowledge_graph_max_client_links: int = Field(
        default=200_000,
        ge=1,
        description="Largest edge count qualified for an interactive browser snapshot.",
    )
    knowledge_graph_build_start_delay_seconds: float = Field(
        default=0,
        ge=0,
        le=30,
        description="Non-production chaos-test delay inserted after a build record is created.",
    )
    connector_ingestion_workspace: str = Field(default="/workspace/connector-ingestions")
    connector_ingestion_enabled: bool = Field(default=True)
    connector_parallel_ingestion_enabled: bool = Field(
        default=False,
        description=(
            "Route newly submitted Git ingestions through the partitioned "
            "coordinator. The single-worker path remains the safe default."
        ),
    )
    connector_extraction_worker_count: int = Field(
        default=4,
        ge=1,
        le=64,
        description=(
            "Extraction lanes used for partition planning. Deploy exactly this many "
            "connector-ingestion-extractor replicas."
        ),
    )
    connector_graph_writer_concurrency: int = Field(
        default=1,
        ge=1,
        le=8,
        description=(
            "Declared graph-writer replica ceiling. The qualified initial topology "
            "supports exactly one globally serialized writer."
        ),
    )
    connector_ingestion_partition_target_files: int = Field(default=100, ge=1, le=10_000)
    connector_ingestion_max_active_partitions_per_org: int = Field(default=8, ge=1, le=256)
    connector_ingestion_max_staged_bytes_per_org: int = Field(
        default=10 * 1024 * 1024 * 1024,
        ge=1,
    )
    connector_ingestion_max_batch_encoded_bytes: int = Field(
        default=4 * 1024 * 1024,
        ge=1024,
        le=64 * 1024 * 1024,
        description="Maximum canonical uncompressed bytes in one staged graph batch.",
    )
    connector_ingestion_staged_retention_days: int = Field(
        default=7,
        ge=1,
        le=365,
        description="Retention after graph commit before staged objects are eligible for cleanup.",
    )
    connector_ingestion_chunk_size: int = Field(default=10, ge=1, le=200)
    connector_ingestion_write_yield_seconds: float = Field(default=0.1, ge=0, le=10)
    connector_ingestion_max_files: int = Field(default=250_000, ge=1)
    connector_ingestion_max_file_bytes: int = Field(default=2 * 1024 * 1024, ge=1)
    connector_ingestion_max_total_bytes: int = Field(default=2 * 1024 * 1024 * 1024, ge=1)
    connector_ingestion_max_deliveries: int = Field(default=3, ge=1, le=20)
    connector_ingestion_stale_after_seconds: int = Field(default=120, ge=30)
    connector_git_clone_depth: int = Field(default=50, ge=1, le=10_000)
    connector_git_clone_timeout_seconds: int = Field(default=600, ge=10)
    connector_git_fetch_timeout_seconds: int = Field(default=300, ge=10)
    connector_ingestion_snapshot_timeout_seconds: int = Field(default=1_800, ge=30)

    # DSH is the shared Agent OS subprocess boundary. Credentials remain in the
    # process environment because DSHRuntime owns the child-env allowlist; these
    # fields deliberately describe only bounded non-secret execution policy.
    #
    # Legacy ECMS_BA_DSH_* variables remain validation aliases during rollout.
    # They must be removed only after deployment configuration has migrated.
    ba_runtime_mode: Literal["dsh", "test"] = Field(
        default="dsh",
        description="Business Analyst execution runtime; production permits DSH only.",
    )
    agent_os_dsh_executable: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "ECMS_AGENT_OS_DSH_EXECUTABLE",
            "ECMS_BA_DSH_EXECUTABLE",
        ),
        description="Optional deployment-pinned DSH executable path; no PATH lookup occurs.",
    )
    agent_os_dsh_home: str = Field(
        default="/var/lib/ecms/dsh",
        validation_alias=AliasChoices(
            "ECMS_AGENT_OS_DSH_HOME",
            "ECMS_BA_DSH_HOME",
        ),
        description="Parent directory for isolated, content-addressed DSH profile homes.",
    )
    agent_os_dsh_timeout_seconds: float = Field(
        default=300,
        gt=0,
        le=1_800,
        validation_alias=AliasChoices(
            "ECMS_AGENT_OS_DSH_TIMEOUT_SECONDS",
            "ECMS_BA_DSH_TIMEOUT_SECONDS",
        ),
    )
    agent_os_dsh_shutdown_grace_seconds: float = Field(
        default=5,
        gt=0,
        le=60,
        validation_alias=AliasChoices(
            "ECMS_AGENT_OS_DSH_SHUTDOWN_GRACE_SECONDS",
            "ECMS_BA_DSH_SHUTDOWN_GRACE_SECONDS",
        ),
    )
    agent_os_dsh_profile_lock_timeout_seconds: float = Field(
        default=30,
        gt=0,
        le=300,
        validation_alias=AliasChoices(
            "ECMS_AGENT_OS_DSH_PROFILE_LOCK_TIMEOUT_SECONDS",
            "ECMS_BA_DSH_PROFILE_LOCK_TIMEOUT_SECONDS",
        ),
    )
    agent_os_dsh_max_task_bytes: int = Field(
        default=96 * 1024,
        ge=1_024,
        le=512 * 1024,
        validation_alias=AliasChoices(
            "ECMS_AGENT_OS_DSH_MAX_TASK_BYTES",
            "ECMS_BA_DSH_MAX_TASK_BYTES",
        ),
    )
    agent_os_dsh_max_command_bytes: int = Field(
        default=112 * 1024,
        ge=1_024,
        le=768 * 1024,
        validation_alias=AliasChoices(
            "ECMS_AGENT_OS_DSH_MAX_COMMAND_BYTES",
            "ECMS_BA_DSH_MAX_COMMAND_BYTES",
        ),
    )
    agent_os_dsh_max_stdout_bytes: int = Field(
        default=1 * 1024 * 1024,
        ge=1_024,
        le=8 * 1024 * 1024,
        validation_alias=AliasChoices(
            "ECMS_AGENT_OS_DSH_MAX_STDOUT_BYTES",
            "ECMS_BA_DSH_MAX_STDOUT_BYTES",
        ),
    )
    agent_os_dsh_max_stderr_bytes: int = Field(
        default=256 * 1024,
        ge=1_024,
        le=2 * 1024 * 1024,
        validation_alias=AliasChoices(
            "ECMS_AGENT_OS_DSH_MAX_STDERR_BYTES",
            "ECMS_BA_DSH_MAX_STDERR_BYTES",
        ),
    )
    ba_prompt_max_source_bytes: int = Field(default=24 * 1024, ge=1_024, le=256 * 1024)
    ba_prompt_max_conversation_bytes: int = Field(default=32 * 1024, ge=1_024, le=256 * 1024)
    ba_prompt_max_evidence_items: int = Field(default=12, ge=1, le=64)
    ba_prompt_max_evidence_bytes: int = Field(default=24 * 1024, ge=1_024, le=256 * 1024)
    ba_prompt_max_graph_nodes: int = Field(default=24, ge=1, le=256)
    ba_prompt_max_graph_edges: int = Field(default=40, ge=1, le=512)
    ba_prompt_max_graph_bytes: int = Field(default=12 * 1024, ge=1_024, le=256 * 1024)
    ba_prompt_max_bytes: int = Field(default=96 * 1024, ge=8 * 1024, le=512 * 1024)
    ba_canonical_projection_required: bool = Field(default=True)
    ba_projection_worker_heartbeat_ttl_seconds: int = Field(default=120, ge=30, le=3_600)

    @model_validator(mode="after")
    def reject_production_chaos_delay(self) -> AppSettings:
        """Prevent the qualification-only build delay from entering production."""
        if (
            self.environment == Profile.PRODUCTION
            and self.knowledge_graph_build_start_delay_seconds > 0
        ):
            raise ValueError("knowledge graph build start delay must be zero in production")
        if (
            self.connector_parallel_ingestion_enabled
            and self.connector_graph_writer_concurrency != 1
        ):
            raise ValueError(
                "parallel connector ingestion currently requires exactly one graph writer"
            )
        if self.agent_os_dsh_max_command_bytes < self.agent_os_dsh_max_task_bytes:
            raise ValueError(
                "agent_os_dsh_max_command_bytes must be at least agent_os_dsh_max_task_bytes"
            )
        if self.ba_prompt_max_bytes < self.ba_prompt_max_source_bytes:
            raise ValueError("ba_prompt_max_bytes must cover ba_prompt_max_source_bytes")
        if self.ba_prompt_max_bytes > self.agent_os_dsh_max_task_bytes:
            raise ValueError("ba_prompt_max_bytes must not exceed agent_os_dsh_max_task_bytes")
        if self.environment == Profile.PRODUCTION:
            if self.ba_runtime_mode != "dsh":
                raise ValueError("production BA execution requires ba_runtime_mode=dsh")
            if not self.ba_canonical_projection_required:
                raise ValueError("production BA execution requires canonical projection")
        return self

    @property
    def cors_origins(self) -> list[str]:
        """Return the trusted CORS origins as a list."""
        return _split_csv(self.cors_allow_origins)

    @property
    def cors_methods(self) -> list[str]:
        """Return the permitted CORS methods as a list."""
        return _split_csv(self.cors_allow_methods)

    @property
    def cors_headers(self) -> list[str]:
        """Return the permitted CORS request headers as a list."""
        return _split_csv(self.cors_allow_headers)

    @property
    def cosmos_roles(self) -> set[str]:
        """Return normalized roles allowed into the staged V2 renderer."""
        return {role.lower() for role in _split_csv(self.knowledge_graph_cosmos_roles)}


@lru_cache
def get_settings() -> AppSettings:
    """Return the cached application settings."""
    return AppSettings()


def reload_settings() -> AppSettings:
    """Clear the settings cache and reload settings from the environment."""
    get_settings.cache_clear()
    return get_settings()

"""Shared enumerations used across ECMS subsystems."""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "AgentRole",
    "AgentStatus",
    "ApprovalStatus",
    "EventCategory",
    "GoalStatus",
    "LifecycleState",
    "MemoryStatus",
    "OntologyCategory",
    "ProcessingStatus",
    "PromotionStatus",
    "RelationshipDirection",
    "RelationshipType",
    "SecurityClassification",
    "SessionStatus",
    "StrategyType",
    "TaskPriority",
    "TaskStatus",
    "ToolExecutionStatus",
    "ValidationStatus",
]


class SecurityClassification(StrEnum):
    """Data-centric security classification of knowledge (SECTION 22/79)."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    HIGHLY_CONFIDENTIAL = "highly_confidential"


class LifecycleState(StrEnum):
    """Lifecycle state of a cognitive object (SECTION 23)."""

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ProcessingStatus(StrEnum):
    """Processing status of a knowledge object (SECTION 22)."""

    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class ValidationStatus(StrEnum):
    """Validation status of a knowledge object (SECTION 22)."""

    VALIDATED = "validated"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class EventCategory(StrEnum):
    """Category of an enterprise event (SECTION 53).

    The nine categories mandated by SECTION 53 (knowledge, memory, runtime, task,
    session, tool, graph, reflection, infrastructure) are extended with the
    cross-cutting categories used by the platform (provider/connector, security,
    plugin, analytics, visualization, administration, system).
    """

    KNOWLEDGE = "knowledge"
    MEMORY = "memory"
    RUNTIME = "runtime"
    TASK = "task"
    SESSION = "session"
    TOOL = "tool"
    GRAPH = "graph"
    REFLECTION = "reflection"
    INFRASTRUCTURE = "infrastructure"
    PROVIDER = "provider"
    VISUALIZATION = "visualization"
    SECURITY = "security"
    ADMINISTRATION = "administration"
    PLUGIN = "plugin"
    ANALYTICS = "analytics"
    SYSTEM = "system"


class RelationshipDirection(StrEnum):
    """Direction of a relationship between cognitive objects (SECTION 30)."""

    DIRECTED = "directed"
    UNDIRECTED = "undirected"
    BIDIRECTIONAL = "bidirectional"


class TaskPriority(StrEnum):
    """Priority of a task (SECTION 24)."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(StrEnum):
    """Lifecycle status of a task (SECTION 24/38)."""

    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionStatus(StrEnum):
    """Lifecycle status of a session (SECTION 25/39)."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class MemoryStatus(StrEnum):
    """Status of a memory workspace (SECTION 26/37)."""

    ACTIVE = "active"
    COMPACTED = "compacted"
    RELEASED = "released"
    DESTROYED = "destroyed"


class AgentRole(StrEnum):
    """Role of a runtime agent (SECTION 22)."""

    PLANNER = "planner"
    BACKEND_ENGINEER = "backend_engineer"
    FRONTEND_ENGINEER = "frontend_engineer"
    DATABASE_ENGINEER = "database_engineer"
    DEVOPS_ENGINEER = "devops_engineer"
    TESTING_ENGINEER = "testing_engineer"
    DOCUMENTATION_ENGINEER = "documentation_engineer"
    REVIEWER = "reviewer"
    REFLECTION_AGENT = "reflection_agent"
    VALIDATION_AGENT = "validation_agent"


class AgentStatus(StrEnum):
    """Lifecycle status of a runtime agent (SECTION 40/60)."""

    CREATED = "created"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    PAUSED = "paused"
    STOPPED = "stopped"
    FAILED = "failed"
    RECOVERED = "recovered"


class ToolExecutionStatus(StrEnum):
    """Status of a single tool invocation (SECTION 46/61)."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    DENIED = "denied"


class GoalStatus(StrEnum):
    """Status of a goal derived from user intent (SECTION 284)."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    FAILED = "failed"
    ABANDONED = "abandoned"


class ApprovalStatus(StrEnum):
    """Approval status of a knowledge candidate (SECTION 44/103)."""

    PENDING = "pending"
    AUTO_APPROVED = "auto_approved"
    APPROVED = "approved"
    REJECTED = "rejected"


class PromotionStatus(StrEnum):
    """Promotion status of a knowledge candidate (SECTION 44/103)."""

    PENDING = "pending"
    PROMOTED = "promoted"
    MERGED = "merged"
    REJECTED = "rejected"


class StrategyType(StrEnum):
    """Execution strategy selected by the Strategy Engine (SECTION 287)."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    DIVIDE_AND_CONQUER = "divide_and_conquer"
    ITERATIVE = "iterative"
    VALIDATION_FIRST = "validation_first"
    TEST_DRIVEN = "test_driven"
    HUMAN_APPROVAL = "human_approval"


class RelationshipType(StrEnum):
    """Canonical semantic relationship types in the graph (SECTION 138).

    The ontology is configurable; these are the canonical defaults and may be
    extended by ontology plugins.
    """

    USES = "uses"
    DEPENDS_ON = "depends_on"
    IMPLEMENTS = "implements"
    CALLS = "calls"
    OWNS = "owns"
    BELONGS_TO = "belongs_to"
    CONTAINS = "contains"
    CONNECTS_TO = "connects_to"
    GENERATES = "generates"
    VALIDATES = "validates"
    DEPLOYS = "deploys"
    TESTS = "tests"
    SECURES = "secures"
    CONFIGURES = "configures"


class OntologyCategory(StrEnum):
    """Top-level enterprise ontology categories (SECTION 141)."""

    BUSINESS = "business"
    TECHNOLOGY = "technology"
    SECURITY = "security"
    INFRASTRUCTURE = "infrastructure"
    ARCHITECTURE = "architecture"
    ORGANIZATION = "organization"
    DOCUMENTATION = "documentation"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"

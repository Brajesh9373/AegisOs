"""Base interface contracts shared across subsystems (Part 5)."""

from ecms.shared.interfaces.base import (
    EventPublisher,
    EventSubscriber,
    HealthProbe,
    Repository,
)
from ecms.shared.interfaces.reasoning import (
    EmbeddingProvider,
    EmbeddingVector,
    ReasoningProvider,
    ReasoningRequest,
    ReasoningResponse,
)

__all__ = [
    "EmbeddingProvider",
    "EmbeddingVector",
    "EventPublisher",
    "EventSubscriber",
    "HealthProbe",
    "ReasoningProvider",
    "ReasoningRequest",
    "ReasoningResponse",
    "Repository",
]

"""GraphQL schema (SECTION 105)."""

from __future__ import annotations

import strawberry

from ecms import __version__

__all__ = ["schema"]


@strawberry.type
class SystemInfo:
    """Platform system information."""

    name: str
    version: str


@strawberry.type
class Query:
    """Root GraphQL query."""

    @strawberry.field
    def version(self) -> str:
        """Return the platform version."""
        return __version__

    @strawberry.field
    def system_info(self) -> SystemInfo:
        """Return platform system information."""
        return SystemInfo(name="Enterprise Cognitive Memory System", version=__version__)


schema = strawberry.Schema(query=Query)

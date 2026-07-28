"""GraphQL router (SECTION 105)."""

from __future__ import annotations

from strawberry.fastapi import GraphQLRouter

from ecms.api.graphql.schema import schema

__all__ = ["create_graphql_router"]


def create_graphql_router() -> GraphQLRouter[None, None]:
    """Create the GraphQL router with the GraphiQL playground enabled."""
    return GraphQLRouter(schema, graphql_ide="graphiql")

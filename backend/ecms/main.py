"""ASGI entry point for the ECMS API gateway."""

from __future__ import annotations

from ecms.api.app import create_app

app = create_app()

__all__ = ["app"]

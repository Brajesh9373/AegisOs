"""Base value object type (SECTION 96).

Value objects are immutable and compared by value. Concrete value objects derive from
:class:`ValueObject`, inheriting frozen semantics and structural equality from Pydantic.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = ["ValueObject"]


class ValueObject(BaseModel):
    """Immutable base for value objects (equality and hashing by value)."""

    model_config = ConfigDict(frozen=True)

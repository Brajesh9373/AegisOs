"""General-purpose utility functions (SECTION 96)."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from itertools import islice

from ecms.shared.exceptions import ValidationError

__all__ = ["chunked", "deep_merge"]


def chunked[T](items: Iterable[T], size: int) -> Iterator[list[T]]:
    """Yield successive lists of at most ``size`` items from ``items``.

    Args:
        items: The iterable to split.
        size: The maximum chunk size; must be positive.

    Yields:
        Lists of at most ``size`` items.

    Raises:
        ValidationError: If ``size`` is not positive.
    """
    if size <= 0:
        raise ValidationError("chunk size must be positive", details={"size": size})
    iterator = iter(items)
    while chunk := list(islice(iterator, size)):
        yield chunk


def deep_merge(base: Mapping[str, object], override: Mapping[str, object]) -> dict[str, object]:
    """Return a recursive merge of two mappings; ``override`` wins on conflicts.

    Args:
        base: The base mapping.
        override: The mapping whose values take precedence.

    Returns:
        A new dictionary containing the merged result.
    """
    result: dict[str, object] = dict(base)
    for key, value in override.items():
        existing = result.get(key)
        if isinstance(existing, Mapping) and isinstance(value, Mapping):
            result[key] = deep_merge(existing, value)
        else:
            result[key] = value
    return result

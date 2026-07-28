"""Dependency-injection container (SECTION 98).

A lightweight, typed container supporting singleton, scoped and transient lifetimes, lazy
resolution and value registrations. Factories receive the container so dependencies can be
composed. Every service, repository, provider, plugin, processor, runtime and gateway is
resolved through this container rather than wired manually.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from typing import Any, TypeVar, cast

from ecms.shared.exceptions import DependencyResolutionError

__all__ = ["Container", "Lifetime", "Scope"]

T = TypeVar("T")


class Lifetime(StrEnum):
    """Lifetime of a registered dependency (SECTION 98)."""

    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


class Container:
    """A typed dependency-injection container (SECTION 98)."""

    def __init__(self) -> None:
        """Initialize an empty container."""
        self._factories: dict[type[Any], tuple[Callable[[Container], Any], Lifetime]] = {}
        self._singletons: dict[type[Any], Any] = {}

    def register(
        self,
        key: type[T],
        factory: Callable[[Container], T],
        *,
        lifetime: Lifetime = Lifetime.TRANSIENT,
    ) -> None:
        """Register a factory for ``key`` with the given lifetime."""
        self._factories[key] = (factory, lifetime)

    def register_value(self, key: type[T], value: T) -> None:
        """Register an existing instance as a singleton value."""
        self._singletons[key] = value
        self._factories[key] = (lambda _container: value, Lifetime.SINGLETON)

    def resolve(self, key: type[T]) -> T:
        """Resolve ``key`` honoring its registered lifetime.

        Raises:
            DependencyResolutionError: If ``key`` is not registered, or is scoped and
                resolved outside a scope.
        """
        return self._resolve(key, scoped=None)

    def create_scope(self) -> Scope:
        """Create a new resolution scope for scoped dependencies."""
        return Scope(self)

    def is_registered(self, key: type[Any]) -> bool:
        """Return whether ``key`` has a registration."""
        return key in self._factories

    def lazy(self, key: type[T]) -> Callable[[], T]:
        """Return a zero-argument callable that resolves ``key`` on first call."""

        def _lazy() -> T:
            return self.resolve(key)

        return _lazy

    def _resolve(self, key: type[T], scoped: dict[type[Any], Any] | None) -> T:
        if key in self._singletons:
            return cast("T", self._singletons[key])
        entry = self._factories.get(key)
        if entry is None:
            raise DependencyResolutionError(f"no registration for {key.__name__}")
        factory, lifetime = entry
        if lifetime is Lifetime.SINGLETON:
            instance = factory(self)
            self._singletons[key] = instance
            return cast("T", instance)
        if lifetime is Lifetime.SCOPED:
            if scoped is None:
                message = f"{key.__name__} is scoped; resolve it within a scope"
                raise DependencyResolutionError(message)
            if key not in scoped:
                scoped[key] = factory(self)
            return cast("T", scoped[key])
        return cast("T", factory(self))


class Scope:
    """A resolution scope that caches scoped instances for its lifetime."""

    def __init__(self, container: Container) -> None:
        """Initialize the scope bound to its parent container."""
        self._container = container
        self._scoped: dict[type[Any], Any] = {}

    def resolve(self, key: type[T]) -> T:
        """Resolve ``key`` within this scope."""
        return self._container._resolve(key, self._scoped)

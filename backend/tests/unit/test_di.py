"""Tests for the dependency-injection container."""

from __future__ import annotations

import pytest

from ecms.infrastructure import Container, Lifetime
from ecms.shared.exceptions import DependencyResolutionError


class _Service:
    def __init__(self) -> None:
        self.value = 42


def test_transient_returns_new_instances() -> None:
    container = Container()
    container.register(_Service, lambda _c: _Service())
    assert container.resolve(_Service) is not container.resolve(_Service)


def test_singleton_returns_same_instance() -> None:
    container = Container()
    container.register(_Service, lambda _c: _Service(), lifetime=Lifetime.SINGLETON)
    assert container.resolve(_Service) is container.resolve(_Service)


def test_register_value() -> None:
    container = Container()
    service = _Service()
    container.register_value(_Service, service)
    assert container.resolve(_Service) is service


def test_unregistered_raises() -> None:
    with pytest.raises(DependencyResolutionError):
        Container().resolve(_Service)


def test_is_registered() -> None:
    container = Container()
    assert not container.is_registered(_Service)
    container.register(_Service, lambda _c: _Service())
    assert container.is_registered(_Service)


def test_scoped_is_same_within_scope_and_new_across_scopes() -> None:
    container = Container()
    container.register(_Service, lambda _c: _Service(), lifetime=Lifetime.SCOPED)
    scope_a = container.create_scope()
    scope_b = container.create_scope()
    assert scope_a.resolve(_Service) is scope_a.resolve(_Service)
    assert scope_a.resolve(_Service) is not scope_b.resolve(_Service)


def test_scoped_without_scope_raises() -> None:
    container = Container()
    container.register(_Service, lambda _c: _Service(), lifetime=Lifetime.SCOPED)
    with pytest.raises(DependencyResolutionError):
        container.resolve(_Service)


def test_lazy_defers_resolution() -> None:
    container = Container()
    container.register(_Service, lambda _c: _Service(), lifetime=Lifetime.SINGLETON)
    lazy = container.lazy(_Service)
    assert lazy() is container.resolve(_Service)


def test_factory_composes_dependencies() -> None:
    class _Repo:
        pass

    class _UseCase:
        def __init__(self, repo: _Repo) -> None:
            self.repo = repo

    container = Container()
    container.register(_Repo, lambda _c: _Repo(), lifetime=Lifetime.SINGLETON)
    container.register(_UseCase, lambda c: _UseCase(c.resolve(_Repo)))
    use_case = container.resolve(_UseCase)
    assert isinstance(use_case.repo, _Repo)
    assert container.resolve(_Repo) is use_case.repo

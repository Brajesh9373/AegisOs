"""Smoke tests verifying the ECMS backend package is importable and well-formed."""

from __future__ import annotations

import ecms


def test_version_is_defined() -> None:
    """The package exposes a non-empty semantic version string."""
    assert isinstance(ecms.__version__, str)
    assert ecms.__version__


def test_package_docstring_present() -> None:
    """The distribution package documents its purpose (SECTION 75)."""
    assert ecms.__doc__

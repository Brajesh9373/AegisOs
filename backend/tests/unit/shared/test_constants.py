"""Tests for ``ecms.shared.constants``."""

from __future__ import annotations

from ecms.shared import constants


def test_platform_name() -> None:
    assert constants.PLATFORM_NAME == "ecms"


def test_page_size_bounds() -> None:
    assert 0 < constants.DEFAULT_PAGE_SIZE <= constants.MAX_PAGE_SIZE

"""Performance benchmarks (SECTION 80/87)."""

from __future__ import annotations

from typing import Any

from ecms.shared.serialization import to_json


def test_to_json_benchmark(benchmark: Any) -> None:
    payload = {"a": 1, "b": [1, 2, 3], "c": {"nested": True}}
    result = benchmark(to_json, payload)
    assert result

from typing import Any


class WorkingMemory:
    """Short-lived per-task memory."""

    def __init__(self) -> None:
        self._values: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._values[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._values.get(key, default)

    def append(self, key: str, value: Any) -> None:
        self._values.setdefault(key, []).append(value)

    def snapshot(self) -> dict[str, Any]:
        return dict(self._values)

    def clear(self) -> None:
        self._values.clear()

"""Dynamic plugin loading (SECTION 103)."""

from __future__ import annotations

import importlib

from ecms.plugins.interfaces.plugin import Plugin
from ecms.shared.exceptions import PluginError

__all__ = ["load_plugin"]


def load_plugin(import_path: str) -> Plugin:
    """Import and instantiate a plugin from a ``module.path:ClassName`` string.

    Args:
        import_path: A ``module:ClassName`` reference to a plugin class.

    Returns:
        A new plugin instance.

    Raises:
        PluginError: If the path is invalid, the module or class cannot be found, or the
            instantiated object is not a plugin.
    """
    module_name, separator, class_name = import_path.partition(":")
    if not separator or not module_name or not class_name:
        raise PluginError(f"invalid plugin path: {import_path!r}")
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        raise PluginError(f"could not import plugin module {module_name!r}: {exc}") from exc
    plugin_class = getattr(module, class_name, None)
    if plugin_class is None:
        raise PluginError(f"plugin class {class_name!r} not found in {module_name!r}")
    instance = plugin_class()
    if not isinstance(instance, Plugin):
        raise PluginError(f"{import_path!r} is not a Plugin")
    return instance

"""Plugin framework module (SECTION 61/103/271/272)."""

from ecms.plugins.domain.manifest import PluginManifest, PluginState
from ecms.plugins.infrastructure.base import BasePlugin
from ecms.plugins.infrastructure.loader import load_plugin
from ecms.plugins.interfaces.plugin import Plugin
from ecms.plugins.services.automation import AutomationEngine, AutomationRule
from ecms.plugins.services.registry import PluginRegistry
from ecms.plugins.services.workflow import Workflow, WorkflowEngine, WorkflowStep

__all__ = [
    "AutomationEngine",
    "AutomationRule",
    "BasePlugin",
    "Plugin",
    "PluginManifest",
    "PluginRegistry",
    "PluginState",
    "Workflow",
    "WorkflowEngine",
    "WorkflowStep",
    "load_plugin",
]

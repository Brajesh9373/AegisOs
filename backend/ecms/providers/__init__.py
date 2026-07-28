"""Connector / provider framework - observes external systems, emits UKOs (SECTION 113)."""

from ecms.providers.domain.connector import DiscoveredObject, SyncResult
from ecms.providers.infrastructure.base import BaseConnector, checksum
from ecms.providers.infrastructure.change_detection import ChangeDetector
from ecms.providers.infrastructure.filesystem_connector import FilesystemConnector
from ecms.providers.interfaces.connector import Connector
from ecms.providers.services.credentials import Credential, CredentialManager
from ecms.providers.services.manager import ConnectorManager
from ecms.providers.services.registry import ConnectorRegistry

__all__ = [
    "BaseConnector",
    "ChangeDetector",
    "Connector",
    "ConnectorManager",
    "ConnectorRegistry",
    "Credential",
    "CredentialManager",
    "DiscoveredObject",
    "FilesystemConnector",
    "SyncResult",
    "checksum",
]

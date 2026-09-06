"""Agent OS runtime package."""

from ecms.agent_os.runtime.agent_factory import (
    AgentFactory,
    AgentInstance,
    LoadedProfile,
    ProfileLoader,
    ScopeEnforcer,
)
from ecms.agent_os.runtime.dsh_sdk_manager import (
    AgentMessage,
    DSHSDKSessionManager,
    PendingRequest,
    SDKAgentSession,
    get_session_manager,
    shutdown_session_manager,
)
from ecms.agent_os.runtime.hierarchy_manager import (
    AgentHierarchyManager,
    get_hierarchy_manager,
)
from ecms.agent_os.runtime.message_router import (
    MessageRouter,
    get_router,
)
from ecms.agent_os.runtime.readiness import AgentOSReadiness, check_readiness
from ecms.agent_os.runtime.scope_middleware import (
    ScopeEnforcementMiddleware,
    ScopedAgentContext,
)

# Global agent factory singleton - shared across all requests
_agent_factory = AgentFactory()

__all__ = [
    "AgentOSReadiness",
    "check_readiness",
    "ProfileLoader",
    "AgentFactory",
    "AgentInstance",
    "ScopeEnforcer",
    "LoadedProfile",
    "ScopeEnforcementMiddleware",
    "ScopedAgentContext",
    # DSH SDK Session Manager
    "AgentMessage",
    "DSHSDKSessionManager",
    "PendingRequest",
    "SDKAgentSession",
    "get_session_manager",
    "shutdown_session_manager",
    # Hierarchy Manager
    "AgentHierarchyManager",
    "get_hierarchy_manager",
    # Message Router
    "MessageRouter",
    "get_router",
    "_agent_factory",
]

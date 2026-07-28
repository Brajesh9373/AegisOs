"""Authentication & authorization security module (SECTION 63/64/100/101)."""

from ecms.auth.domain.authorization import (
    AccessDecision,
    AccessRequest,
    Policy,
    PolicyEffect,
    Role,
)
from ecms.auth.domain.identity import Identity, PrincipalType
from ecms.auth.domain.tokens import TokenClaims, TokenPair, TokenType
from ecms.auth.infrastructure.api_keys import ApiKeyManager
from ecms.auth.infrastructure.bearer import extract_bearer_token
from ecms.auth.infrastructure.jwt_codec import JwtTokenCodec
from ecms.auth.infrastructure.password import BcryptPasswordHasher
from ecms.auth.interfaces.authorization import AuthorizationService
from ecms.auth.interfaces.service import AuthenticationService, PasswordHasher, TokenCodec
from ecms.auth.services.analytics import SecurityAnalytics
from ecms.auth.services.authentication_service import JwtAuthenticationService
from ecms.auth.services.authorization_service import PolicyAuthorizationService
from ecms.auth.services.compliance import ComplianceEngine
from ecms.auth.services.encryption import EncryptionService

__all__ = [
    "AccessDecision",
    "AccessRequest",
    "ApiKeyManager",
    "AuthenticationService",
    "AuthorizationService",
    "BcryptPasswordHasher",
    "ComplianceEngine",
    "EncryptionService",
    "Identity",
    "JwtAuthenticationService",
    "JwtTokenCodec",
    "PasswordHasher",
    "Policy",
    "PolicyAuthorizationService",
    "PolicyEffect",
    "PrincipalType",
    "Role",
    "SecurityAnalytics",
    "TokenClaims",
    "TokenCodec",
    "TokenPair",
    "TokenType",
    "extract_bearer_token",
]

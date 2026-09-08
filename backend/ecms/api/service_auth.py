"""Service-to-service authentication for trusted callers.

The Express BFF fronts browser traffic and forwards project/discovery calls
to ECMS. Browser tokens are BFF-scoped, so the BFF authenticates to ECMS with
a shared service token instead (`x-ecms-service-token` header, value from the
ECMS_SERVICE_TOKEN env var). When the header is absent or mismatched, callers
fall through to normal Bearer auth. An empty/uset ECMS_SERVICE_TOKEN disables
the bypass entirely.
"""

from __future__ import annotations

import os

SERVICE_TOKEN_HEADER = "x-ecms-service-token"


def service_user(headers) -> dict | None:
    """Return the service identity when the request carries a valid token.

    Args:
        headers: Request headers mapping (case-insensitive).

    Returns:
        A synthetic user dict, or None when the bypass does not apply.
    """
    expected = os.environ.get("ECMS_SERVICE_TOKEN", "")
    if not expected:
        return None
    presented = headers.get(SERVICE_TOKEN_HEADER, "")
    if not presented or presented != expected:
        return None
    return {"id": "bff-service", "email": "bff-service@internal", "name": "BFF service"}

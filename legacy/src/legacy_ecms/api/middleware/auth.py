from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from legacy_ecms.config import Settings


class ApiKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings
        self.exempt_paths = {"/", "/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if (
            not self.settings.auth_enabled
            or request.url.path in self.exempt_paths
            or request.url.path.startswith("/assets/")
        ):
            return await call_next(request)
        supplied_key = request.headers.get("x-api-key")
        if supplied_key != self.settings.api_key:
            return JSONResponse({"detail": "Invalid or missing API key"}, status_code=401)
        return await call_next(request)

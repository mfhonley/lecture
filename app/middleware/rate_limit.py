"""
Rate limit по IP: ограничение числа запросов с одного клиента за окно времени.

Лимит задаётся в config: RATE_LIMIT (например, "100/minute").
При превышении — 429 и структурированный ответ ErrorResponse.
"""
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings
from app.schemas.common import ErrorResponse


def _get_client_ip(request: Request) -> str:
    """IP клиента: X-Forwarded-For (первый) или request.client.host."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware: счётчик запросов по IP, при превышении лимита — 429."""

    def __init__(self, app, key_func: Callable[[Request], str] | None = None):
        super().__init__(app)
        self.key_func = key_func or _get_client_ip
        self.max_requests, self.window_seconds = settings.rate_limit_parsed()
        # ip -> (count, window_start)
        self._storage: dict[str, tuple[int, float]] = {}

    async def dispatch(self, request: Request, call_next):
        key = self.key_func(request)
        now = time.monotonic()
        if key in self._storage:
            count, start = self._storage[key]
            if now - start >= self.window_seconds:
                count, start = 0, now
            count += 1
            self._storage[key] = (count, start)
            if count > self.max_requests:
                body = ErrorResponse(
                    error="rate_limit_exceeded",
                    message=f"Too many requests. Limit: {self.max_requests} per {self.window_seconds}s.",
                )
                return JSONResponse(status_code=429, content=body.model_dump())
        else:
            self._storage[key] = (1, now)
        return await call_next(request)

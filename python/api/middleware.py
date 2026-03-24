"""Middleware for the FastAPI application."""

from compression import zstd
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

MINIMUM_RESPONSE_SIZE = 500


class ZstdMiddleware(BaseHTTPMiddleware):
    """Middleware that compresses responses with zstd when the client supports it."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Compress the response with zstd if the client accepts it."""
        accepted_encodings = request.headers.get("accept-encoding", "")
        if "zstd" not in accepted_encodings:
            return await call_next(request)

        response = await call_next(request)

        if response.headers.get("content-encoding") or "text/event-stream" in response.headers.get("content-type", ""):
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk if isinstance(chunk, bytes) else chunk.encode()

        if len(body) < MINIMUM_RESPONSE_SIZE:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        compressed = zstd.compress(body)

        headers = dict(response.headers)
        headers["content-encoding"] = "zstd"
        headers["content-length"] = str(len(compressed))
        headers.pop("transfer-encoding", None)

        return Response(
            content=compressed,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )

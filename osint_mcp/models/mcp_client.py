import logging
from contextlib import AsyncExitStack, asynccontextmanager

import httpx
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client

_logger = logging.getLogger(__name__)


@asynccontextmanager
async def open_mcp_session(server_url, apikey=None):
    """Open an initialized MCP ClientSession.

    Transport heuristic (same as fastmcp): URL ending with /sse -> SSE,
    anything else -> Streamable HTTP.
    """
    headers = {"Authorization": f"Bearer {apikey}"} if apikey else None

    async with AsyncExitStack() as stack:
        if server_url.rstrip("/").endswith("/sse"):
            streams = await stack.enter_async_context(
                sse_client(server_url, headers=headers)
            )
        else:
            http_client = await stack.enter_async_context(
                httpx.AsyncClient(
                    headers=headers,
                    follow_redirects=True,
                    timeout=httpx.Timeout(30.0, read=300.0),
                )
            )
            streams = await stack.enter_async_context(
                streamable_http_client(server_url, http_client=http_client)
            )

        # sse_client -> (read, write), streamable_http_client -> (read, write, ...)
        session = await stack.enter_async_context(
            ClientSession(streams[0], streams[1])
        )
        await session.initialize()
        yield session


def flatten_exception(exc):
    """Return a readable message, unwrapping anyio/asyncio ExceptionGroups."""
    if isinstance(exc, BaseExceptionGroup):
        return "; ".join(flatten_exception(e) for e in exc.exceptions)
    return f"{type(exc).__name__}: {exc}"

"""Thin async wrapper around the pageindex MCP server.

Architectural notes (ARCHITECTURE.md Pattern 3):
- This is the ONLY module that crosses the PageIndex MCP boundary from Python.
- Plan 05's GATE-04 (doc_search), GATE-05 (fetch_node diacritics), and GATE-07
  (3 concurrent doc_search) tests use this client directly — NOT through an
  AIAgent — because per CONTEXT.md and PITFALLS Pitfall 4, asyncio.gather over
  AIAgent instances deadlocks, but asyncio.gather over the MCP client itself is
  safe (the MCP client is async-native via the mcp==1.27.1 SDK).

Phase 2/3 agents access PageIndex through Hermes MCP tool dispatch, NOT through
this client. This client exists for Phase 1 smoke tests + future ingest tooling.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@dataclass
class PageIndexClient:
    """Async client that spawns the `npx -y pageindex-mcp` subprocess and
    dispatches tool calls (doc_search, tree_search, fetch_node) over MCP stdio.

    Usage:
        async with PageIndexClient.connect() as client:
            result = await client.doc_search("konstytucja")
            text = await client.fetch_node(result["node_id"])
    """

    session: ClientSession

    @classmethod
    @asynccontextmanager
    async def connect(
        cls, api_key: str | None = None
    ) -> AsyncIterator["PageIndexClient"]:
        """Spawn pageindex-mcp and return a connected client."""
        key = api_key or os.environ.get("PAGEINDEX_API_KEY")
        if not key or key.startswith("replace-with"):
            raise RuntimeError(
                "PAGEINDEX_API_KEY missing or placeholder — provision via "
                "https://dash.pageindex.ai (Plan 04 Task 1 checkpoint)."
            )

        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "pageindex-mcp"],
            env={"PAGEINDEX_API_KEY": key, **os.environ},
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield cls(session=session)

    async def doc_search(self, query: str) -> dict[str, Any]:
        """Search across all documents; returns a dict with node_id at minimum."""
        result = await self.session.call_tool("doc_search", {"query": query})
        return _unwrap(result)

    async def tree_search(self, query: str, doc_id: str | None = None) -> dict[str, Any]:
        args: dict[str, Any] = {"query": query}
        if doc_id is not None:
            args["doc_id"] = doc_id
        result = await self.session.call_tool("tree_search", args)
        return _unwrap(result)

    async def fetch_node(self, node_id: str) -> dict[str, Any]:
        result = await self.session.call_tool("fetch_node", {"node_id": node_id})
        return _unwrap(result)


def _unwrap(call_result: Any) -> dict[str, Any]:
    """Convert an MCP CallToolResult into a plain dict.

    The MCP SDK returns either `structuredContent` (preferred, post-1.0) or
    `content` (list of TextContent blocks). We try structured first, then parse
    the first text block as JSON.
    """
    import json

    if getattr(call_result, "structuredContent", None):
        return dict(call_result.structuredContent)
    content = getattr(call_result, "content", None) or []
    for block in content:
        text = getattr(block, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"text": text}
    return {"raw": str(call_result)}

"""Thin async wrapper around the pageindex MCP server.

Architectural notes (ARCHITECTURE.md Pattern 3):
- This is the ONLY module that crosses the PageIndex MCP boundary from Python.
- Plan 05's GATE-04 (search_documents), GATE-05 (get_page_content diacritics), and
  GATE-07 (3 concurrent search_documents) tests use this client directly — NOT
  through an AIAgent — because per CONTEXT.md and PITFALLS Pitfall 4, asyncio.gather
  over AIAgent instances deadlocks, but asyncio.gather over the MCP client is safe.

MCP tools exposed by pageindex-mcp (npx -y pageindex-mcp):
  process_document    — upload local/remote PDF, returns doc_id
  browse_documents    — list docs in a folder (no query)
  search_documents    — keyword search across docs
  get_document        — doc status/metadata by doc_id or doc_name
  get_document_structure — hierarchical outline of a document
  get_page_content    — page text for a doc_name + page range
  get_folder_structure   — folder tree
  remove_document     — delete a doc

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
    dispatches tool calls over MCP stdio.

    Usage:
        async with PageIndexClient.connect() as client:
            results = await client.search_documents("konstytucja")
            structure = await client.get_document_structure("konstytucja.pdf")
            content = await client.get_page_content("konstytucja.pdf", pages="1-3")
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
                # list_tools() must be called first — the pageindex-mcp server only
                # loads remote tools into its global registry when ListTools is handled.
                # Calling call_tool() before list_tools() results in "Tool not found".
                await session.list_tools()
                yield cls(session=session)

    async def search_documents(
        self,
        query: str,
        folder_id: str = "root",
    ) -> dict[str, Any]:
        """Keyword search across all documents.

        query should contain keywords only (AND-matched on name/description).
        Returns raw MCP response dict.
        """
        args: dict[str, Any] = {"query": query, "folder_id": folder_id}
        result = await self.session.call_tool("search_documents", args)
        return _unwrap(result)

    async def browse_documents(
        self,
        folder_id: str = "root",
        recursive: bool = False,
    ) -> dict[str, Any]:
        """List documents in a folder without a query."""
        args: dict[str, Any] = {"folder_id": folder_id, "recursive": recursive}
        result = await self.session.call_tool("browse_documents", args)
        return _unwrap(result)

    async def get_document_structure(
        self,
        doc_name: str,
        folder_id: str | None = None,
        part: int = 1,
    ) -> dict[str, Any]:
        """Get hierarchical outline of a document.

        doc_name must match the `name` field verbatim from browse/search response.
        """
        args: dict[str, Any] = {"doc_name": doc_name, "part": part}
        if folder_id is not None:
            args["folder_id"] = folder_id
        result = await self.session.call_tool("get_document_structure", args)
        return _unwrap(result)

    async def get_page_content(
        self,
        doc_name: str,
        pages: str,
        folder_id: str | None = None,
        wait_for_completion: bool = True,
    ) -> dict[str, Any]:
        """Extract page text from a document.

        pages: "5", "3,7,10", "5-10", or "1-3,7,9-12"
        doc_name must match the `name` field verbatim from browse/search response.
        """
        args: dict[str, Any] = {
            "doc_name": doc_name,
            "pages": pages,
            "wait_for_completion": wait_for_completion,
        }
        if folder_id is not None:
            args["folder_id"] = folder_id
        result = await self.session.call_tool("get_page_content", args)
        return _unwrap(result)

    async def get_document(
        self,
        doc_name: str,
        folder_id: str | None = None,
    ) -> dict[str, Any]:
        """Get document status and metadata."""
        args: dict[str, Any] = {"doc_name": doc_name}
        if folder_id is not None:
            args["folder_id"] = folder_id
        result = await self.session.call_tool("get_document", args)
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

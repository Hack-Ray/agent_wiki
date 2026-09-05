from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class McpStdioIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_mcp_remember_search_read_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "brain.db"
            parameters = StdioServerParameters(
                command=sys.executable,
                args=["-m", "brain.mcp.server"],
                cwd=Path(__file__).resolve().parents[1],
                env={**os.environ, "BRAIN_DB_PATH": str(database_path)},
            )
            async with stdio_client(parameters) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    self.assertEqual(
                        {
                            "brain_remember",
                            "brain_search",
                            "brain_read",
                            "brain_update",
                        },
                        {tool.name for tool in tools.tools},
                    )

                    remembered = await session.call_tool(
                        "brain_remember",
                        {
                            "title": "MCP boundary memory",
                            "content": "This complete content crossed the MCP stdio boundary.",
                            "scope": "projects/ai-brain",
                            "tags": ["mcp", "stdio"],
                        },
                    )
                    self.assertFalse(remembered.isError)
                    memory_id = remembered.structuredContent["id"]

                    updated = await session.call_tool(
                        "brain_update",
                        {
                            "id": memory_id,
                            "status": "verified",
                            "verification_basis": "evidence",
                            "verification_evidence": "Confirmed by MCP integration test.",
                        },
                    )
                    self.assertFalse(updated.isError)
                    self.assertEqual("verified", updated.structuredContent["status"])
                    self.assertIsNotNone(updated.structuredContent["verified_at"])

                    searched = await session.call_tool(
                        "brain_search",
                        {"query": "boundary stdio", "status": "verified"},
                    )
                    self.assertFalse(searched.isError)
                    search_results = searched.structuredContent["result"]
                    self.assertEqual(memory_id, search_results[0]["id"])
                    self.assertNotIn("content", search_results[0])

                    read = await session.call_tool("brain_read", {"id": memory_id})
                    self.assertFalse(read.isError)
                    self.assertEqual(
                        "This complete content crossed the MCP stdio boundary.",
                        read.structuredContent["content"],
                    )

            self.assertTrue(database_path.exists())


if __name__ == "__main__":
    unittest.main()

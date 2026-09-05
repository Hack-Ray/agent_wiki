from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from brain.repositories.sqlite import SqliteMemoryRepository
from brain.services.brain import BrainService


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "memory" / "brain.db"
repository = SqliteMemoryRepository(Path(os.environ.get("BRAIN_DB_PATH", DEFAULT_DATABASE_PATH)))
service = BrainService(repository)
mcp = FastMCP("Personal AI Brain")


@mcp.tool()
def brain_remember(
    title: str, content: str, summary: str | None = None,
    type: str = "learning", scope: str = "misc", tags: list[str] | None = None,
    importance: int | None = None, confidence: float | None = None,
) -> dict[str, Any]:
    """Save a durable candidate memory and return its typed identifier."""
    return service.remember(
        title, content, summary, type, scope, tags, importance, confidence
    ).to_dict()


@mcp.tool()
def brain_search(
    query: str, scope: str | None = None, type: str | None = None,
    status: str | None = None, limit: int = 10,
) -> list[dict[str, Any]]:
    """Search memories and return compact summaries, not full content."""
    return [result.to_dict() for result in service.search(query, scope, type, status, limit)]


@mcp.tool()
def brain_read(id: str) -> dict[str, Any]:
    """Read one complete memory using a memory:<id> typed identifier."""
    return service.read(id).to_dict()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

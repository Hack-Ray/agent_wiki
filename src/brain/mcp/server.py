from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from brain.repositories.knowledge import KnowledgeFileRepository
from brain.repositories.knowledge_index import SqliteKnowledgeIndexRepository
from brain.repositories.sqlite import SqliteMemoryRepository
from brain.services.brain import BrainService


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "memory" / "brain.db"
repository = SqliteMemoryRepository(Path(os.environ.get("BRAIN_DB_PATH", DEFAULT_DATABASE_PATH)))
knowledge_repository = KnowledgeFileRepository(
    Path(os.environ.get("BRAIN_KNOWLEDGE_PATH", PROJECT_ROOT / "knowledge"))
)
knowledge_index_repository = SqliteKnowledgeIndexRepository(
    Path(os.environ.get("BRAIN_DB_PATH", DEFAULT_DATABASE_PATH))
)
service = BrainService(repository, knowledge_repository, knowledge_index_repository)
mcp = FastMCP("Personal AI Brain")


@mcp.tool()
def brain_remember(
    title: str, content: str, summary: str | None = None,
    type: str = "learning", scope: str = "misc", tags: list[str] | None = None,
    importance: int | None = None, confidence: float | None = None,
    source_refs: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Save a durable candidate memory and return its typed identifier."""
    return service.remember(
        title, content, summary, type, scope, tags, importance, confidence,
        source_refs,
    ).to_dict()


@mcp.tool()
def brain_search(
    query: str, scope: str | None = None, type: str | None = None,
    status: str | None = None, limit: int = 10,
) -> list[dict[str, Any]]:
    """Search Memory and Knowledge, returning lightweight unified results."""
    return [result.to_dict() for result in service.search(query, scope, type, status, limit)]


@mcp.tool()
def brain_read(id: str) -> dict[str, Any]:
    """Read complete Memory or Knowledge using its typed identifier."""
    return service.read(id).to_dict()


@mcp.tool()
def brain_update(
    id: str,
    title: str | None = None,
    content: str | None = None,
    summary: str | None = None,
    type: str | None = None,
    scope: str | None = None,
    tags: list[str] | None = None,
    importance: int | None = None,
    confidence: float | None = None,
    status: str | None = None,
    verification_basis: str | None = None,
    verification_evidence: str | None = None,
    source_refs: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Update a memory or make a validated lifecycle transition.

    A transition to verified is allowed only for real evidence or explicit user
    confirmation. Set verification_basis to "evidence" or
    "explicit_user_confirmation" and describe that basis in
    verification_evidence. Never verify a hypothesis or inference merely
    because it seems likely.
    """
    return service.update(
        id,
        title=title,
        content=content,
        summary=summary,
        type=type,
        scope=scope,
        tags=tags,
        importance=importance,
        confidence=confidence,
        status=status,
        verification_basis=verification_basis,
        verification_evidence=verification_evidence,
        source_refs=source_refs,
    ).to_dict()


@mcp.tool()
def brain_compile(
    id: str, knowledge_path: str, knowledge_content: str
) -> dict[str, Any]:
    """Persist Agent-consolidated Markdown from a verified Memory.

    knowledge_content must be the complete new UTF-8 Markdown for the target,
    not a fragment to append. The Agent must inspect known existing Knowledge
    and perform all reasoning, organization, and consolidation before calling.
    """
    return service.compile(id, knowledge_path, knowledge_content).to_dict()


@mcp.tool()
def brain_rebuild_index() -> dict[str, Any]:
    """Rebuild the derived Knowledge index from canonical Markdown files."""
    return service.rebuild_index().to_dict()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

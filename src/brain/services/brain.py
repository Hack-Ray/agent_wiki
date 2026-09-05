from __future__ import annotations

from datetime import datetime, timezone

from brain.models import Memory, SearchResult
from brain.repositories.sqlite import SqliteMemoryRepository


class BrainService:
    def __init__(self, repository: SqliteMemoryRepository) -> None:
        self._repository = repository

    def remember(
        self, title: str, content: str, summary: str | None = None,
        type: str = "learning", scope: str = "misc", tags: list[str] | None = None,
        importance: int | None = None, confidence: float | None = None,
    ) -> Memory:
        title = self._required_text(title, "title")
        content = self._required_text(content, "content")
        summary = summary.strip() if summary and summary.strip() else content[:240]
        memory_type = self._required_text(type, "type")
        memory_scope = self._required_text(scope, "scope")
        normalized_tags = self._normalize_tags(tags or [])
        if importance is not None and not 1 <= importance <= 5:
            raise ValueError("importance must be between 1 and 5")
        if confidence is not None and not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        timestamp = datetime.now(timezone.utc).isoformat()
        return self._repository.create(
            title=title, summary=summary, content=content, memory_type=memory_type,
            status="candidate", scope=memory_scope, tags=normalized_tags,
            importance=importance, confidence=confidence, timestamp=timestamp,
        )

    def search(
        self, query: str, scope: str | None = None, type: str | None = None,
        status: str | None = None, limit: int = 10,
    ) -> list[SearchResult]:
        query = self._required_text(query, "query")
        if not 1 <= limit <= 50:
            raise ValueError("limit must be between 1 and 50")
        return self._repository.search(
            query=query, scope=scope, memory_type=type, status=status, limit=limit
        )

    def read(self, identifier: str) -> Memory:
        if not isinstance(identifier, str) or not identifier.startswith("memory:"):
            raise ValueError("id must be a typed identifier with the memory: prefix")
        raw_id = identifier.removeprefix("memory:")
        if not raw_id.isdigit() or int(raw_id) < 1:
            raise ValueError("memory id must be a positive integer")
        memory = self._repository.get(int(raw_id))
        if memory is None:
            raise LookupError(f"Memory not found: {identifier}")
        return memory

    @staticmethod
    def _required_text(value: str, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")
        return value.strip()

    @staticmethod
    def _normalize_tags(tags: list[str]) -> list[str]:
        if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
            raise ValueError("tags must be a list of strings")
        return list(dict.fromkeys(tag.strip() for tag in tags if tag.strip()))


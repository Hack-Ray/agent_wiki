from __future__ import annotations

from datetime import datetime, timezone

from brain.models import Memory, SearchResult
from brain.repositories.sqlite import SqliteMemoryRepository


class BrainService:
    _ALLOWED_TRANSITIONS = {
        "candidate": {"candidate", "verified", "deprecated"},
        "verified": {"verified", "deprecated"},
        "deprecated": {"deprecated"},
    }

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
        memory_id = self._parse_memory_id(identifier)
        memory = self._repository.get(memory_id)
        if memory is None:
            raise LookupError(f"Memory not found: {identifier}")
        return memory

    def update(
        self,
        identifier: str,
        *,
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
    ) -> Memory:
        memory_id = self._parse_memory_id(identifier)
        current = self._repository.get(memory_id)
        if current is None:
            raise LookupError(f"Memory not found: {identifier}")

        target_status = status.strip() if isinstance(status, str) else status
        if target_status is not None:
            if target_status not in self._ALLOWED_TRANSITIONS:
                raise ValueError(
                    "status must be one of: candidate, verified, deprecated"
                )
            if target_status not in self._ALLOWED_TRANSITIONS[current.status]:
                raise ValueError(
                    f"invalid lifecycle transition: {current.status} -> {target_status}"
                )
        else:
            target_status = current.status

        substantive_updates = {
            name
            for name, value in (
                ("title", title), ("content", content), ("summary", summary)
            )
            if value is not None
        }
        if current.status in {"verified", "deprecated"} and substantive_updates:
            raise ValueError(
                f"cannot change verified content fields: "
                f"{', '.join(sorted(substantive_updates))}"
            )

        changes: dict[str, object] = {}
        for name, value in (
            ("title", title), ("content", content), ("summary", summary),
            ("type", type), ("scope", scope),
        ):
            if value is not None:
                changes[name] = self._required_text(value, name)
        if tags is not None:
            changes["tags"] = self._normalize_tags(tags)
        if importance is not None:
            if not 1 <= importance <= 5:
                raise ValueError("importance must be between 1 and 5")
            changes["importance"] = importance
        if confidence is not None:
            if not 0 <= confidence <= 1:
                raise ValueError("confidence must be between 0 and 1")
            changes["confidence"] = confidence

        timestamp = datetime.now(timezone.utc).isoformat()
        if target_status != current.status:
            changes["status"] = target_status
            if target_status == "verified":
                if verification_basis not in {
                    "evidence", "explicit_user_confirmation"
                }:
                    raise ValueError(
                        "verification_basis must be evidence or "
                        "explicit_user_confirmation"
                    )
                evidence = self._required_text(
                    verification_evidence, "verification_evidence"
                )
                changes["verified_at"] = timestamp
                changes["verification_basis"] = verification_basis
                changes["verification_evidence"] = evidence
            elif target_status == "deprecated":
                changes["deprecated_at"] = timestamp
        elif verification_basis is not None or verification_evidence is not None:
            raise ValueError(
                "verification details are only accepted when transitioning to verified"
            )

        if not changes:
            raise ValueError("at least one field must be provided for update")
        changes["updated_at"] = timestamp
        return self._repository.update(
            memory_id, expected_status=current.status, changes=changes
        )

    @staticmethod
    def _parse_memory_id(identifier: str) -> int:
        if not isinstance(identifier, str) or not identifier.startswith("memory:"):
            raise ValueError("id must be a typed identifier with the memory: prefix")
        raw_id = identifier.removeprefix("memory:")
        if not raw_id.isdigit() or int(raw_id) < 1:
            raise ValueError("memory id must be a positive integer")
        return int(raw_id)

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

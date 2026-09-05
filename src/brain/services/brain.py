from __future__ import annotations

from datetime import datetime, timezone
from pathlib import PurePosixPath, PureWindowsPath

from brain.models import Knowledge, Memory, SearchResult
from brain.repositories.knowledge import KnowledgeFileRepository
from brain.repositories.sqlite import SqliteMemoryRepository


class BrainService:
    _ALLOWED_TRANSITIONS = {
        "candidate": {"candidate", "verified", "deprecated"},
        "verified": {"verified", "deprecated"},
        "deprecated": {"deprecated"},
        "compiled": set(),
    }

    def __init__(
        self,
        repository: SqliteMemoryRepository,
        knowledge_repository: KnowledgeFileRepository | None = None,
    ) -> None:
        self._repository = repository
        self._knowledge_repository = knowledge_repository

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

    def read(self, identifier: str) -> Memory | Knowledge:
        if isinstance(identifier, str) and identifier.startswith("memory:"):
            memory_id = self._parse_memory_id(identifier)
            memory = self._repository.get(memory_id)
            if memory is None:
                raise LookupError(f"Memory not found: {identifier}")
            return memory
        if isinstance(identifier, str) and identifier.startswith("knowledge:"):
            path = self._validate_knowledge_path(
                identifier.removeprefix("knowledge:")
            )
            repository = self._require_knowledge_repository()
            return Knowledge(
                id=f"knowledge:{path}", path=path, content=repository.read(path)
            )
        raise ValueError("id must use the memory: or knowledge: prefix")

    def compile(
        self, identifier: str, knowledge_path: str, knowledge_content: str
    ) -> Memory:
        memory_id = self._parse_memory_id(identifier)
        path = self._validate_knowledge_path(knowledge_path)
        if not isinstance(knowledge_content, str) or not knowledge_content.strip():
            raise ValueError("knowledge_content must be a non-empty string")
        content = knowledge_content
        memory = self._repository.get(memory_id)
        if memory is None:
            raise LookupError(f"Memory not found: {identifier}")
        if memory.status != "verified":
            raise ValueError(
                f"only verified Memory can be compiled; current status: {memory.status}"
            )
        if memory.knowledge_path is not None and memory.knowledge_path != path:
            raise ValueError("Memory already references a different knowledge_path")

        knowledge_repository = self._require_knowledge_repository()
        previous_content = knowledge_repository.read_optional(path)
        knowledge_repository.write_atomic(path, content)
        timestamp = datetime.now(timezone.utc).isoformat()
        try:
            return self._repository.update(
                memory_id,
                expected_status="verified",
                changes={
                    "status": "compiled",
                    "knowledge_path": path,
                    "updated_at": timestamp,
                },
            )
        except Exception as update_error:
            try:
                if previous_content is None:
                    knowledge_repository.delete(path)
                else:
                    knowledge_repository.write_atomic(path, previous_content)
            except Exception as recovery_error:
                raise RuntimeError(
                    "SQLite compile update failed and Knowledge recovery failed for "
                    f"{path}; filesystem state requires manual inspection"
                ) from ExceptionGroup(
                    "compile and recovery failures", [update_error, recovery_error]
                )
            raise RuntimeError(
                f"SQLite compile update failed; Knowledge was restored for {path}"
            ) from update_error

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
        if current.status in {"verified", "compiled", "deprecated"} and substantive_updates:
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
    def _validate_knowledge_path(value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("knowledge_path must be a non-empty string")
        value = value.strip()
        if "\\" in value or "\0" in value or ":" in value:
            raise ValueError("knowledge_path contains forbidden characters")
        windows_path = PureWindowsPath(value)
        parts = value.split("/")
        if windows_path.is_absolute() or windows_path.drive or windows_path.root:
            raise ValueError("knowledge_path must be relative")
        if any(part in {"", ".", ".."} for part in parts):
            raise ValueError("knowledge_path contains invalid path segments")
        path = PurePosixPath(value)
        if not value.endswith(".md"):
            raise ValueError("knowledge_path must end with .md")
        return path.as_posix()

    def _require_knowledge_repository(self) -> KnowledgeFileRepository:
        if self._knowledge_repository is None:
            raise RuntimeError("Knowledge repository is not configured")
        return self._knowledge_repository

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

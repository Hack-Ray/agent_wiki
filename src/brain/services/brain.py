from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import PurePosixPath, PureWindowsPath

from brain.models import (
    Knowledge,
    KnowledgeIndexEntry,
    Memory,
    RebuildResult,
    SearchResult,
    SourceDocument,
    SourceIndexEntry,
    SourceRebuildResult,
    SourceSearchResult,
)
from brain.repositories.knowledge import KnowledgeFileRepository
from brain.repositories.knowledge_index import SqliteKnowledgeIndexRepository
from brain.repositories.sqlite import SqliteMemoryRepository
from brain.repositories.source import SourceFileRepository
from brain.repositories.source_index import SqliteSourceIndexRepository


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
        knowledge_index_repository: SqliteKnowledgeIndexRepository | None = None,
        source_repository: SourceFileRepository | None = None,
        source_index_repository: SqliteSourceIndexRepository | None = None,
    ) -> None:
        self._repository = repository
        self._knowledge_repository = knowledge_repository
        self._knowledge_index_repository = knowledge_index_repository
        self._source_repository = source_repository
        self._source_index_repository = source_index_repository

    def remember(
        self, title: str, content: str, summary: str | None = None,
        type: str = "learning", scope: str = "misc", tags: list[str] | None = None,
        importance: int | None = None, confidence: float | None = None,
        source_refs: list[dict[str, str]] | None = None,
    ) -> Memory:
        title = self._required_text(title, "title")
        content = self._required_text(content, "content")
        summary = summary.strip() if summary and summary.strip() else content[:240]
        memory_type = self._required_text(type, "type")
        memory_scope = self._required_text(scope, "scope")
        normalized_tags = self._normalize_tags(tags or [])
        normalized_source_refs = self._normalize_source_refs(
            source_refs if source_refs is not None else []
        )
        if importance is not None and not 1 <= importance <= 5:
            raise ValueError("importance must be between 1 and 5")
        if confidence is not None and not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        timestamp = datetime.now(timezone.utc).isoformat()
        return self._repository.create(
            title=title, summary=summary, content=content, memory_type=memory_type,
            status="candidate", scope=memory_scope, tags=normalized_tags,
            source_refs=normalized_source_refs,
            importance=importance, confidence=confidence, timestamp=timestamp,
        )

    def search(
        self, query: str, scope: str | None = None, type: str | None = None,
        status: str | None = None, limit: int = 10,
    ) -> list[SearchResult]:
        query = self._required_text(query, "query")
        if not 1 <= limit <= 50:
            raise ValueError("limit must be between 1 and 50")
        candidate_limit = 50
        memory_statuses = [status] if status is not None else [
            "verified", "candidate", "compiled"
        ]
        memory_results = [
            result
            for memory_status in memory_statuses
            for result in self._repository.search(
                query=query,
                scope=scope,
                memory_type=type,
                status=memory_status,
                limit=candidate_limit,
            )
        ]
        knowledge_results: list[SearchResult] = []
        if type is None and status is None and self._knowledge_index_repository:
            knowledge_results = self._knowledge_index_repository.search(
                query=query, scope=scope, limit=candidate_limit
            )
            knowledge_repository = self._require_knowledge_repository()
            knowledge_results = [
                result
                for result in knowledge_results
                if result.knowledge_path is not None
                and knowledge_repository.read_optional(result.knowledge_path) is not None
            ]

        matched_knowledge_paths = {
            result.knowledge_path for result in knowledge_results
        }
        memory_results = [
            result
            for result in memory_results
            if not (
                result.status == "compiled"
                and result.knowledge_path in matched_knowledge_paths
            )
        ]
        priority = {
            ("knowledge", None): 0,
            ("memory", "verified"): 1,
            ("memory", "candidate"): 2,
            ("memory", "compiled"): 3,
            ("memory", "deprecated"): 4,
        }
        merged = sorted(
            [*knowledge_results, *memory_results],
            key=lambda result: (
                priority.get((result.kind, result.status), 5),
                result.score,
                result.id,
            ),
        )
        return merged[:limit]

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
            compiled = self._repository.update(
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

        if self._knowledge_index_repository is not None:
            try:
                self._knowledge_index_repository.upsert(
                    self._extract_knowledge_metadata(path, content)
                )
            except Exception as index_error:
                raise RuntimeError(
                    "Compile succeeded but Knowledge index update failed; "
                    "run brain_rebuild_index"
                ) from index_error
        return compiled

    def rebuild_index(self) -> RebuildResult:
        knowledge_repository = self._require_knowledge_repository()
        index_repository = self._require_knowledge_index_repository()
        entries = [
            self._extract_knowledge_metadata(path, knowledge_repository.read(path))
            for path in knowledge_repository.list_markdown_paths()
        ]
        index_repository.replace_all(entries)
        return RebuildResult(knowledge_indexed=len(entries))

    def search_sources(
        self, query: str, path: str | None = None, limit: int = 10
    ) -> list[SourceSearchResult]:
        query = self._required_text(query, "query")
        if not 1 <= limit <= 50:
            raise ValueError("limit must be between 1 and 50")
        subtree = (
            self._validate_source_path(path, require_supported=False)
            if path is not None
            else None
        )
        index_repository = self._require_source_index_repository()
        source_repository = self._require_source_repository()
        readable_results: list[SourceSearchResult] = []
        offset = 0
        batch_size = 50
        while len(readable_results) < limit:
            results = index_repository.search(
                query=query, path=subtree, limit=batch_size, offset=offset
            )
            if not results:
                break
            offset += len(results)
            for result in results:
                try:
                    safe_path = self._validate_source_path(
                        result.path, require_supported=True
                    )
                    source_repository.read(safe_path)
                except UnicodeError:
                    raise
                except (LookupError, ValueError):
                    continue
                readable_results.append(result)
                if len(readable_results) == limit:
                    break
            if len(results) < batch_size:
                break
        return readable_results

    def read_source(self, identifier: str) -> SourceDocument:
        path = self._parse_source_id(identifier)
        content = self._require_source_repository().read(path)
        return SourceDocument(
            id=f"source:{path}", kind="source", path=path, content=content
        )

    def rebuild_source_index(self) -> SourceRebuildResult:
        source_repository = self._require_source_repository()
        entries: list[SourceIndexEntry] = []
        for listed_path in source_repository.list_supported_paths():
            try:
                path = self._validate_source_path(
                    listed_path, require_supported=True
                )
                content = source_repository.read(path)
            except Exception as error:
                raise RuntimeError(
                    f"Failed to index Source source:{listed_path}: {error}"
                ) from error
            entries.append(
                SourceIndexEntry(
                    path=path, name=PurePosixPath(path).name, content=content
                )
            )
        self._require_source_index_repository().replace_all(entries)
        return SourceRebuildResult(sources_indexed=len(entries))

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
        source_refs: list[dict[str, str]] | None = None,
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
        if source_refs is not None:
            changes["source_refs"] = self._normalize_source_refs(source_refs)
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

    @classmethod
    def _parse_source_id(cls, identifier: str) -> str:
        if not isinstance(identifier, str) or not identifier.startswith("source:"):
            raise ValueError("id must be a typed identifier with the source: prefix")
        return cls._validate_source_path(
            identifier.removeprefix("source:"), require_supported=True
        )

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

    @staticmethod
    def _validate_source_path(value: str, *, require_supported: bool) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("source path must be a non-empty string")
        value = value.strip()
        if "\\" in value or "\0" in value or ":" in value:
            raise ValueError("source path contains forbidden characters")
        windows_path = PureWindowsPath(value)
        parts = value.split("/")
        if windows_path.is_absolute() or windows_path.drive or windows_path.root:
            raise ValueError("source path must be relative")
        if any(part in {"", ".", ".."} for part in parts):
            raise ValueError("source path contains invalid path segments")
        path = PurePosixPath(value)
        if (
            require_supported
            and path.suffix.lower() not in SourceFileRepository.SUPPORTED_EXTENSIONS
        ):
            raise ValueError("source path uses an unsupported extension")
        return path.as_posix()

    def _require_knowledge_repository(self) -> KnowledgeFileRepository:
        if self._knowledge_repository is None:
            raise RuntimeError("Knowledge repository is not configured")
        return self._knowledge_repository

    def _require_knowledge_index_repository(self) -> SqliteKnowledgeIndexRepository:
        if self._knowledge_index_repository is None:
            raise RuntimeError("Knowledge index repository is not configured")
        return self._knowledge_index_repository

    def _require_source_repository(self) -> SourceFileRepository:
        if self._source_repository is None:
            raise RuntimeError("Source repository is not configured")
        return self._source_repository

    def _require_source_index_repository(self) -> SqliteSourceIndexRepository:
        if self._source_index_repository is None:
            raise RuntimeError("Source index repository is not configured")
        return self._source_index_repository

    @classmethod
    def _extract_knowledge_metadata(
        cls, path: str, content: str
    ) -> KnowledgeIndexEntry:
        lines = content.splitlines()
        title = next(
            (
                match.group(1).strip().rstrip("#").strip()
                for line in lines
                if (match := re.match(r"^#\s+(.+)$", line.strip()))
            ),
            PurePosixPath(path).stem,
        )
        summary = ""
        for index, line in enumerate(lines):
            if re.match(r"^##\s+Summary\s*#*\s*$", line.strip(), re.IGNORECASE):
                summary = cls._first_markdown_paragraph(lines[index + 1 :], True)
                break
        if not summary:
            summary = cls._first_markdown_paragraph(lines, False)
        if not summary:
            summary = title
        parts = PurePosixPath(path).parts
        scope = parts[0] if len(parts) > 1 else "misc"
        return KnowledgeIndexEntry(
            path=path, title=title, summary=summary, scope=scope, content=content
        )

    @staticmethod
    def _first_markdown_paragraph(lines: list[str], stop_at_heading: bool) -> str:
        paragraph: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                if stop_at_heading:
                    break
                continue
            if not stripped:
                if paragraph:
                    break
                continue
            paragraph.append(stripped)
        return " ".join(paragraph)

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

    @staticmethod
    def _normalize_source_refs(
        source_refs: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        if not isinstance(source_refs, list):
            raise ValueError("source_refs must be a list of structured objects")
        allowed_types = {"local_file_path", "url", "log_or_source_path"}
        normalized: list[dict[str, str]] = []
        for reference in source_refs:
            if not isinstance(reference, dict):
                raise ValueError("each source_ref must be a structured object")
            if set(reference) != {"type", "value"}:
                raise ValueError("each source_ref must contain only type and value")
            reference_type = reference["type"]
            value = reference["value"]
            if not isinstance(reference_type, str) or reference_type not in allowed_types:
                raise ValueError(
                    "source_ref type must be local_file_path, url, or "
                    "log_or_source_path"
                )
            if not isinstance(value, str) or not value.strip():
                raise ValueError("source_ref value must be a non-empty string")
            normalized.append({"type": reference_type, "value": value})
        return normalized

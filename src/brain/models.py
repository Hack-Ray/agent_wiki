from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Memory:
    id: str
    title: str
    summary: str
    content: str
    type: str
    status: str
    scope: str
    tags: list[str]
    importance: int | None
    confidence: float | None
    created_at: str
    updated_at: str
    verified_at: str | None
    deprecated_at: str | None
    verification_basis: str | None
    verification_evidence: str | None
    knowledge_path: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SearchResult:
    id: str
    kind: str
    title: str
    summary: str
    type: str | None
    status: str | None
    scope: str
    score: float
    knowledge_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result.pop("knowledge_path")
        return result


@dataclass(frozen=True)
class Knowledge:
    id: str
    path: str
    content: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KnowledgeIndexEntry:
    path: str
    title: str
    summary: str
    scope: str
    content: str


@dataclass(frozen=True)
class RebuildResult:
    knowledge_indexed: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

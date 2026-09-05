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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SearchResult:
    id: str
    title: str
    summary: str
    type: str
    status: str
    scope: str
    score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


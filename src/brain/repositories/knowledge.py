from __future__ import annotations

import os
import tempfile
from pathlib import Path


class KnowledgeFileRepository:
    def __init__(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        self._root = root.resolve()

    def read(self, logical_path: str) -> str:
        target = self._target(logical_path)
        try:
            return target.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise LookupError(f"Knowledge not found: knowledge:{logical_path}") from None

    def read_optional(self, logical_path: str) -> str | None:
        try:
            return self.read(logical_path)
        except LookupError:
            return None

    def write_atomic(self, logical_path: str, content: str) -> None:
        target = self._target(logical_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            descriptor, name = tempfile.mkstemp(
                dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
            )
            temporary_path = Path(name)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, target)
            temporary_path = None
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def delete(self, logical_path: str) -> None:
        self._target(logical_path).unlink(missing_ok=True)

    def _target(self, logical_path: str) -> Path:
        target = (self._root / Path(*logical_path.split("/"))).resolve(strict=False)
        try:
            target.relative_to(self._root)
        except ValueError:
            raise ValueError("knowledge path escapes knowledge root") from None
        return target

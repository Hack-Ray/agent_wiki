from __future__ import annotations

from pathlib import Path


class SourceFileRepository:
    SUPPORTED_EXTENSIONS = {".md", ".txt", ".log", ".json", ".csv"}

    def __init__(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        self._root = root.resolve()

    def list_supported_paths(self) -> list[str]:
        return sorted(
            path.relative_to(self._root).as_posix()
            for path in self._root.rglob("*")
            if path.suffix.lower() in self.SUPPORTED_EXTENSIONS
            and (path.is_symlink() or path.is_file())
        )

    def read(self, logical_path: str) -> str:
        target = self._target(logical_path)
        if target.exists() and not target.is_file():
            raise ValueError(f"Source path must reference a file: source:{logical_path}")
        try:
            return target.read_text(encoding="utf-8-sig")
        except FileNotFoundError:
            raise LookupError(f"Source not found: source:{logical_path}") from None
        except UnicodeDecodeError as error:
            raise UnicodeError(
                f"Source is not valid UTF-8: source:{logical_path}"
            ) from error

    def _target(self, logical_path: str) -> Path:
        target = (self._root / Path(*logical_path.split("/"))).resolve(strict=False)
        try:
            target.relative_to(self._root)
        except ValueError:
            raise ValueError("source path escapes Source root") from None
        return target

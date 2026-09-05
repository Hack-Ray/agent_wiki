from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from brain.models import SourceIndexEntry, SourceSearchResult


class SqliteSourceIndexRepository:
    def __init__(self, database_path: Path) -> None:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(database_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA busy_timeout=5000")
        try:
            self._initialize_schema()
        except Exception:
            self._connection.close()
            raise

    def _initialize_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS source_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS source_fts USING fts5(
                path UNINDEXED, name, content
            );
            """
        )

    def close(self) -> None:
        self._connection.close()

    def search(
        self, *, query: str, path: str | None, limit: int, offset: int = 0
    ) -> list[SourceSearchResult]:
        clauses = ["source_fts MATCH ?"]
        parameters: list[object] = [self._to_match_query(query)]
        if path is not None:
            clauses.append(
                "(si.path = ? OR substr(si.path, 1, length(?) + 1) = ? || '/')"
            )
            parameters.extend((path, path, path))
        parameters.extend((limit, offset))
        rows = self._connection.execute(
            f"""
            SELECT si.path, si.name,
                   snippet(source_fts, 2, '[', ']', ' … ', 16) AS snippet
            FROM source_fts
            JOIN source_index AS si ON si.id = source_fts.rowid
            WHERE {' AND '.join(clauses)}
            ORDER BY bm25(source_fts), si.path
            LIMIT ? OFFSET ?
            """,
            parameters,
        ).fetchall()
        return [
            SourceSearchResult(
                id=f"source:{row['path']}", kind="source", path=row["path"],
                name=row["name"], snippet=row["snippet"],
            )
            for row in rows
        ]

    def replace_all(self, entries: list[SourceIndexEntry]) -> None:
        self._initialize_schema()
        with self._connection:
            self._connection.execute("DELETE FROM source_fts")
            self._connection.execute("DELETE FROM source_index")
            for entry in entries:
                cursor = self._connection.execute(
                    "INSERT INTO source_index (path, name) VALUES (?, ?)",
                    (entry.path, entry.name),
                )
                self._insert_fts(cursor.lastrowid, entry)

    def clear(self) -> None:
        self.replace_all([])

    def _insert_fts(self, row_id: int, entry: SourceIndexEntry) -> None:
        self._connection.execute(
            """
            INSERT INTO source_fts (rowid, path, name, content)
            VALUES (?, ?, ?, ?)
            """,
            (row_id, entry.path, entry.name, entry.content),
        )

    @staticmethod
    def _to_match_query(query: str) -> str:
        terms = re.findall(r"[^\W_]+", query, flags=re.UNICODE)
        if not terms:
            raise ValueError("query must contain at least one searchable term")
        return " AND ".join(f'"{term}"' for term in terms)

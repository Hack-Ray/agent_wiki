from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from brain.models import KnowledgeIndexEntry, SearchResult


class SqliteKnowledgeIndexRepository:
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
            CREATE TABLE IF NOT EXISTS knowledge_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                scope TEXT NOT NULL
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                path UNINDEXED, title, summary, content, scope
            );
            """
        )

    def close(self) -> None:
        self._connection.close()

    def search(self, *, query: str, scope: str | None, limit: int) -> list[SearchResult]:
        clauses = ["knowledge_fts MATCH ?"]
        parameters: list[object] = [self._to_match_query(query)]
        if scope is not None:
            clauses.append("ki.scope = ?")
            parameters.append(scope)
        parameters.append(limit)
        rows = self._connection.execute(
            f"""
            SELECT ki.path, ki.title, ki.summary, ki.scope,
                   bm25(knowledge_fts) AS score
            FROM knowledge_fts
            JOIN knowledge_index AS ki ON ki.id = knowledge_fts.rowid
            WHERE {' AND '.join(clauses)}
            ORDER BY score, ki.path
            LIMIT ?
            """,
            parameters,
        ).fetchall()
        return [
            SearchResult(
                id=f"knowledge:{row['path']}", kind="knowledge",
                title=row["title"], summary=row["summary"], type=None,
                status=None, scope=row["scope"], score=row["score"],
                knowledge_path=row["path"],
            )
            for row in rows
        ]

    def upsert(self, entry: KnowledgeIndexEntry) -> None:
        with self._connection:
            row = self._connection.execute(
                "SELECT id FROM knowledge_index WHERE path = ?", (entry.path,)
            ).fetchone()
            if row is None:
                cursor = self._connection.execute(
                    """
                    INSERT INTO knowledge_index (path, title, summary, scope)
                    VALUES (?, ?, ?, ?)
                    """,
                    (entry.path, entry.title, entry.summary, entry.scope),
                )
                row_id = cursor.lastrowid
            else:
                row_id = row["id"]
                self._connection.execute(
                    """
                    UPDATE knowledge_index
                    SET title = ?, summary = ?, scope = ?
                    WHERE id = ?
                    """,
                    (entry.title, entry.summary, entry.scope, row_id),
                )
                self._connection.execute(
                    "DELETE FROM knowledge_fts WHERE rowid = ?", (row_id,)
                )
            self._insert_fts(row_id, entry)

    def replace_all(self, entries: list[KnowledgeIndexEntry]) -> None:
        self._initialize_schema()
        with self._connection:
            self._connection.execute("DELETE FROM knowledge_fts")
            self._connection.execute("DELETE FROM knowledge_index")
            for entry in entries:
                cursor = self._connection.execute(
                    """
                    INSERT INTO knowledge_index (path, title, summary, scope)
                    VALUES (?, ?, ?, ?)
                    """,
                    (entry.path, entry.title, entry.summary, entry.scope),
                )
                self._insert_fts(cursor.lastrowid, entry)

    def clear(self) -> None:
        self.replace_all([])

    def _insert_fts(self, row_id: int, entry: KnowledgeIndexEntry) -> None:
        self._connection.execute(
            """
            INSERT INTO knowledge_fts (rowid, path, title, summary, content, scope)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (row_id, entry.path, entry.title, entry.summary, entry.content, entry.scope),
        )

    @staticmethod
    def _to_match_query(query: str) -> str:
        terms = re.findall(r"[^\W_]+", query, flags=re.UNICODE)
        if not terms:
            raise ValueError("query must contain at least one searchable term")
        return " AND ".join(f'"{term}"' for term in terms)

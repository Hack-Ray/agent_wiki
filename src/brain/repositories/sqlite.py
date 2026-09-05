from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from brain.models import Memory, SearchResult


class SqliteMemoryRepository:
    _UPDATABLE_COLUMNS = {
        "title", "summary", "content", "type", "status", "scope", "tags",
        "importance", "confidence", "updated_at", "verified_at",
        "deprecated_at", "verification_basis", "verification_evidence",
    }

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
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
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                content TEXT NOT NULL,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                scope TEXT NOT NULL,
                tags TEXT NOT NULL,
                importance INTEGER,
                confidence REAL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                verified_at TEXT,
                deprecated_at TEXT,
                verification_basis TEXT,
                verification_evidence TEXT
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                title, summary, content, tags,
                content='memories', content_rowid='id'
            );

            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, title, summary, content, tags)
                VALUES (new.id, new.title, new.summary, new.content, new.tags);
            END;

            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, title, summary, content, tags)
                VALUES ('delete', old.id, old.title, old.summary, old.content, old.tags);
                INSERT INTO memories_fts(rowid, title, summary, content, tags)
                VALUES (new.id, new.title, new.summary, new.content, new.tags);
            END;
            """
        )
        self._connection.execute("BEGIN")
        try:
            self._add_column_if_missing("verified_at", "TEXT")
            self._add_column_if_missing("deprecated_at", "TEXT")
            self._add_column_if_missing("verification_basis", "TEXT")
            self._add_column_if_missing("verification_evidence", "TEXT")
        except Exception:
            self._connection.rollback()
            raise
        else:
            self._connection.commit()

    def _add_column_if_missing(self, name: str, definition: str) -> None:
        columns = {
            row["name"] for row in self._connection.execute("PRAGMA table_info(memories)")
        }
        if name not in columns:
            self._connection.execute(
                f"ALTER TABLE memories ADD COLUMN {name} {definition}"
            )

    def close(self) -> None:
        self._connection.close()

    def create(
        self,
        *,
        title: str,
        summary: str,
        content: str,
        memory_type: str,
        status: str,
        scope: str,
        tags: list[str],
        importance: int | None,
        confidence: float | None,
        timestamp: str,
    ) -> Memory:
        tags_json = json.dumps(tags, ensure_ascii=False)
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO memories (
                    title, summary, content, type, status, scope, tags,
                    importance, confidence, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, summary, content, memory_type, status, scope, tags_json,
                 importance, confidence, timestamp, timestamp),
            )
        memory = self.get(cursor.lastrowid)
        if memory is None:
            raise RuntimeError("Memory insert succeeded but could not be read back")
        return memory

    def get(self, memory_id: int) -> Memory | None:
        row = self._connection.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()
        return self._to_memory(row) if row else None

    def update(
        self,
        memory_id: int,
        *,
        expected_status: str,
        changes: dict[str, object],
    ) -> Memory:
        if not changes:
            raise ValueError("changes must not be empty")
        unsupported_columns = changes.keys() - self._UPDATABLE_COLUMNS
        if unsupported_columns:
            raise ValueError(
                f"unsupported update columns: {', '.join(sorted(unsupported_columns))}"
            )
        stored_changes = dict(changes)
        if "tags" in stored_changes:
            stored_changes["tags"] = json.dumps(
                stored_changes["tags"], ensure_ascii=False
            )
        assignments = ", ".join(f"{column} = ?" for column in stored_changes)
        parameters = [*stored_changes.values(), memory_id, expected_status]
        with self._connection:
            cursor = self._connection.execute(
                f"UPDATE memories SET {assignments} WHERE id = ? AND status = ?",
                parameters,
            )
        if cursor.rowcount != 1:
            raise RuntimeError("Memory changed concurrently or no longer exists")
        memory = self.get(memory_id)
        if memory is None:
            raise RuntimeError("Memory update succeeded but could not be read back")
        return memory

    def search(
        self,
        *,
        query: str,
        scope: str | None,
        memory_type: str | None,
        status: str | None,
        limit: int,
    ) -> list[SearchResult]:
        clauses = ["memories_fts MATCH ?"]
        parameters: list[object] = [self._to_match_query(query)]
        for column, value in (("scope", scope), ("type", memory_type), ("status", status)):
            if value is not None:
                clauses.append(f"m.{column} = ?")
                parameters.append(value)
        parameters.append(limit)
        rows = self._connection.execute(
            f"""
            SELECT m.id, m.title, m.summary, m.type, m.status, m.scope,
                   bm25(memories_fts) AS score
            FROM memories_fts
            JOIN memories AS m ON m.id = memories_fts.rowid
            WHERE {' AND '.join(clauses)}
            ORDER BY score, m.id
            LIMIT ?
            """,
            parameters,
        ).fetchall()
        return [SearchResult(
            id=f"memory:{row['id']}", title=row["title"], summary=row["summary"],
            type=row["type"], status=row["status"], scope=row["scope"],
            score=row["score"],
        ) for row in rows]

    @staticmethod
    def _to_match_query(query: str) -> str:
        terms = re.findall(r"[^\W_]+", query, flags=re.UNICODE)
        if not terms:
            raise ValueError("query must contain at least one searchable term")
        return " AND ".join(f'"{term}"' for term in terms)

    @staticmethod
    def _to_memory(row: sqlite3.Row) -> Memory:
        return Memory(
            id=f"memory:{row['id']}", title=row["title"], summary=row["summary"],
            content=row["content"], type=row["type"], status=row["status"],
            scope=row["scope"], tags=json.loads(row["tags"]),
            importance=row["importance"], confidence=row["confidence"],
            created_at=row["created_at"], updated_at=row["updated_at"],
            verified_at=row["verified_at"], deprecated_at=row["deprecated_at"],
            verification_basis=row["verification_basis"],
            verification_evidence=row["verification_evidence"],
        )

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from brain.repositories.knowledge import KnowledgeFileRepository
from brain.repositories.sqlite import SqliteMemoryRepository
from brain.services.brain import BrainService


class FailingCompileRepository(SqliteMemoryRepository):
    fail_compile = False

    def update(self, memory_id: int, *, expected_status: str, changes: dict[str, object]):
        if self.fail_compile and changes.get("status") == "compiled":
            raise RuntimeError("injected SQLite failure")
        return super().update(
            memory_id, expected_status=expected_status, changes=changes
        )


class KnowledgeCompileIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.database_path = self.root / "brain.db"
        self.knowledge_root = self.root / "knowledge"
        self.repository = SqliteMemoryRepository(self.database_path)
        self.knowledge_repository = KnowledgeFileRepository(self.knowledge_root)
        self.service = BrainService(self.repository, self.knowledge_repository)

    def tearDown(self) -> None:
        self.repository.close()
        self.temporary_directory.cleanup()

    def _remember(self):
        return self.service.remember(
            "Knowledge lifecycle", "Complete source memory.", scope="brain"
        )

    def _verify(self, identifier: str):
        return self.service.update(
            identifier,
            status="verified",
            verification_basis="evidence",
            verification_evidence="Reviewed source and test evidence.",
        )

    def test_verified_memory_compiles_and_persists_across_connections(self) -> None:
        candidate = self._remember()
        verified = self._verify(candidate.id)
        markdown = "\n# 知識層\n\n保留完整 UTF-8 內容。\n"

        compiled = self.service.compile(
            candidate.id, "architecture/knowledge-layer.md", markdown
        )

        self.assertEqual("compiled", compiled.status)
        self.assertEqual("architecture/knowledge-layer.md", compiled.knowledge_path)
        self.assertEqual(verified.verified_at, compiled.verified_at)
        self.assertEqual(verified.verification_basis, compiled.verification_basis)
        self.assertEqual(verified.verification_evidence, compiled.verification_evidence)
        self.assertEqual(markdown, (self.knowledge_root / compiled.knowledge_path).read_text(encoding="utf-8"))
        self.assertEqual(compiled, self.service.read(candidate.id))
        self.assertEqual(
            [candidate.id],
            [result.id for result in self.service.search("Knowledge", status="compiled")],
        )
        knowledge = self.service.read("knowledge:architecture/knowledge-layer.md")
        self.assertEqual("knowledge:architecture/knowledge-layer.md", knowledge.id)
        self.assertEqual(markdown, knowledge.content)

        self.repository.close()
        self.repository = SqliteMemoryRepository(self.database_path)
        self.service = BrainService(self.repository, KnowledgeFileRepository(self.knowledge_root))
        persisted = self.service.read(candidate.id)
        self.assertEqual("compiled", persisted.status)
        self.assertEqual("architecture/knowledge-layer.md", persisted.knowledge_path)
        self.assertEqual(verified.verified_at, persisted.verified_at)
        self.assertEqual(markdown, self.service.read("knowledge:architecture/knowledge-layer.md").content)

    def test_compile_replaces_existing_document_instead_of_appending(self) -> None:
        memory = self._remember()
        self._verify(memory.id)
        self.knowledge_repository.write_atomic("topic.md", "# Old\n\nstale\n")
        replacement = "# New\n\ncomplete replacement\n"

        self.service.compile(memory.id, "topic.md", replacement)

        self.assertEqual(replacement, self.knowledge_repository.read("topic.md"))
        self.assertNotIn("stale", self.knowledge_repository.read("topic.md"))

    def test_only_verified_memory_can_compile(self) -> None:
        candidate = self._remember()
        with self.assertRaisesRegex(ValueError, "only verified"):
            self.service.compile(candidate.id, "candidate.md", "# Candidate\n")
        deprecated = self.service.update(candidate.id, status="deprecated")
        with self.assertRaisesRegex(ValueError, "only verified"):
            self.service.compile(deprecated.id, "deprecated.md", "# Deprecated\n")
        self.assertFalse(any(self.knowledge_root.rglob("*.md")))

    def test_compiled_memory_cannot_be_compiled_again(self) -> None:
        memory = self._remember()
        self._verify(memory.id)
        self.service.compile(memory.id, "once.md", "# Once\n")
        with self.assertRaisesRegex(ValueError, "only verified"):
            self.service.compile(memory.id, "once.md", "# Twice\n")
        with self.assertRaisesRegex(ValueError, "cannot change verified content"):
            self.service.update(memory.id, content="Changed after compilation")

    def test_compile_validates_typed_memory_identifier_and_safe_markdown_path(self) -> None:
        memory = self._remember()
        self._verify(memory.id)
        invalid_paths = (
            "/absolute.md", "C:/absolute.md", "../escape.md", "folder/../escape.md",
            "folder\\escape.md", "folder//escape.md", "folder/./escape.md",
            "not-markdown.txt", "knowledge:other.md",
        )
        with self.assertRaises(ValueError):
            self.service.compile("knowledge:any.md", "safe.md", "# Safe\n")
        for invalid_path in invalid_paths:
            with self.subTest(path=invalid_path), self.assertRaises(ValueError):
                self.service.compile(memory.id, invalid_path, "# Unsafe\n")
        self.assertFalse((self.root / "escape.md").exists())
        self.assertEqual("verified", self.service.read(memory.id).status)

    def test_atomic_file_failure_leaves_memory_verified_and_no_partial_file(self) -> None:
        memory = self._remember()
        verified = self._verify(memory.id)
        with patch("brain.repositories.knowledge.os.replace", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                self.service.compile(memory.id, "failed.md", "# Never partial\n")

        current = self.service.read(memory.id)
        self.assertEqual("verified", current.status)
        self.assertEqual(verified.verified_at, current.verified_at)
        self.assertFalse((self.knowledge_root / "failed.md").exists())
        self.assertEqual([], list(self.knowledge_root.glob("*.tmp")))

    def test_sqlite_failure_restores_previous_knowledge(self) -> None:
        self.repository.close()
        self.repository = FailingCompileRepository(self.database_path)
        self.service = BrainService(self.repository, self.knowledge_repository)
        memory = self._remember()
        verified = self._verify(memory.id)
        self.knowledge_repository.write_atomic("existing.md", "# Previous\n")
        self.repository.fail_compile = True

        with self.assertRaisesRegex(RuntimeError, "Knowledge was restored"):
            self.service.compile(memory.id, "existing.md", "# Replacement\n")

        self.assertEqual("# Previous\n", self.knowledge_repository.read("existing.md"))
        current = self.service.read(memory.id)
        self.assertEqual("verified", current.status)
        self.assertEqual(verified.verification_evidence, current.verification_evidence)

    def test_sqlite_failure_removes_new_knowledge(self) -> None:
        self.repository.close()
        self.repository = FailingCompileRepository(self.database_path)
        self.service = BrainService(self.repository, self.knowledge_repository)
        memory = self._remember()
        self._verify(memory.id)
        self.repository.fail_compile = True

        with self.assertRaisesRegex(RuntimeError, "Knowledge was restored"):
            self.service.compile(memory.id, "new.md", "# New\n")

        self.assertFalse((self.knowledge_root / "new.md").exists())
        self.assertEqual("verified", self.service.read(memory.id).status)

    def test_read_rejects_invalid_or_missing_knowledge_identifier(self) -> None:
        for identifier in ("knowledge:../escape.md", "knowledge:not-md.txt"):
            with self.subTest(identifier=identifier), self.assertRaises(ValueError):
                self.service.read(identifier)
        with self.assertRaises(LookupError):
            self.service.read("knowledge:missing.md")


class KnowledgeMigrationTests(unittest.TestCase):
    def test_milestone_3_database_migrates_without_changing_existing_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "brain.db"
            connection = sqlite3.connect(database_path)
            connection.execute(
                """
                CREATE TABLE memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL, summary TEXT NOT NULL, content TEXT NOT NULL,
                    type TEXT NOT NULL, status TEXT NOT NULL, scope TEXT NOT NULL,
                    tags TEXT NOT NULL, importance INTEGER, confidence REAL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    verified_at TEXT, deprecated_at TEXT,
                    verification_basis TEXT, verification_evidence TEXT
                )
                """
            )
            connection.execute(
                """
                INSERT INTO memories (
                    title, summary, content, type, status, scope, tags,
                    created_at, updated_at, verified_at,
                    verification_basis, verification_evidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "Existing", "Existing summary", "Existing content", "learning",
                    "verified", "migration", "[]", "created", "updated", "verified",
                    "evidence", "Existing evidence",
                ),
            )
            connection.commit()
            connection.close()

            repository = SqliteMemoryRepository(database_path)
            memory = repository.get(1)
            columns = {
                row["name"]
                for row in repository._connection.execute("PRAGMA table_info(memories)")
            }
            self.assertIn("knowledge_path", columns)
            self.assertEqual("verified", memory.status)
            self.assertEqual("Existing evidence", memory.verification_evidence)
            self.assertIsNone(memory.knowledge_path)
            repository.close()


if __name__ == "__main__":
    unittest.main()

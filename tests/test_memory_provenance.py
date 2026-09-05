from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from brain.repositories.knowledge import KnowledgeFileRepository
from brain.repositories.sqlite import SqliteMemoryRepository
from brain.services.brain import BrainService


SOURCE_REFS = [
    {"type": "local_file_path", "value": r"D:\project\service.py"},
    {"type": "url", "value": "https://example.com/evidence"},
    {"type": "log_or_source_path", "value": "sources/logs/failure.log"},
]


class MemoryProvenanceIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.database_path = self.root / "brain.db"
        self.repository = SqliteMemoryRepository(self.database_path)
        self.service = BrainService(
            self.repository, KnowledgeFileRepository(self.root / "knowledge")
        )

    def tearDown(self) -> None:
        self.repository.close()
        self.temporary_directory.cleanup()

    def test_remember_read_reconnect_verify_and_compile_preserve_source_refs(self) -> None:
        memory = self.service.remember(
            "Traceable conclusion", "Complete conclusion", source_refs=SOURCE_REFS
        )
        self.assertEqual(SOURCE_REFS, memory.source_refs)
        self.assertEqual(SOURCE_REFS, self.service.read(memory.id).source_refs)

        self.repository.close()
        self.repository = SqliteMemoryRepository(self.database_path)
        self.service = BrainService(
            self.repository, KnowledgeFileRepository(self.root / "knowledge")
        )
        reconnected = self.service.read(memory.id)
        self.assertEqual(SOURCE_REFS, reconnected.source_refs)

        verified = self.service.update(
            memory.id,
            status="verified",
            verification_basis="evidence",
            verification_evidence="Evidence was independently reviewed.",
        )
        self.assertEqual(SOURCE_REFS, verified.source_refs)
        compiled = self.service.compile(
            memory.id, "provenance.md", "# Provenance\n\nComplete Knowledge.\n"
        )
        self.assertEqual(SOURCE_REFS, compiled.source_refs)
        self.assertEqual("evidence", compiled.verification_basis)
        self.assertEqual(
            "Evidence was independently reviewed.",
            compiled.verification_evidence,
        )
        self.assertEqual(verified.verified_at, compiled.verified_at)

    def test_update_replaces_source_refs_and_empty_list_clears_them(self) -> None:
        without_refs = self.service.remember("No provenance", "Uses default")
        self.assertEqual([], without_refs.source_refs)
        memory = self.service.remember(
            "Replace provenance", "Candidate content", source_refs=SOURCE_REFS
        )
        replacement = [{"type": "url", "value": "https://example.com/new"}]

        updated = self.service.update(memory.id, source_refs=replacement)
        self.assertEqual(replacement, updated.source_refs)
        cleared = self.service.update(memory.id, source_refs=[])
        self.assertEqual([], cleared.source_refs)

    def test_candidate_and_verified_deprecation_preserve_source_refs(self) -> None:
        candidate = self.service.remember(
            "Candidate deprecation", "Candidate", source_refs=SOURCE_REFS
        )
        candidate_deprecated = self.service.update(
            candidate.id, status="deprecated"
        )
        self.assertEqual(SOURCE_REFS, candidate_deprecated.source_refs)

        verified_memory = self.service.remember(
            "Verified deprecation", "Verified", source_refs=SOURCE_REFS
        )
        verified = self.service.update(
            verified_memory.id,
            status="verified",
            verification_basis="explicit_user_confirmation",
            verification_evidence="User explicitly confirmed this Memory.",
        )
        deprecated = self.service.update(verified.id, status="deprecated")
        self.assertEqual(SOURCE_REFS, deprecated.source_refs)
        self.assertEqual(verified.verified_at, deprecated.verified_at)
        self.assertEqual(verified.verification_basis, deprecated.verification_basis)
        self.assertEqual(
            verified.verification_evidence, deprecated.verification_evidence
        )

    def test_source_refs_validation_rejects_invalid_shapes(self) -> None:
        invalid_values = (
            "sources/logs/raw.log",
            ["sources/logs/raw.log"],
            [{"type": "unknown", "value": "somewhere"}],
            [{"type": ["url"], "value": "somewhere"}],
            [{"type": "url", "value": ""}],
            [{"type": "url", "value": "   "}],
            [{"type": "url"}],
            [{"type": "url", "value": "https://example.com", "extra": "no"}],
        )
        for source_refs in invalid_values:
            with self.subTest(source_refs=source_refs), self.assertRaises(ValueError):
                self.service.remember(
                    "Invalid provenance", "Must be rejected", source_refs=source_refs
                )

    def test_source_refs_do_not_change_verification_policy(self) -> None:
        memory = self.service.remember(
            "Still candidate", "A reference is not verification", source_refs=SOURCE_REFS
        )
        self.assertEqual("candidate", memory.status)
        with self.assertRaises(ValueError):
            self.service.update(memory.id, status="verified")


class MemoryProvenanceMigrationTests(unittest.TestCase):
    @staticmethod
    def _create_pre_provenance_database(database_path: Path) -> None:
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
                verification_basis TEXT, verification_evidence TEXT,
                knowledge_path TEXT
            )
            """
        )
        connection.execute(
            """
            INSERT INTO memories (
                title, summary, content, type, status, scope, tags,
                created_at, updated_at, verified_at,
                verification_basis, verification_evidence, knowledge_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Existing M5 Memory", "Existing summary", "Existing content",
                "learning", "verified", "migration", "[]", "created", "updated",
                "verified", "evidence", "Existing verification", None,
            ),
        )
        connection.commit()
        connection.close()

    def test_existing_memory_migrates_to_empty_source_refs_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "brain.db"
            self._create_pre_provenance_database(database_path)

            repository = SqliteMemoryRepository(database_path)
            memory = repository.get(1)
            self.assertEqual([], memory.source_refs)
            self.assertEqual("verified", memory.status)
            self.assertEqual("Existing verification", memory.verification_evidence)
            repository.close()

            reopened = SqliteMemoryRepository(database_path)
            columns = [
                row["name"]
                for row in reopened._connection.execute("PRAGMA table_info(memories)")
            ]
            self.assertEqual(1, columns.count("source_refs"))
            self.assertEqual([], reopened.get(1).source_refs)
            reopened.close()

    def test_source_refs_migration_failure_rolls_back_added_column(self) -> None:
        class FailingSourceRefsMigrationRepository(SqliteMemoryRepository):
            def _add_column_if_missing(self, name: str, definition: str) -> None:
                super()._add_column_if_missing(name, definition)
                if name == "source_refs":
                    raise RuntimeError("injected source_refs migration failure")

        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "brain.db"
            self._create_pre_provenance_database(database_path)

            with self.assertRaisesRegex(
                RuntimeError, "injected source_refs migration failure"
            ):
                FailingSourceRefsMigrationRepository(database_path)

            connection = sqlite3.connect(database_path)
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(memories)")
            }
            row = connection.execute(
                "SELECT status, verification_evidence FROM memories WHERE id = 1"
            ).fetchone()
            connection.close()
            self.assertNotIn("source_refs", columns)
            self.assertEqual(("verified", "Existing verification"), row)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from brain.repositories.sqlite import SqliteMemoryRepository
from brain.services.brain import BrainService


class MemoryLifecycleIntegrationTests(unittest.TestCase):
    def test_candidate_verify_deprecate_persists_and_filters(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "brain.db"
            repository = SqliteMemoryRepository(database_path)
            service = BrainService(repository)
            memory = service.remember(
                "Lifecycle persistence", "Evidence-backed lifecycle content"
            )
            self.assertEqual("candidate", memory.status)
            self.assertIsNone(memory.verified_at)
            self.assertIsNone(memory.deprecated_at)

            with self.assertRaises(ValueError):
                service.update(memory.id, status="verified")
            with self.assertRaises(ValueError):
                service.update(
                    memory.id,
                    status="verified",
                    verification_basis="self_asserted",
                    verification_evidence="This is still only a hypothesis.",
                )
            self.assertEqual("candidate", service.read(memory.id).status)

            verified = service.update(
                memory.id,
                status="verified",
                verification_basis="explicit_user_confirmation",
                verification_evidence="User explicitly confirmed the result.",
            )
            self.assertEqual("verified", verified.status)
            self.assertIsNotNone(verified.verified_at)
            self.assertIsNone(verified.deprecated_at)
            self.assertEqual(
                "User explicitly confirmed the result.",
                verified.verification_evidence,
            )
            self.assertEqual(
                "explicit_user_confirmation", verified.verification_basis
            )
            with self.assertRaises(ValueError):
                service.update(verified.id, content="Unverified replacement content")
            self.assertIsNotNone(datetime.fromisoformat(verified.verified_at))
            repository.close()

            reopened_repository = SqliteMemoryRepository(database_path)
            reopened_service = BrainService(reopened_repository)
            persisted = reopened_service.read(memory.id)
            self.assertEqual(verified, persisted)
            self.assertEqual(
                [memory.id],
                [
                    result.id
                    for result in reopened_service.search(
                        "Lifecycle persistence", status="verified"
                    )
                ],
            )

            deprecated = reopened_service.update(memory.id, status="deprecated")
            self.assertEqual("deprecated", deprecated.status)
            self.assertEqual(verified.verified_at, deprecated.verified_at)
            self.assertIsNotNone(deprecated.deprecated_at)
            self.assertIsNotNone(datetime.fromisoformat(deprecated.deprecated_at))
            with self.assertRaises(ValueError):
                reopened_service.update(
                    memory.id,
                    status="verified",
                    verification_basis="evidence",
                    verification_evidence="Attempted rollback.",
                )
            reopened_repository.close()

            final_repository = SqliteMemoryRepository(database_path)
            final_memory = BrainService(final_repository).read(memory.id)
            self.assertEqual(deprecated, final_memory)
            final_repository.close()

    def test_candidate_can_be_deprecated_and_compiled_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = SqliteMemoryRepository(Path(temporary_directory) / "brain.db")
            service = BrainService(repository)
            memory = service.remember("Obsolete candidate", "No longer relevant")
            with self.assertRaises(ValueError):
                service.update(memory.id, status="compiled")
            deprecated = service.update(memory.id, status="deprecated")
            self.assertEqual("deprecated", deprecated.status)
            self.assertIsNotNone(deprecated.deprecated_at)
            repository.close()

    def test_content_update_refreshes_fts_and_preserves_typed_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = SqliteMemoryRepository(Path(temporary_directory) / "brain.db")
            service = BrainService(repository)
            memory = service.remember("Original phrase", "Original content")
            updated = service.update(
                memory.id,
                title="Replacement phrase",
                content="Replacement searchable content",
                summary="Replacement summary",
                tags=["replacement-tag"],
            )
            self.assertEqual(memory.id, updated.id)
            self.assertEqual([], service.search("Original"))
            self.assertEqual(
                [memory.id],
                [result.id for result in service.search("Replacement searchable")],
            )
            repository.close()

    def test_existing_milestone_one_schema_is_migrated_in_place(self) -> None:
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
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                )
                """
            )
            timestamp = "2026-09-05T00:00:00+00:00"
            connection.execute(
                """
                INSERT INTO memories (
                    title, summary, content, type, status, scope, tags,
                    importance, confidence, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "Existing M1 memory", "Existing summary", "Existing content",
                    "learning", "candidate", "misc", json.dumps(["existing"]),
                    None, None, timestamp, timestamp,
                ),
            )
            connection.commit()
            connection.close()

            repository = SqliteMemoryRepository(database_path)
            columns = {
                row["name"]
                for row in repository._connection.execute("PRAGMA table_info(memories)")
            }
            self.assertTrue(
                {
                    "verified_at", "deprecated_at", "verification_basis",
                    "verification_evidence",
                }
                <= columns
            )
            memory = BrainService(repository).read("memory:1")
            self.assertEqual("candidate", memory.status)
            self.assertIsNone(memory.verified_at)
            self.assertIsNone(memory.deprecated_at)
            repository.close()

            reopened_repository = SqliteMemoryRepository(database_path)
            persisted_columns = {
                row["name"]
                for row in reopened_repository._connection.execute(
                    "PRAGMA table_info(memories)"
                )
            }
            self.assertTrue(
                {
                    "verified_at", "deprecated_at", "verification_basis",
                    "verification_evidence",
                }
                <= persisted_columns
            )
            self.assertEqual(
                "Existing M1 memory",
                BrainService(reopened_repository).read("memory:1").title,
            )
            reopened_repository.close()

    def test_migration_failure_rolls_back_all_new_columns(self) -> None:
        class FailingMigrationRepository(SqliteMemoryRepository):
            migration_calls = 0

            def _add_column_if_missing(self, name: str, definition: str) -> None:
                self.migration_calls += 1
                if self.migration_calls == 2:
                    raise RuntimeError("injected migration failure")
                super()._add_column_if_missing(name, definition)

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
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                )
                """
            )
            connection.commit()
            connection.close()

            with self.assertRaisesRegex(RuntimeError, "injected migration failure"):
                FailingMigrationRepository(database_path)

            connection = sqlite3.connect(database_path)
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(memories)")
            }
            connection.close()
            self.assertNotIn("verified_at", columns)
            self.assertNotIn("deprecated_at", columns)
            self.assertNotIn("verification_basis", columns)
            self.assertNotIn("verification_evidence", columns)


if __name__ == "__main__":
    unittest.main()

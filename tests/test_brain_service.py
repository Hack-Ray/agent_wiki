from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from brain.repositories.sqlite import SqliteMemoryRepository
from brain.services.brain import BrainService


class BrainServiceIntegrationTests(unittest.TestCase):
    def test_repository_enables_wal_and_busy_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = SqliteMemoryRepository(Path(temporary_directory) / "brain.db")
            journal_mode = repository._connection.execute(
                "PRAGMA journal_mode"
            ).fetchone()[0]
            busy_timeout = repository._connection.execute(
                "PRAGMA busy_timeout"
            ).fetchone()[0]
            self.assertEqual("wal", journal_mode)
            self.assertEqual(5000, busy_timeout)
            repository.close()

    def test_remember_search_read_persists_across_connections(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "brain.db"
            repository = SqliteMemoryRepository(database_path)
            service = BrainService(repository)
            remembered = service.remember(
                title="SQL Server SELECT Deadlock",
                content="SELECT can participate in a deadlock when incompatible locks form a cycle.",
                summary="SELECT statements can be deadlock participants.",
                type="debugging", scope="database",
                tags=["sql-server", "deadlock"], importance=5, confidence=0.9,
            )
            self.assertEqual("candidate", remembered.status)
            repository.close()

            reopened_repository = SqliteMemoryRepository(database_path)
            reopened_service = BrainService(reopened_repository)
            results = reopened_service.search("SELECT deadlock")
            self.assertEqual([remembered.id], [result.id for result in results])
            self.assertFalse(hasattr(results[0], "content"))
            self.assertEqual(remembered, reopened_service.read(results[0].id))
            reopened_repository.close()

    def test_read_rejects_untyped_and_unknown_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = SqliteMemoryRepository(Path(temporary_directory) / "brain.db")
            service = BrainService(repository)
            for identifier in ("1", "unknown:1", "memory:nope"):
                with self.subTest(identifier=identifier), self.assertRaises(ValueError):
                    service.read(identifier)
            with self.assertRaises(LookupError):
                service.read("memory:999")
            repository.close()

    def test_search_filters_and_validates_bounds(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = SqliteMemoryRepository(Path(temporary_directory) / "brain.db")
            service = BrainService(repository)
            service.remember("Shared term", "alpha", type="learning", scope="cs")
            service.remember("Shared term", "beta", type="incident", scope="work")
            self.assertEqual(1, len(service.search("shared", scope="cs")))
            self.assertEqual(1, len(service.search("shared", type="incident")))
            self.assertEqual(2, len(service.search("shared", status="candidate")))
            with self.assertRaises(ValueError):
                service.search("shared", limit=0)
            repository.close()


if __name__ == "__main__":
    unittest.main()

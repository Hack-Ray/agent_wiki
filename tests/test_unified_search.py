from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from brain.repositories.knowledge import KnowledgeFileRepository
from brain.repositories.knowledge_index import SqliteKnowledgeIndexRepository
from brain.repositories.sqlite import SqliteMemoryRepository
from brain.services.brain import BrainService


class UnifiedSearchIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.database_path = self.root / "brain.db"
        self.knowledge_root = self.root / "knowledge"
        self.memory_repository = SqliteMemoryRepository(self.database_path)
        self.knowledge_repository = KnowledgeFileRepository(self.knowledge_root)
        self.index_repository = SqliteKnowledgeIndexRepository(self.database_path)
        self.service = BrainService(
            self.memory_repository,
            self.knowledge_repository,
            self.index_repository,
        )

    def tearDown(self) -> None:
        self.index_repository.close()
        self.memory_repository.close()
        self.temporary_directory.cleanup()

    def _verify(self, identifier: str):
        return self.service.update(
            identifier,
            status="verified",
            verification_basis="evidence",
            verification_evidence="Verified by deterministic integration test.",
        )

    def test_markdown_metadata_is_deterministic_and_results_are_lightweight(self) -> None:
        with_summary = (
            "# SQL Server Deadlocks\n\n"
            "## Summary\n\n"
            "Cycle detection and victim selection.\n"
            "This remains the same paragraph.\n\n"
            "## Knowledge\n\nFull deadlock material sentinel.\n"
        )
        fallback = (
            "# Fallback Knowledge\n\n"
            "## Context\n\n"
            "Fallback paragraph carries fallbackmarker.\n\n"
            "More material.\n"
        )
        self.knowledge_repository.write_atomic("database/deadlocks.md", with_summary)
        self.knowledge_repository.write_atomic("projects/fallback.md", fallback)
        result = self.service.rebuild_index()
        self.assertEqual(2, result.knowledge_indexed)

        deadlock = self.service.search("victim selection")[0]
        self.assertEqual("knowledge:database/deadlocks.md", deadlock.id)
        self.assertEqual("knowledge", deadlock.kind)
        self.assertEqual("SQL Server Deadlocks", deadlock.title)
        self.assertEqual(
            "Cycle detection and victim selection. This remains the same paragraph.",
            deadlock.summary,
        )
        self.assertEqual("database", deadlock.scope)
        self.assertIsNone(deadlock.status)
        self.assertIsNone(deadlock.type)
        self.assertNotIn("content", deadlock.to_dict())
        self.assertNotIn("knowledge_path", deadlock.to_dict())
        self.assertEqual(
            with_summary,
            self.service.read("knowledge:database/deadlocks.md").content,
        )

        fallback_result = self.service.search("fallbackmarker")[0]
        self.assertEqual(
            "Fallback paragraph carries fallbackmarker.", fallback_result.summary
        )
        self.assertEqual("projects", fallback_result.scope)

    def test_unified_priority_suppression_and_final_limit(self) -> None:
        candidate = self.service.remember(
            "Priority candidate", "prioritymarker candidate", scope="database"
        )
        verified = self.service.remember(
            "Priority verified", "prioritymarker verified", scope="database"
        )
        self._verify(verified.id)
        compiled = self.service.remember(
            "Priority compiled", "prioritymarker compiled", scope="database"
        )
        self._verify(compiled.id)
        self.service.compile(
            compiled.id,
            "database/canonical.md",
            "# Canonical Priority\n\n## Summary\n\nprioritymarker canonical.\n",
        )
        self.knowledge_repository.write_atomic(
            "database/second.md",
            "# Second Canonical\n\n## Summary\n\nprioritymarker second.\n",
        )
        self.service.rebuild_index()

        results = self.service.search("prioritymarker", limit=10)
        self.assertEqual(
            ["knowledge", "knowledge", "memory", "memory"],
            [result.kind for result in results],
        )
        self.assertEqual(
            ["verified", "candidate"],
            [result.status for result in results if result.kind == "memory"],
        )
        self.assertNotIn(compiled.id, [result.id for result in results])
        self.assertIn(verified.id, [result.id for result in results])
        self.assertIn(candidate.id, [result.id for result in results])

        limited = self.service.search("prioritymarker", limit=2)
        self.assertEqual(2, len(limited))
        self.assertEqual(["knowledge", "knowledge"], [item.kind for item in limited])

    def test_compiled_memory_remains_when_canonical_knowledge_is_not_indexed(self) -> None:
        memory = self.service.remember(
            "Orphan compiled", "orphanmarker historical content"
        )
        self._verify(memory.id)
        compiled = self.service.compile(
            memory.id, "orphan.md", "# Canonical\n\norphanmarker canonical terms.\n"
        )
        self.knowledge_repository.delete("orphan.md")

        results = self.service.search("orphanmarker")
        self.assertEqual([compiled.id], [result.id for result in results])
        self.assertEqual("compiled", results[0].status)
        self.assertEqual("memory", results[0].kind)

        self.service.rebuild_index()
        rebuilt_results = self.service.search("orphanmarker")
        self.assertEqual([compiled.id], [result.id for result in rebuilt_results])

    def test_deprecated_default_filter_and_explicit_memory_filters(self) -> None:
        candidate = self.service.remember("Visible candidate", "visibilitymarker")
        verified = self.service.remember("Visible verified", "visibilitymarker")
        self._verify(verified.id)
        deprecated = self.service.remember("Hidden deprecated", "visibilitymarker")
        self.service.update(deprecated.id, status="deprecated")
        self.knowledge_repository.write_atomic(
            "visibility.md", "# Visibility\n\nvisibilitymarker Knowledge.\n"
        )
        self.service.rebuild_index()

        default_ids = [item.id for item in self.service.search("visibilitymarker")]
        self.assertNotIn(deprecated.id, default_ids)
        self.assertIn(candidate.id, default_ids)
        self.assertIn(verified.id, default_ids)
        deprecated_results = self.service.search(
            "visibilitymarker", status="deprecated"
        )
        self.assertEqual([deprecated.id], [item.id for item in deprecated_results])
        self.assertTrue(all(item.kind == "memory" for item in deprecated_results))
        typed_results = self.service.search("visibilitymarker", type="learning")
        self.assertTrue(all(item.kind == "memory" for item in typed_results))

    def test_clear_and_rebuild_restores_index_without_mutating_canonical_data(self) -> None:
        memory = self.service.remember("Preserved Memory", "preservemarker")
        verified = self._verify(memory.id)
        markdown = "# Preserved Knowledge\n\n## Summary\n\npreservemarker canonical.\n"
        self.knowledge_repository.write_atomic("preserved.md", markdown)
        self.service.rebuild_index()
        memory_before = self.service.read(verified.id).to_dict()
        bytes_before = (self.knowledge_root / "preserved.md").read_bytes()

        self.index_repository.clear()
        self.assertEqual(
            [verified.id],
            [item.id for item in self.service.search("preservemarker")],
        )
        rebuilt = self.service.rebuild_index()

        self.assertEqual(1, rebuilt.knowledge_indexed)
        self.assertEqual(
            "knowledge:preserved.md", self.service.search("preservemarker")[0].id
        )
        self.index_repository._connection.executescript(
            "DROP TABLE knowledge_fts; DROP TABLE knowledge_index;"
        )
        rebuilt_after_drop = self.service.rebuild_index()
        self.assertEqual(1, rebuilt_after_drop.knowledge_indexed)
        self.assertEqual(
            "knowledge:preserved.md", self.service.search("preservemarker")[0].id
        )
        self.assertEqual(memory_before, self.service.read(verified.id).to_dict())
        self.assertEqual(bytes_before, (self.knowledge_root / "preserved.md").read_bytes())

    def test_failed_rebuild_rolls_back_index_and_does_not_mutate_sources(self) -> None:
        memory = self.service.remember("Failure safe", "failuremarker memory")
        verified = self._verify(memory.id)
        original = "# Original\n\n## Summary\n\nfailuremarker original.\n"
        added = "# Added\n\n## Summary\n\nfailuremarker added.\n"
        self.knowledge_repository.write_atomic("original.md", original)
        self.service.rebuild_index()
        self.knowledge_repository.write_atomic("added.md", added)
        memory_before = self.service.read(verified.id).to_dict()
        files_before = {
            path: (self.knowledge_root / path).read_bytes()
            for path in ("original.md", "added.md")
        }

        with patch.object(
            self.index_repository,
            "_insert_fts",
            side_effect=RuntimeError("injected rebuild failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "injected rebuild failure"):
                self.service.rebuild_index()

        results = self.service.search("failuremarker")
        self.assertIn("knowledge:original.md", [item.id for item in results])
        self.assertNotIn("knowledge:added.md", [item.id for item in results])
        self.assertEqual(memory_before, self.service.read(verified.id).to_dict())
        for path, expected in files_before.items():
            self.assertEqual(expected, (self.knowledge_root / path).read_bytes())


if __name__ == "__main__":
    unittest.main()

"""Tests for reproducible VAB run artifacts."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vab.artifacts import write_procurement_smoke_artifacts


class ArtifactTests(unittest.TestCase):
    def test_run_writes_complete_auditable_artifact_set(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            result = write_procurement_smoke_artifacts(
                "rule-based",
                output,
                run_at=datetime(2026, 9, 26, 10, 0, tzinfo=timezone.utc),
                git_commit="test-commit",
            )
            expected = {
                "manifest.json", "tasks.json", "traces.jsonl", "scores.json", "failures.json", "sha256sums.txt"
            }
            self.assertEqual(expected, {path.name for path in output.iterdir()})
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual("test-commit", manifest["git_commit"])
            self.assertEqual("rule-based", manifest["participant"])
            self.assertEqual(4, len(manifest["task_hashes"]))
            self.assertEqual([], result["failures"])
            self.assertEqual(3, len((output / "traces.jsonl").read_text().splitlines()))

            for line in (output / "sha256sums.txt").read_text().splitlines():
                digest, name = line.split("  ")
                self.assertEqual(digest, hashlib.sha256((output / name).read_bytes()).hexdigest())

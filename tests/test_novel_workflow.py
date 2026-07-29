#!/usr/bin/env python3
"""CLI 烟雾测试（无第三方依赖）。"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "novel_workflow.py"


class WorkflowTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_status_runs(self) -> None:
        r = self.run_cli("status")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("阶段", r.stdout)
        self.assertIn("潮汐守望者", r.stdout)

    def test_next_path(self) -> None:
        r = self.run_cli("next-path")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("chapters/001-", r.stdout)

    def test_scaffold_and_validate_fail_on_empty(self) -> None:
        # 使用临时章节号避免污染正式 001
        r = self.run_cli("scaffold", "--chapter", "99", "--title", "测试章", "--force")
        self.assertEqual(r.returncode, 0, r.stderr)
        chapter = ROOT / "manuscript" / "chapters" / "099-测试章.md"
        summary = ROOT / "manuscript" / "summaries" / "099.md"
        self.assertTrue(chapter.exists())
        self.assertTrue(summary.exists())
        v = self.run_cli("validate", "--chapter", "99")
        self.assertNotEqual(v.returncode, 0)
        # cleanup
        chapter.unlink(missing_ok=True)
        summary.unlink(missing_ok=True)

    def test_export_without_chapters(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out.md"
            r = self.run_cli("export", "--output", str(out))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(out.exists())
            text = out.read_text(encoding="utf-8")
            self.assertIn("潮汐守望者", text)


if __name__ == "__main__":
    unittest.main()

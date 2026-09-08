from __future__ import annotations

import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_changed_coverage.py"
SPEC = importlib.util.spec_from_file_location("check_changed_coverage", SCRIPT)
assert SPEC and SPEC.loader
check_changed_coverage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_changed_coverage)


class ChangedCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Coverage Test")
        self.git("config", "user.email", "coverage@example.invalid")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *arguments: str) -> str:
        return self.git_at(self.root, *arguments)

    def git_at(self, root: Path, *arguments: str) -> str:
        return subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def commit(self, message: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-qm", message)
        return self.git("rev-parse", "HEAD")

    def test_uses_merge_base_when_base_branch_advances(self) -> None:
        (self.root / "base.py").write_text("BASE = 1\n", encoding="utf-8")
        base = self.commit("base")
        self.git("switch", "-qc", "feature")
        feature = self.root / "scripts" / "feature.py"
        feature.parent.mkdir()
        feature.write_text("FEATURE = 1\n", encoding="utf-8")
        self.commit("feature")
        self.git("switch", "-q", "main")
        (self.root / "main.txt").write_text("advanced\n", encoding="utf-8")
        advanced_base = self.commit("advance base")
        self.git("switch", "-q", "feature")

        merge_base = check_changed_coverage.resolve_merge_base(
            self.root,
            advanced_base,
        )
        self.assertEqual(merge_base, base)
        self.assertEqual(
            check_changed_coverage.changed_python_paths(self.root, merge_base),
            ("scripts/feature.py",),
        )

    def test_changed_python_scope_is_table_driven(self) -> None:
        cases = (
            (
                "new missing file",
                {"README.md": "base\n"},
                {
                    "README.md": "base\n",
                    "scripts/new_check.py": "CHECK = True\n",
                },
                ("scripts/new_check.py",),
            ),
            (
                "rename",
                {"resources/scripts/old_name.py": "VALUE = 1\n"},
                {"resources/scripts/new_name.py": "VALUE = 1\n"},
                ("resources/scripts/new_name.py",),
            ),
            (
                "pure deletion",
                {"scripts/deleted.py": "VALUE = 1\n"},
                {},
                (),
            ),
            (
                "no Python diff",
                {"README.md": "base\n"},
                {"README.md": "changed\n"},
                (),
            ),
            (
                "Python outside coverage scope",
                {"tests/test_example.py": "VALUE = 1\n"},
                {"tests/test_example.py": "VALUE = 2\n"},
                (),
            ),
        )
        for index, (name, before, after, expected) in enumerate(cases):
            with self.subTest(name=name):
                root = self.root / f"case-{index}"
                root.mkdir()
                self.git_at(root, "init", "-q", "-b", "main")
                self.git_at(root, "config", "user.name", "Coverage Test")
                self.git_at(
                    root,
                    "config",
                    "user.email",
                    "coverage@example.invalid",
                )
                for relative, content in before.items():
                    path = root / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content, encoding="utf-8")
                self.git_at(root, "add", "-A")
                self.git_at(root, "commit", "-qm", "base")
                base = self.git_at(root, "rev-parse", "HEAD")
                for relative in set(before) - set(after):
                    (root / relative).unlink()
                for relative, content in after.items():
                    path = root / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content, encoding="utf-8")
                self.git_at(root, "add", "-A")
                self.git_at(root, "commit", "-qm", "change")
                self.assertEqual(
                    check_changed_coverage.changed_python_paths(root, base),
                    expected,
                )

    def test_missing_changed_file_in_coverage_fails_closed(self) -> None:
        coverage_xml = self.root / "coverage.xml"
        coverage_xml.write_text(
            "<coverage><packages><package><classes>"
            '<class filename="resources/scripts/runtime.py" />'
            "</classes></package></packages></coverage>",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            check_changed_coverage.ChangedCoverageError,
            "scripts/new_check.py",
        ):
            check_changed_coverage.require_changed_paths_in_coverage(
                self.root,
                coverage_xml,
                ("resources/scripts/runtime.py", "scripts/new_check.py"),
            )

    def test_local_scope_includes_pending_source_and_ignores_deletions(self) -> None:
        scripts = self.root / "scripts"
        scripts.mkdir()
        modified = scripts / "modified.py"
        deleted = scripts / "deleted.py"
        modified.write_text("VALUE = 1\n", encoding="utf-8")
        deleted.write_text("VALUE = 1\n", encoding="utf-8")
        (self.root / ".gitignore").write_text("scripts/ignored.py\n", encoding="utf-8")
        base = self.commit("base")
        modified.write_text("VALUE = 2\n", encoding="utf-8")
        deleted.unlink()
        (scripts / "staged.py").write_text("STAGED = True\n", encoding="utf-8")
        self.git("add", "scripts/staged.py")
        runtime = self.root / "resources/scripts"
        runtime.mkdir(parents=True)
        (runtime / "新 check.py").write_text("NEW = True\n", encoding="utf-8")
        (scripts / "ignored.py").write_text("IGNORED = True\n", encoding="utf-8")
        (self.root / "outside.py").write_text("OUTSIDE = True\n", encoding="utf-8")
        self.assertEqual(
            check_changed_coverage.changed_python_paths(self.root, base), ()
        )
        self.assertEqual(
            check_changed_coverage.changed_python_paths(
                self.root, base, include_uncommitted=True
            ),
            (
                "resources/scripts/新 check.py",
                "scripts/modified.py",
                "scripts/staged.py",
            ),
        )

    def test_unicode_paths_ignore_default_subprocess_encoding(self) -> None:
        (self.root / "README.md").write_text("base\n", encoding="utf-8")
        base = self.commit("base")
        tracked = self.root / "scripts/已 tracked.py"
        tracked.parent.mkdir()
        tracked.write_text("TRACKED = True\n", encoding="utf-8")
        self.commit("add tracked source")
        pending = self.root / "resources/scripts/新 pending.py"
        pending.parent.mkdir(parents=True)
        pending.write_text("PENDING = True\n", encoding="utf-8")
        # Exercise real Git output under the legacy text-decoding default used
        # by Windows Python, regardless of the current host's locale.
        with patch("subprocess._text_encoding", return_value="cp1252"):
            self.assertEqual(
                check_changed_coverage.changed_python_paths(self.root, base),
                ("scripts/已 tracked.py",),
            )
            self.assertEqual(
                check_changed_coverage.changed_python_paths(
                    self.root, base, include_uncommitted=True
                ),
                ("resources/scripts/新 pending.py", "scripts/已 tracked.py"),
            )

    def test_local_main_checks_untracked_coverage_and_explicit_base_without_pr(
        self,
    ) -> None:
        (self.root / "README.md").write_text("base\n", encoding="utf-8")
        base = self.commit("base")
        source = self.root / "scripts/new.py"
        source.parent.mkdir()
        source.write_text("CHECK = True\n", encoding="utf-8")
        coverage_xml = self.root / "coverage.xml"
        arguments = [
            str(SCRIPT),
            "--root",
            str(self.root),
            "--coverage",
            str(coverage_xml),
        ]
        for hits, expected in ((None, 2), (0, 2), (1, 0)):
            coverage_xml.write_text(
                '<coverage><packages><package name="scripts"><classes>'
                + (
                    ""
                    if hits is None
                    else (
                        '<class filename="scripts/new.py"><lines>'
                        f'<line number="1" hits="{hits}"/>'
                        "</lines></class>"
                    )
                )
                + "</classes></package></packages></coverage>",
                encoding="utf-8",
            )
            with (
                self.subTest(hits=hits),
                patch.dict(
                    os.environ, {"GITHUB_EVENT_NAME": "push", "PR_BASE_SHA": "ignored"}
                ),
                patch.object(sys, "argv", [*arguments, "--local"]),
            ):
                self.assertEqual(check_changed_coverage.main(), expected)
        self.commit("add source")
        with (
            patch.dict(os.environ, {"GITHUB_EVENT_NAME": "push"}),
            patch.object(sys, "argv", [*arguments, "--base-sha", base]),
        ):
            self.assertEqual(check_changed_coverage.main(), 0)

    def test_pr_still_requires_a_baseline(self) -> None:
        with (
            patch.dict(os.environ, {"GITHUB_EVENT_NAME": "pull_request"}, clear=True),
            patch.object(sys, "argv", [str(SCRIPT), "--root", str(self.root)]),
            redirect_stderr(io.StringIO()) as stderr,
        ):
            self.assertEqual(check_changed_coverage.main(), 2)
        self.assertIn("PR_BASE_SHA is required", stderr.getvalue())

    def test_pr_main_rejects_missing_coverage_before_diff_cover(self) -> None:
        path = self.root / "scripts" / "new_check.py"
        path.parent.mkdir()
        (self.root / "README.md").write_text("base\n", encoding="utf-8")
        base = self.commit("base")
        path.write_text("CHECK = True\n", encoding="utf-8")
        self.commit("add check")
        coverage_xml = self.root / "coverage.xml"
        coverage_xml.write_text("<coverage />", encoding="utf-8")
        stderr = io.StringIO()
        with (
            patch.dict(
                os.environ,
                {"GITHUB_EVENT_NAME": "pull_request"},
                clear=False,
            ),
            patch.object(
                sys,
                "argv",
                [
                    str(SCRIPT),
                    "--root",
                    str(self.root),
                    "--coverage",
                    str(coverage_xml),
                    "--base-sha",
                    base,
                ],
            ),
            patch.object(check_changed_coverage, "run_diff_cover") as diff_cover,
            redirect_stderr(stderr),
        ):
            self.assertEqual(check_changed_coverage.main(), 2)
        diff_cover.assert_not_called()
        self.assertIn("missing from coverage XML", stderr.getvalue())

    def test_non_pr_event_skips_without_git_or_coverage_inputs(self) -> None:
        with (
            patch.dict(os.environ, {"GITHUB_EVENT_NAME": "push"}, clear=False),
            patch.object(sys, "argv", [str(SCRIPT)]),
        ):
            self.assertEqual(check_changed_coverage.main(), 0)

    def test_invalid_base_sha_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            check_changed_coverage.ChangedCoverageError,
            "full commit hash",
        ):
            check_changed_coverage.resolve_merge_base(self.root, "main")

    def test_malformed_coverage_and_diff_cover_fail_closed(self) -> None:
        malformed = self.root / "malformed.xml"
        malformed.write_text("<coverage>", encoding="utf-8")
        with self.assertRaisesRegex(
            check_changed_coverage.ChangedCoverageError,
            "malformed",
        ):
            check_changed_coverage.coverage_xml_paths(self.root, malformed)

        missing_filename = self.root / "missing-filename.xml"
        missing_filename.write_text(
            "<coverage><class /></coverage>",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            check_changed_coverage.ChangedCoverageError,
            "without a file",
        ):
            check_changed_coverage.coverage_xml_paths(self.root, missing_filename)

        with (
            patch.object(check_changed_coverage.shutil, "which", return_value=None),
            self.assertRaisesRegex(
                check_changed_coverage.ChangedCoverageError,
                "unavailable",
            ),
        ):
            check_changed_coverage.run_diff_cover(
                self.root,
                malformed,
                "a" * 40,
                fail_under=90,
            )

        failed = subprocess.CompletedProcess([], 1, "", "")
        with (
            patch.object(
                check_changed_coverage.shutil,
                "which",
                return_value="diff-cover",
            ),
            patch.object(
                check_changed_coverage.subprocess,
                "run",
                return_value=failed,
            ),
            self.assertRaisesRegex(
                check_changed_coverage.ChangedCoverageError,
                "exit code 1",
            ),
        ):
            check_changed_coverage.run_diff_cover(
                self.root,
                malformed,
                "a" * 40,
                fail_under=90,
            )


if __name__ == "__main__":
    unittest.main()

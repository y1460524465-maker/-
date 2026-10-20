import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "01-agent-layer"))

from scripts import workspace


EMPTY_INDEX = """# 工作事项总览

## 活动事项

<!-- ACTIVE_ITEMS_START -->
| ID | 标题 | 状态 | 最近更新 | 工作路径 | 状态路径 |
|---|---|---|---|---|---|
<!-- ACTIVE_ITEMS_END -->

## 已归档事项

<!-- ARCHIVED_ITEMS_START -->
| ID | 标题 | 完成日期 | 工作路径 | 状态路径 |
|---|---|---|---|---|
<!-- ARCHIVED_ITEMS_END -->
"""


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self._temp_dir.name)

    def tearDown(self):
        self._temp_dir.cleanup()

    def _write_index(self):
        path = self.root / "02-work-items" / "WORK_INDEX.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(EMPTY_INDEX, encoding="utf-8", newline="\n")

    def _write_config(self, mode="shared-kit", shared_layer=None):
        path = self.root / ".ai-workspace.json"
        config = {
            "schemaVersion": 1,
            "mode": mode,
            "name": "test-workspace",
        }
        if shared_layer is not None:
            config["sharedAgentLayer"] = str(shared_layer)
        path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def _prepare_new_item_root(self):
        shutil.copytree(
            REPO_ROOT / "01-agent-layer" / "templates" / "work-item",
            self.root / "01-agent-layer" / "templates" / "work-item",
        )
        self._write_config()
        self._write_index()

    def _prepare_valid_workspace(self):
        for relative_path in [
            "AGENTS.md",
            "CLAUDE.md",
            "GEMINI.md",
            ".cursor/rules/agent-guide.mdc",
            ".github/copilot-instructions.md",
            "01-agent-layer/AGENT_GUIDE.md",
            "01-agent-layer/router/context-router.md",
            "01-agent-layer/scripts/workspace.py",
            "01-agent-layer/githooks/pre-commit",
        ]:
            source = REPO_ROOT / relative_path
            destination = self.root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

        for relative_dir in [
            "01-agent-layer/core",
            "01-agent-layer/contexts",
            "01-agent-layer/templates",
            "03-session-state/knowledge",
        ]:
            shutil.copytree(REPO_ROOT / relative_dir, self.root / relative_dir)

        for relative_dir in [
            "02-work-items/active",
            "02-work-items/archived",
            "03-session-state/active",
            "03-session-state/archived",
        ]:
            (self.root / relative_dir).mkdir(parents=True, exist_ok=True)
        self._write_config()
        self._write_index()

        return workspace.create_item(
            root=self.root,
            slug="alpha",
            title="Alpha 需求",
            workspaces=["requirement"],
            date="2026-10-19",
        )

    def test_create_item_bootstraps_work_and_state(self):
        self._prepare_new_item_root()
        item_id = "2026-10-19-alpha"

        work_path = workspace.create_item(
            root=self.root,
            slug="alpha",
            title="Alpha 需求",
            workspaces=["requirement", "investigation"],
            date="2026-10-19",
        )
        state_path = self.root / "03-session-state" / "active" / item_id

        self.assertEqual(
            work_path,
            self.root / "02-work-items" / "active" / item_id,
        )
        self.assertTrue((work_path / "brief.md").is_file())
        self.assertTrue((work_path / "reviews" / "README.md").is_file())
        self.assertTrue((work_path / "workspaces" / "requirement" / "README.md").is_file())
        self.assertTrue((state_path / "STATUS.md").is_file())
        self.assertTrue((state_path / "handoff.md").is_file())
        self.assertTrue((state_path / "journal" / "2026-10-19.md").is_file())
        self.assertFalse((work_path / "STATUS.md").exists())

        status = (state_path / "STATUS.md").read_text(encoding="utf-8")
        self.assertIn('id: "2026-10-19-alpha"', status)
        self.assertIn("status: planning", status)
        index = (self.root / "02-work-items" / "WORK_INDEX.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            f"| {item_id} | Alpha 需求 | planning | 2026-10-19 | "
            f"`02-work-items/active/{item_id}/` | "
            f"`03-session-state/active/{item_id}/` |",
            index,
        )

    def test_context_manifest_for_modes(self):
        self._prepare_new_item_root()
        workspace.create_item(
            root=self.root,
            slug="alpha",
            title="Alpha 需求",
            workspaces=["requirement"],
            date="2026-10-19",
        )
        item_id = "2026-10-19-alpha"
        work_prefix = f"02-work-items/active/{item_id}"
        state_prefix = f"03-session-state/active/{item_id}"

        auto = workspace.context_manifest(self.root, item_id, "auto")
        self.assertEqual(
            auto["always_load"],
            [
                "01-agent-layer/AGENT_GUIDE.md",
                "01-agent-layer/core/invariants.md",
                "01-agent-layer/router/context-router.md",
            ],
        )
        self.assertEqual(
            auto["item_state"],
            [
                f"{state_prefix}/STATUS.md",
                f"{state_prefix}/handoff.md",
                f"{work_prefix}/brief.md",
                f"{state_prefix}/journal/2026-10-19.md",
            ],
        )

        mixed = workspace.context_manifest(self.root, item_id, "delegation,coding,review,sync")
        self.assertEqual(
            mixed["scenario"],
            [
                "01-agent-layer/contexts/delegation.md",
                "01-agent-layer/contexts/coding.md",
                "01-agent-layer/contexts/codex-review.md",
                "01-agent-layer/contexts/sync.md",
            ],
        )
        self.assertIn(f"{state_prefix}/decisions.md", mixed["load_on_demand"])
        self.assertIn(f"{work_prefix}/workspaces/README.md", mixed["load_on_demand"])

    def test_create_item_rejects_unsafe_names(self):
        self._prepare_new_item_root()
        for slug in ["../escape", "nested/path", "..", "Uppercase", ""]:
            with self.subTest(slug=slug):
                with self.assertRaises(ValueError):
                    workspace.create_item(
                        root=self.root,
                        slug=slug,
                        title="Unsafe",
                        date="2026-10-19",
                    )

    def test_create_item_preserves_quoted_title(self):
        self._prepare_new_item_root()
        workspace.create_item(
            root=self.root,
            slug="quoted-title",
            title='需求 "A"',
            date="2026-10-19",
        )
        status = (
            self.root
            / "03-session-state"
            / "active"
            / "2026-10-19-quoted-title"
            / "STATUS.md"
        ).read_text(encoding="utf-8")
        self.assertIn('title: "需求 \\"A\\""', status)
        self.assertIn('# STATUS — 需求 "A"', status)

    def test_validate_reports_contract_errors(self):
        work_path = self._prepare_valid_workspace()
        state_path = (
            self.root / "03-session-state" / "active" / "2026-10-19-alpha"
        )
        self.assertEqual(workspace.validate_workspace(self.root), [])

        def remove_state_status(root):
            (root / "03-session-state" / "active" / "2026-10-19-alpha" / "STATUS.md").unlink()

        def remove_heading(root):
            path = root / "03-session-state" / "active" / "2026-10-19-alpha" / "STATUS.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace("## 最近验证", "## 验证"), encoding="utf-8", newline="\n")

        def leave_placeholder(root):
            path = root / "02-work-items" / "active" / "2026-10-19-alpha" / "brief.md"
            with path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write("\n{{LEFTOVER}}\n")

        def break_adapter(root):
            path = root / "AGENTS.md"
            with path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write("\nAsk before reading state.\n")

        def remove_pair(root):
            shutil.rmtree(root / "03-session-state" / "active" / "2026-10-19-alpha")

        def remove_reviews(root):
            shutil.rmtree(root / "02-work-items" / "active" / "2026-10-19-alpha" / "reviews")

        def add_flat_review(root):
            path = root / "02-work-items" / "active" / "2026-10-19-alpha" / "reviews" / "review.md"
            path.write_text("# flat review\n", encoding="utf-8", newline="\n")

        cases = [
            ("missing state status", remove_state_status, "STATUS.md"),
            ("missing heading", remove_heading, "最近验证"),
            ("work placeholder", leave_placeholder, "占位"),
            ("adapter drift", break_adapter, "适配器"),
            ("missing state pair", remove_pair, "配对"),
            ("missing reviews directory", remove_reviews, "reviews"),
            ("flat review evidence", add_flat_review, "round-N"),
        ]
        for label, mutate, expected in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as temp_dir:
                original_root = self.root
                try:
                    self.root = Path(temp_dir)
                    self._prepare_valid_workspace()
                    mutate(self.root)
                    errors = workspace.validate_workspace(self.root)
                    self.assertTrue(
                        any(expected in error for error in errors),
                        f"expected {expected!r} in {errors!r}",
                    )
                finally:
                    self.root = original_root

        self.assertTrue(work_path.is_dir())
        self.assertTrue(state_path.is_dir())

    def test_validate_ignores_vendored_tool_placeholders(self):
        work_path = self._prepare_valid_workspace()
        stream = work_path / "workspaces" / "implementation"
        stream.mkdir(parents=True)
        (stream / "README.md").write_text("# implementation\n", encoding="utf-8")
        vendored = stream / ".tools" / "go" / "doc" / "godebug.md"
        vendored.parent.mkdir(parents=True)
        vendored.write_text("{{.DefaultGODEBUG}}\n", encoding="utf-8")
        self.assertEqual(workspace.validate_workspace(self.root), [])

    def test_cli_validate_uses_exit_codes(self):
        self._prepare_valid_workspace()
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = workspace.main(["--root", str(self.root), "validate"])
        self.assertEqual(code, 0, stderr.getvalue())
        self.assertIn("OK", stdout.getvalue())

    def test_discover_project_root_from_nested_directory(self):
        self._prepare_valid_workspace()
        nested = self.root / "02-work-items" / "active" / "2026-10-19-alpha" / "workspaces"
        self.assertEqual(
            workspace.discover_project_root(nested),
            self.root.resolve(),
        )
        self.assertEqual(
            workspace.resolve_project_root(explicit_root=self.root, start=nested),
            self.root.resolve(),
        )

    def test_validate_rejects_broken_project_shared_layer(self):
        self._prepare_valid_workspace()
        config_path = self.root / ".ai-workspace.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["mode"] = "project"
        config["sharedAgentLayer"] = str(self.root / "missing-shared-layer")
        config_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        errors = workspace.validate_workspace(self.root)
        self.assertTrue(any("sharedAgentLayer" in error for error in errors), errors)

    @unittest.skipUnless(os.name == "nt", "Windows directory junctions are required")
    def test_new_project_uses_shared_layer_and_isolates_items(self):
        script = REPO_ROOT / "01-agent-layer" / "scripts" / "New-AiProject.ps1"
        self.assertTrue(script.is_file(), "project generator is missing")
        shared_layer = REPO_ROOT / "01-agent-layer"
        project_a = self.root / "Project-A"
        project_b = self.root / "Project-B"
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        self.assertIsNotNone(powershell)

        for project in [project_a, project_b]:
            command = [
                powershell,
                "-NoProfile",
                "-File",
                str(script),
                "-Path",
                str(project),
            ]
            if project == project_b:
                command.extend(["-SharedLayer", str(shared_layer)])
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

        self.assertEqual(
            (project_a / "01-agent-layer" / "AGENT_GUIDE.md").read_text(encoding="utf-8"),
            (shared_layer / "AGENT_GUIDE.md").read_text(encoding="utf-8"),
        )
        self.assertTrue(
            os.path.samefile(
                project_a / "01-agent-layer" / "AGENT_GUIDE.md",
                shared_layer / "AGENT_GUIDE.md",
            )
        )
        self.assertTrue((project_a / ".git").is_dir())
        self.assertTrue((project_b / ".git").is_dir())
        status_a = subprocess.run(
            ["git", "-C", str(project_a), "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).stdout
        self.assertNotIn("01-agent-layer/", status_a)
        hooks_path = subprocess.run(
            ["git", "-C", str(project_a), "config", "--get", "core.hooksPath"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).stdout.strip()
        self.assertEqual(hooks_path, "01-agent-layer/githooks")

        subprocess.run(
            [
                sys.executable,
                str(project_a / "01-agent-layer" / "scripts" / "workspace.py"),
                "new-item",
                "alpha",
                "--title",
                "Alpha",
                "--date",
                "2026-10-19",
            ],
            cwd=project_a,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        subprocess.run(
            ["git", "-C", str(project_b), "hook", "run", "pre-commit"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertTrue(
            (project_a / "02-work-items" / "active" / "2026-10-19-alpha").is_dir()
        )
        self.assertFalse(
            (project_b / "02-work-items" / "active" / "2026-10-19-alpha").exists()
        )
        self.assertNotIn(
            "2026-10-19-alpha",
            (project_b / "02-work-items" / "WORK_INDEX.md").read_text(encoding="utf-8"),
        )
        subprocess.run(
            [
                sys.executable,
                str(project_b / "01-agent-layer" / "scripts" / "workspace.py"),
                "validate",
            ],
            cwd=project_b,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )


if __name__ == "__main__":
    unittest.main()

import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import dsh_bridge


class DshBridgeTests(unittest.TestCase):
    def setUp(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self._temp_dir.name)
        self.item_id = "2026-10-19-alpha"
        self.item_path = self.root / "02-work-items" / "active" / self.item_id
        self.item_path.mkdir(parents=True)
        self.cwd = self.item_path / "workspaces" / "implementation"
        self.cwd.mkdir(parents=True)
        self.task_file = self.item_path / "task.md"
        self.task_file.write_text("实现功能并运行测试。\n", encoding="utf-8")
        self.patch_file = self.root / "headless-codex.patch.yml"
        self.patch_file.write_text(
            "- id: credentials\n  disabled: false\n",
            encoding="utf-8",
        )
        self.record_path = self.root / "fake-record.json"
        self.fake_dsh = self._write_fake_dsh()

    def tearDown(self):
        self._temp_dir.cleanup()

    def _write_fake_dsh(self):
        fake_python = self.root / "fake_dsh.py"
        fake_python.write_text(
            """
import json
import os
import subprocess
import sys
import time

record = {
    "args": sys.argv[1:],
    "stdin": sys.stdin.read(),
    "env": dict(os.environ),
}
with open(os.environ["FAKE_DSH_RECORD"], "w", encoding="utf-8") as handle:
    json.dump(record, handle, ensure_ascii=False)

session_id = os.environ.get("FAKE_DSH_SESSION", "session-fake")
print(json.dumps({"type": "session", "sessionId": session_id, "cwd": os.getcwd()}), flush=True)
print(json.dumps({"type": "status", "phase": "turn_start", "turn": 1}), flush=True)

sleep_seconds = float(os.environ.get("FAKE_DSH_SLEEP", "0"))
if sleep_seconds:
    time.sleep(sleep_seconds)

if os.environ.get("FAKE_DSH_ERROR") == "1":
    print(json.dumps({
        "type": "status",
        "phase": "turn_end",
        "reason": {"kind": "error", "error": {"message": "fake failure"}},
    }), flush=True)
    print(json.dumps({"type": "final", "text": ""}), flush=True)
    raise SystemExit(1)

if os.environ.get("FAKE_DSH_COMMIT") == "1":
    with open("unauthorized.txt", "w", encoding="utf-8") as handle:
        handle.write("unexpected commit\\n")
    subprocess.run(["git", "add", "unauthorized.txt"], check=True)
    subprocess.run(
        ["git", "-c", "user.name=Fake", "-c", "user.email=fake@example.invalid",
         "commit", "-m", "fake delegated commit"],
        check=True,
        capture_output=True,
    )

print(json.dumps({
    "type": "status",
    "phase": "turn_end",
    "reason": {"kind": "completed"},
}), flush=True)
print(json.dumps({"type": "final", "text": "实现完成"}, ensure_ascii=False), flush=True)
""".strip()
            + "\n",
            encoding="utf-8",
        )
        fake_cmd = self.root / "fake_dsh.cmd"
        fake_cmd.write_text(
            f'@echo off\r\n"{sys.executable}" "{fake_python}" %*\r\n',
            encoding="utf-8",
        )
        return fake_cmd

    def _delegate(self, **overrides):
        values = {
            "root": self.root,
            "item_id": self.item_id,
            "task_file": self.task_file,
            "cwd": self.cwd,
            "label": "implement",
            "session_id": None,
            "permission_mode": "workspace-write",
            "timeout": 5,
            "dsh": self.fake_dsh,
            "patch": self.patch_file,
        }
        values.update(overrides)
        return dsh_bridge.delegate_item(**values)

    def test_delegate_saves_events_result_and_metadata(self):
        environment = {
            "FAKE_DSH_RECORD": str(self.record_path),
            "FAKE_DSH_SESSION": "session-123",
            "MY_API_KEY": "must-not-leak",
            "CUSTOM_TOKEN": "must-not-leak",
            "NORMAL_VALUE": "kept",
        }
        with patch.dict(os.environ, environment, clear=False):
            result = self._delegate()

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.session_id, "session-123")
        self.assertEqual(result.final_text, "实现完成")

        delegation_dir = self.item_path / "artifacts" / "delegation"
        self.assertTrue(result.request_path.is_file())
        self.assertTrue(result.events_path.is_file())
        self.assertTrue(result.result_path.is_file())
        self.assertTrue(result.meta_path.is_file())
        self.assertIn("session-123", (delegation_dir / "INDEX.md").read_text(encoding="utf-8"))
        self.assertIn("实现功能并运行测试", result.request_path.read_text(encoding="utf-8"))
        self.assertIn("实现完成", result.result_path.read_text(encoding="utf-8"))

        record = json.loads(self.record_path.read_text(encoding="utf-8"))
        self.assertEqual(
            record["args"][:6],
            ["--profile", "headless", "--patch", str(self.patch_file), "--json", "-"],
        )
        self.assertEqual(record["stdin"], "实现功能并运行测试。\n")
        self.assertEqual(record["env"]["DSH_PERMISSION_MODE"], "workspace-write")
        self.assertNotIn("MY_API_KEY", record["env"])
        self.assertNotIn("CUSTOM_TOKEN", record["env"])
        self.assertEqual(record["env"]["NORMAL_VALUE"], "kept")

        meta = json.loads(result.meta_path.read_text(encoding="utf-8"))
        self.assertEqual(meta["session_id"], "session-123")
        self.assertEqual(meta["status"], "completed")
        self.assertEqual(meta["permission_mode"], "workspace-write")

    def test_delegate_returns_error_status_for_failed_run(self):
        environment = {
            "FAKE_DSH_RECORD": str(self.record_path),
            "FAKE_DSH_ERROR": "1",
        }
        with patch.dict(os.environ, environment, clear=False):
            result = self._delegate()

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.status, "error")
        self.assertIn("fake failure", result.meta_path.read_text(encoding="utf-8"))
        self.assertIn('"type": "final"', result.events_path.read_text(encoding="utf-8"))

    def test_delegate_returns_timeout_status(self):
        environment = {
            "FAKE_DSH_RECORD": str(self.record_path),
            "FAKE_DSH_SLEEP": "1.0",
        }
        with patch.dict(os.environ, environment, clear=False):
            result = self._delegate(timeout=0.2)

        self.assertEqual(result.exit_code, 124)
        self.assertEqual(result.status, "timeout")
        self.assertTrue(result.events_path.is_file())
        self.assertIn("timeout", result.result_path.read_text(encoding="utf-8").lower())

    def test_delegate_reuses_session_and_rejects_unsafe_permission_mode(self):
        environment = {
            "FAKE_DSH_RECORD": str(self.record_path),
            "FAKE_DSH_SESSION": "session-existing",
        }
        with patch.dict(os.environ, environment, clear=False):
            result = self._delegate(session_id="session-existing")

        record = json.loads(self.record_path.read_text(encoding="utf-8"))
        self.assertEqual(result.session_id, "session-existing")
        session_index = record["args"].index("--session-id")
        self.assertEqual(record["args"][session_index + 1], "session-existing")

        with self.assertRaisesRegex(ValueError, "权限模式"):
            self._delegate(permission_mode="danger-full-access")

    def test_delegate_rejects_missing_task_and_workdir_before_launch(self):
        with self.assertRaisesRegex(FileNotFoundError, "任务单"):
            self._delegate(task_file=self.root / "missing.md")
        with self.assertRaisesRegex(FileNotFoundError, "工作目录"):
            self._delegate(cwd=self.root / "missing")
        self.assertFalse(self.record_path.exists())

    def test_doctor_reports_missing_launcher_and_patch(self):
        report = dsh_bridge.doctor(self.fake_dsh, self.patch_file)
        self.assertTrue(report["dsh_ok"])
        self.assertTrue(report["patch_ok"])

        missing = dsh_bridge.doctor(self.root / "missing.cmd", self.root / "missing.yml")
        self.assertFalse(missing["dsh_ok"])
        self.assertFalse(missing["patch_ok"])

        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = dsh_bridge.main(
                [
                    "doctor",
                    "--dsh",
                    str(self.fake_dsh),
                    "--patch",
                    str(self.patch_file),
                ]
            )
        self.assertEqual(exit_code, 0, stderr.getvalue())
        self.assertIn("DSH_CLI_OK: yes", stdout.getvalue())

    def test_delegate_flags_worker_commit_as_policy_violation(self):
        subprocess.run(["git", "init"], cwd=self.cwd, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=self.cwd,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=self.cwd,
            check=True,
        )
        (self.cwd / "README.md").write_text("initial\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.cwd, check=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=self.cwd,
            check=True,
            capture_output=True,
        )

        environment = {
            "FAKE_DSH_RECORD": str(self.record_path),
            "FAKE_DSH_COMMIT": "1",
        }
        with patch.dict(os.environ, environment, clear=False):
            result = self._delegate()

        meta = json.loads(result.meta_path.read_text(encoding="utf-8"))
        self.assertEqual(
            result.status,
            "policy_violation",
            result.result_path.read_text(encoding="utf-8"),
        )
        self.assertTrue(meta["git_head_changed"])

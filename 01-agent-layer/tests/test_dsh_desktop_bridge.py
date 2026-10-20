import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import dsh_desktop_bridge


class RecordingHandler(BaseHTTPRequestHandler):
    responses = []
    requests = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        type(self).requests.append(
            {
                "path": self.path,
                "cookie": self.headers.get("Cookie"),
                "body": json.loads(body),
            }
        )
        status, response = type(self).responses.pop(0)
        payload = json.dumps(response).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        pass


class FakeDesktopClient:
    def __init__(
        self,
        *,
        cwd: Path,
        no_completion: bool = False,
        danger: bool = False,
    ):
        self.port = 53208
        self.cwd = str(cwd)
        self.no_completion = no_completion
        self.danger = danger
        self.calls = []
        self.projection_counts = 0

    def call(self, endpoint, method, request):
        self.calls.append((endpoint, method, request))
        if endpoint == "workspace/create":
            return {
                "workspace": {
                    "workspaceId": "ws-1",
                    "path": self.cwd,
                    "title": "implementation",
                    "sessionIds": [],
                    "createdAt": "2026-10-19T00:00:00.000Z",
                    "updatedAt": "2026-10-19T00:00:00.000Z",
                }
            }
        if endpoint == "workspace/rename":
            return {
                "workspace": {
                    "workspaceId": "ws-1",
                    "path": self.cwd,
                    "title": request["request"]["title"],
                    "sessionIds": [],
                    "createdAt": "2026-10-19T00:00:00.000Z",
                    "updatedAt": "2026-10-19T00:00:00.000Z",
                }
            }
        if endpoint == "session/create":
            return {"sessionId": request["request"]["sessionId"]}
        if endpoint == "session/rename":
            return {"title": request["request"]["title"], "seq": 1}
        if endpoint == "session/prompt":
            return {"accepted": True}
        if endpoint == "session/projections":
            self.projection_counts += 1
            seq = 1 if self.projection_counts == 1 or self.no_completion else 5
            return {
                "kind": "sequenced",
                "asOfSeq": seq,
                "values": {
                    "title": "Desktop live task",
                    "workingDirectory": self.cwd,
                    "permissions": {
                        "currentValue": (
                            "danger-full-access" if self.danger else "workspace-write"
                        )
                    },
                },
            }
        if endpoint == "session/page":
            records = [
                {
                    "type": "event",
                    "event": {
                        "type": "user/message",
                        "seq": 1,
                        "time": 1792400000000,
                        "data": {"text": "old prompt"},
                    },
                },
                {
                    "type": "event",
                    "event": {
                        "type": "assistant/message",
                        "seq": 4,
                        "time": 1792400001000,
                        "data": {
                            "message": {
                                "role": "assistant",
                                "content": [
                                    {"type": "text", "text": "DESKTOP_LIVE_OK"}
                                ],
                            }
                        },
                    },
                },
                {
                    "type": "event",
                    "event": {
                        "type": "turn/end",
                        "seq": 5,
                        "time": 1792400002000,
                        "data": {"turn": 1, "reason": {"kind": "completed"}},
                    },
                },
            ]
            if self.no_completion:
                records = records[:1]
            return {"records": records, "hasMore": False}
        raise AssertionError(f"Unexpected endpoint: {endpoint}")


class DesktopBridgeTests(unittest.TestCase):
    def setUp(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self._temp_dir.name)
        self.item_id = "2026-10-19-alpha"
        self.item_path = self.root / "02-work-items" / "active" / self.item_id
        self.cwd = self.item_path / "workspaces" / "implementation"
        self.cwd.mkdir(parents=True)
        self.task_file = self.item_path / "task.md"
        self.task_file.write_text("Build the thing.\n", encoding="utf-8")

    def tearDown(self):
        self._temp_dir.cleanup()

    def test_client_uses_desktop_rpc_envelope(self):
        RecordingHandler.requests = []
        RecordingHandler.responses = [
            (
                200,
                {
                    "type": "server-response",
                    "rpcId": "test",
                    "result": {"ok": True, "value": {"items": []}},
                },
            )
        ]
        server = ThreadingHTTPServer(("127.0.0.1", 0), RecordingHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = dsh_desktop_bridge.DesktopHostClient(
                server.server_address[1],
                "dsh-auth-test=value",
            )
            value = client.call("session/list", "session/list", {"_request": {}})
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertEqual(value, {"items": []})
        recorded = RecordingHandler.requests[0]
        self.assertEqual(recorded["path"], "/api/session/list")
        self.assertEqual(recorded["cookie"], "dsh-auth-test=value")
        self.assertEqual(
            recorded["body"],
            {
                "type": "client-request",
                "rpcId": recorded["body"]["rpcId"],
                "method": "session/list",
                "payload": {"args": {"_request": {}}},
            },
        )

    def test_delegate_creates_visible_session_and_collects_result(self):
        client = FakeDesktopClient(cwd=self.cwd)
        focused = []

        result = dsh_desktop_bridge.delegate_desktop(
            client=client,
            root=self.root,
            item_id=self.item_id,
            task_file=self.task_file,
            cwd=self.cwd,
            label="implement",
            session_id=None,
            timeout=1,
            poll_interval=0,
            focus_callback=lambda workspace, session: focused.append((workspace, session)),
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.final_text, "DESKTOP_LIVE_OK")
        self.assertEqual(result.workspace_id, "ws-1")
        self.assertEqual(result.session_id, result.session_id)
        self.assertTrue(result.request_path.is_file())
        self.assertTrue(result.events_path.is_file())
        self.assertTrue(result.result_path.is_file())
        self.assertTrue(result.meta_path.is_file())
        self.assertIn("Build the thing.", result.request_path.read_text(encoding="utf-8"))
        self.assertIn("DESKTOP_LIVE_OK", result.result_path.read_text(encoding="utf-8"))
        meta = json.loads(result.meta_path.read_text(encoding="utf-8"))
        self.assertEqual(meta["workspace_id"], "ws-1")
        self.assertEqual(meta["session_id"], result.session_id)
        self.assertNotIn("cookie", json.dumps(meta).lower())

        endpoints = [call[0] for call in client.calls]
        self.assertEqual(endpoints[:6], [
            "workspace/create",
            "workspace/rename",
            "session/create",
            "session/rename",
            "session/projections",
            "session/prompt",
        ])
        self.assertEqual(focused, [(self.item_id, f"{self.item_id} · implement")])
        prompt = next(call for call in client.calls if call[0] == "session/prompt")
        self.assertEqual(prompt[2]["request"]["content"][0]["text"], "Build the thing.\n")

    def test_delegate_timeout_without_new_turn_end(self):
        client = FakeDesktopClient(cwd=self.cwd, no_completion=True)

        result = dsh_desktop_bridge.delegate_desktop(
            client=client,
            root=self.root,
            item_id=self.item_id,
            task_file=self.task_file,
            cwd=self.cwd,
            label="timeout-test",
            session_id=None,
            timeout=0.01,
            poll_interval=0,
        )

        self.assertEqual(result.status, "timeout")
        self.assertEqual(result.exit_code, 124)
        self.assertIn("timeout", result.result_path.read_text(encoding="utf-8").lower())

    def test_delegate_reuses_existing_session_without_create(self):
        client = FakeDesktopClient(cwd=self.cwd)

        result = dsh_desktop_bridge.delegate_desktop(
            client=client,
            root=self.root,
            item_id=self.item_id,
            task_file=self.task_file,
            cwd=self.cwd,
            label="fix-1",
            session_id="session-existing",
            timeout=1,
            poll_interval=0,
            focus_callback=lambda workspace, session: None,
        )

        endpoints = [call[0] for call in client.calls]
        self.assertNotIn("session/create", endpoints)
        self.assertNotIn("workspace/create", endpoints)
        self.assertEqual(result.session_id, "session-existing")
        self.assertEqual(result.status, "completed")

    def test_select_authenticated_connection_uses_valid_cookie(self):
        attempts = []

        class ProbeClient:
            def __init__(self, port, cookie):
                self.port = port
                self.cookie = cookie

            def call(self, endpoint, method, request):
                attempts.append((self.port, self.cookie))
                if self.cookie == "dsh-auth-good=ok":
                    return {"items": []}
                raise dsh_desktop_bridge.DesktopBridgeError("401 unauthorized")

        connection = dsh_desktop_bridge.select_authenticated_connection(
            ports=[53208, 53209],
            cookies=["dsh-auth-bad=no", "dsh-auth-good=ok"],
            client_factory=ProbeClient,
        )

        self.assertEqual(connection.port, 53208)
        self.assertEqual(connection.cookie, "dsh-auth-good=ok")
        self.assertEqual(attempts, [(53208, "dsh-auth-bad=no"), (53208, "dsh-auth-good=ok")])

    def test_delegate_rejects_danger_full_access_session(self):
        client = FakeDesktopClient(cwd=self.cwd, danger=True)

        result = dsh_desktop_bridge.delegate_desktop(
            client=client,
            root=self.root,
            item_id=self.item_id,
            task_file=self.task_file,
            cwd=self.cwd,
            label="danger-test",
            session_id=None,
            timeout=1,
            poll_interval=0,
        )

        self.assertEqual(result.status, "error")
        self.assertIn(
            "danger-full-access",
            result.result_path.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()

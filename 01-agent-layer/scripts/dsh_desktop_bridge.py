from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DSH_EXE = Path(r"D:\Apps\DeepSeek Harness\DeepSeek Harness.exe")
DEFAULT_DEVTOOLS_PORT = 9226


class DesktopBridgeError(RuntimeError):
    pass


@dataclass
class DesktopConnection:
    port: int
    cookie: str
    devtools_port: int


@dataclass
class DesktopDelegationResult:
    session_id: str
    workspace_id: str | None
    status: str
    final_text: str
    exit_code: int
    request_path: Path
    events_path: Path
    result_path: Path
    meta_path: Path


class DesktopHostClient:
    def __init__(self, port: int, cookie: str):
        if not isinstance(port, int) or not 1 <= port <= 65535:
            raise ValueError("桌面宿主端口无效")
        if not cookie or "\n" in cookie or "\r" in cookie:
            raise ValueError("桌面认证 cookie 无效")
        self.port = port
        self._cookie = cookie

    @property
    def origin(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def call(self, endpoint: str, method: str, request: dict) -> dict:
        envelope = {
            "type": "client-request",
            "rpcId": str(uuid.uuid4()),
            "method": method,
            "payload": {"args": request},
        }
        payload = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
        http_request = urllib.request.Request(
            f"{self.origin}/api/{endpoint}",
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Cookie": self._cookie,
                "Origin": self.origin,
            },
        )
        try:
            with urllib.request.urlopen(http_request, timeout=30) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise DesktopBridgeError(
                f"桌面宿主 {endpoint} 返回 HTTP {exc.code}"
            ) from exc
        except OSError as exc:
            raise DesktopBridgeError(f"无法连接桌面宿主 {endpoint}: {exc}") from exc

        try:
            result = json.loads(body)
        except json.JSONDecodeError as exc:
            raise DesktopBridgeError(f"桌面宿主 {endpoint} 返回非 JSON 响应") from exc
        if result.get("type") != "server-response":
            raise DesktopBridgeError(f"桌面宿主 {endpoint} 响应格式无效")
        response_value = result.get("result") or {}
        if response_value.get("ok") is not True:
            error = response_value.get("error") or {}
            code = error.get("code", "unknown")
            message = error.get("message", "unknown error")
            raise DesktopBridgeError(f"{endpoint}: {code}: {message}")
        return response_value.get("value") or {}


def _read_cdp_cookies(devtools_port: int) -> list[str]:
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{devtools_port}/json",
            timeout=5,
        ) as response:
            targets = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise DesktopBridgeError(
            "无法连接 DeepSeek Harness 的本地调试端口；"
            "请先运行 `python 01-agent-layer/scripts/dsh_desktop_bridge.py launch`"
        ) from exc

    page = next((target for target in targets if target.get("type") == "page"), None)
    if page is None:
        raise DesktopBridgeError("DeepSeek Harness 没有可控制的页面")

    try:
        import websocket
    except ImportError as exc:
        raise DesktopBridgeError("缺少 websocket-client 依赖") from exc

    connection = websocket.create_connection(
        page["webSocketDebuggerUrl"],
        timeout=10,
        suppress_origin=True,
    )
    try:
        connection.send(json.dumps({"id": 1, "method": "Network.getAllCookies"}))
        while True:
            message = json.loads(connection.recv())
            if message.get("id") == 1:
                cookies = message.get("result", {}).get("cookies", [])
                break
    finally:
        connection.close()

    values = []
    for cookie in cookies:
        name = str(cookie.get("name", ""))
        value = cookie.get("value")
        domain = str(cookie.get("domain", ""))
        if name.startswith("dsh-auth-") and value and domain == "127.0.0.1":
            values.append(f"{name}={value}")
    if not values:
        raise DesktopBridgeError("没有找到 DeepSeek 桌面认证 cookie")
    return values


def _desktop_host_ports(devtools_port: int) -> list[int]:
    try:
        import psutil
    except ImportError as exc:
        raise DesktopBridgeError("缺少 psutil 依赖") from exc

    process_ids = {
        process.pid
        for process in psutil.process_iter(["pid", "name", "exe"])
        if (process.info.get("name") or "") == "DeepSeek Harness.exe"
        or "DeepSeek Harness.exe" in (process.info.get("exe") or "")
    }
    if not process_ids:
        raise DesktopBridgeError("DeepSeek Harness 未运行")

    ports = set()
    for connection in psutil.net_connections(kind="tcp"):
        if connection.status != psutil.CONN_LISTEN:
            continue
        if connection.pid not in process_ids or connection.laddr is None:
            continue
        if connection.laddr.ip != "127.0.0.1":
            continue
        port = int(connection.laddr.port)
        if port != devtools_port:
            ports.add(port)
    if not ports:
        raise DesktopBridgeError("没有找到 DeepSeek 桌面宿主端口")
    return sorted(ports)


def select_authenticated_connection(
    ports: list[int],
    cookies: list[str],
    client_factory=DesktopHostClient,
) -> DesktopConnection:
    last_error: DesktopBridgeError | None = None
    for port in ports:
        for cookie in cookies:
            try:
                client_factory(port, cookie).call(
                    "session/list",
                    "session/list",
                    {"_request": {}},
                )
                return DesktopConnection(
                    port=port,
                    cookie=cookie,
                    devtools_port=DEFAULT_DEVTOOLS_PORT,
                )
            except DesktopBridgeError as exc:
                last_error = exc
    raise DesktopBridgeError(
        f"没有可用的 DeepSeek 桌面宿主认证连接: {last_error or 'unknown'}"
    )


def discover_desktop(
    devtools_port: int = DEFAULT_DEVTOOLS_PORT,
) -> DesktopConnection:
    cookies = _read_cdp_cookies(devtools_port)
    ports = _desktop_host_ports(devtools_port)
    connection = select_authenticated_connection(ports, cookies)
    connection.devtools_port = devtools_port
    return connection


def _safe_label(label: str) -> str:
    cleaned = "".join(
        char if char.isascii() and (char.isalnum() or char == "-") else "-"
        for char in label.strip().lower()
    ).strip("-")
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    if not cleaned:
        raise ValueError("label 仅允许字母、数字和连字符")
    return cleaned


def _last_assistant_text(records: list[dict], after_seq: int) -> str:
    for record in reversed(records):
        event = record.get("event") or {}
        if int(event.get("seq", 0)) <= after_seq:
            continue
        if event.get("type") != "assistant/message":
            continue
        message = (event.get("data") or {}).get("message") or {}
        if message.get("role") != "assistant":
            continue
        parts = []
        for part in message.get("content") or []:
            if part.get("type") == "text" and part.get("text"):
                parts.append(str(part["text"]))
        if parts:
            return "\n".join(parts)
    return ""


def _last_turn_end(records: list[dict], after_seq: int) -> dict | None:
    for record in reversed(records):
        event = record.get("event") or {}
        if int(event.get("seq", 0)) <= after_seq:
            continue
        if event.get("type") == "turn/end":
            return event
    return None


def _append_index(index_path: Path, row: str) -> None:
    if not index_path.exists():
        index_path.write_text(
            "# Delegation Index\n\n"
            "| Time | Label | Session | Status | Result |\n"
            "|---|---|---|---|---|\n",
            encoding="utf-8",
            newline="\n",
        )
    with index_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(row + "\n")


def _cdp_evaluate(devtools_port: int, expression: str) -> str:
    try:
        import websocket
    except ImportError as exc:
        raise DesktopBridgeError("缺少 websocket-client 依赖") from exc
    with urllib.request.urlopen(
        f"http://127.0.0.1:{devtools_port}/json",
        timeout=5,
    ) as response:
        targets = json.loads(response.read().decode("utf-8"))
    page = next((target for target in targets if target.get("type") == "page"), None)
    if page is None:
        raise DesktopBridgeError("DeepSeek Harness 没有可控制的页面")
    connection = websocket.create_connection(
        page["webSocketDebuggerUrl"],
        timeout=10,
        suppress_origin=True,
    )
    try:
        connection.send(
            json.dumps(
                {
                    "id": 1,
                    "method": "Runtime.evaluate",
                    "params": {
                        "expression": expression,
                        "returnByValue": True,
                    },
                }
            )
        )
        while True:
            message = json.loads(connection.recv())
            if message.get("id") == 1:
                return str(message.get("result", {}).get("result", {}).get("value", ""))
    finally:
        connection.close()


def focus_session_in_desktop(
    devtools_port: int,
    workspace_title: str,
    session_title: str,
    timeout: float = 30,
) -> bool:
    expression = f"""(() => {{
      const workspaceTitle = {json.dumps(workspace_title, ensure_ascii=False)};
      const sessionTitle = {json.dumps(session_title, ensure_ascii=False)};
      const rows = [...document.querySelectorAll('[role="treeitem"]')];
      const workspace = rows.find(el => (el.textContent || '').includes(workspaceTitle));
      if (workspace && workspace.getAttribute('aria-expanded') === 'false') {{
        workspace.click();
      }}
      const session = rows.find(el => (el.textContent || '').includes(sessionTitle));
      if (!session) return 'WAITING';
      session.click();
      return 'FOCUSED';
    }})()"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if _cdp_evaluate(devtools_port, expression) == "FOCUSED":
                return True
        except (OSError, DesktopBridgeError):
            pass
        time.sleep(0.5)
    return False


def delegate_desktop(
    client: DesktopHostClient,
    root: Path,
    item_id: str,
    task_file: Path,
    cwd: Path,
    label: str,
    session_id: str | None,
    timeout: float,
    poll_interval: float = 1.0,
    focus_callback: Callable[[str, str], None] | None = None,
) -> DesktopDelegationResult:
    root = Path(root).resolve()
    item_path = root / "02-work-items" / "active" / item_id
    if not item_path.is_dir():
        raise FileNotFoundError(f"找不到活动事项: {item_id}")
    task_file = Path(task_file).resolve()
    if not task_file.is_file():
        raise FileNotFoundError(f"缺少任务单: {task_file}")
    cwd = Path(cwd).resolve()
    if not cwd.is_dir():
        raise FileNotFoundError(f"工作目录不存在: {cwd}")
    label = _safe_label(label)
    task_text = task_file.read_text(encoding="utf-8")

    artifact_dir = item_path / "artifacts" / "delegation"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    prefix = f"{stamp}-{label}"
    request_path = artifact_dir / f"{prefix}-request.md"
    events_path = artifact_dir / f"{prefix}-events.jsonl"
    result_path = artifact_dir / f"{prefix}-result.md"
    meta_path = artifact_dir / f"{prefix}-meta.json"
    request_path.write_text(
        "# DeepSeek Desktop Live Request\n\n"
        f"- Item: `{item_id}`\n"
        f"- CWD: `{cwd}`\n"
        f"- Session: `{session_id or 'new'}`\n"
        f"- Label: `{label}`\n\n"
        "## Task\n\n"
        f"{task_text}",
        encoding="utf-8",
        newline="\n",
    )

    workspace_id: str | None = None
    session_title: str | None = None
    status = "error"
    final_text = ""
    exit_code = 1
    records: list[dict] = []
    initial_seq = 0
    completed_seq: int | None = None
    error_message: str | None = None

    try:
        if session_id is not None:
            initial = client.call(
                "session/projections",
                "session/projections",
                {"request": {"sessionId": session_id}},
            )
            working_directory = (initial.get("values") or {}).get("workingDirectory")
            if working_directory and Path(working_directory).resolve() != cwd:
                raise DesktopBridgeError(
                    f"session cwd 不一致: {working_directory} != {cwd}"
                )
            permission = (
                (initial.get("values") or {}).get("permissions") or {}
            ).get("currentValue")
            if permission == "danger-full-access":
                raise DesktopBridgeError(
                    "拒绝在 danger-full-access 会话中执行桌面委派"
                )
            initial_seq = int(initial.get("asOfSeq", 0))
            session_title = (initial.get("values") or {}).get("title") or session_id
        else:
            workspace_result = client.call(
                "workspace/create",
                "workspace/create",
                {"request": {"path": str(cwd)}},
            )
            workspace = workspace_result.get("workspace") or workspace_result
            workspace_id = workspace.get("workspaceId")
            if not workspace_id:
                raise DesktopBridgeError("workspace/create 没有返回 workspaceId")
            try:
                client.call(
                    "workspace/rename",
                    "workspace/rename",
                    {"request": {"workspaceId": workspace_id, "title": item_id}},
                )
            except DesktopBridgeError:
                pass
            created = client.call(
                "session/create",
                "session/create",
                {
                    "request": {
                        "workspaceId": workspace_id,
                        "sessionId": f"session-{uuid.uuid4()}",
                        "agentPreset": "standard",
                    }
                },
            )
            session_id = created.get("sessionId")
            if not session_id:
                raise DesktopBridgeError("session/create 没有返回 sessionId")
            session_title = f"{item_id} · {label}"
            client.call(
                "session/rename",
                "session/rename",
                {"request": {"sessionId": session_id, "title": session_title}},
            )
            initial = client.call(
                "session/projections",
                "session/projections",
                {"request": {"sessionId": session_id}},
            )
            permission = (
                (initial.get("values") or {}).get("permissions") or {}
            ).get("currentValue")
            if permission == "danger-full-access":
                raise DesktopBridgeError(
                    "新建桌面会话处于 danger-full-access，已拒绝执行"
                )
            initial_seq = int(initial.get("asOfSeq", 0))

        client.call(
            "session/prompt",
            "session/prompt",
            {
                "request": {
                    "requestId": str(uuid.uuid4()),
                    "sessionId": session_id,
                    "mode": "queue",
                    "content": [{"type": "text", "text": task_text}],
                    "clientTimeZone": "Asia/Shanghai",
                }
            },
        )
        if focus_callback is not None and session_title:
            try:
                focus_callback(item_id, session_title)
            except Exception:
                pass

        deadline = time.monotonic() + timeout
        while True:
            projection = client.call(
                "session/projections",
                "session/projections",
                {"request": {"sessionId": session_id}},
            )
            as_of_seq = int(projection.get("asOfSeq", 0))
            if as_of_seq > initial_seq:
                page = client.call(
                    "session/page",
                    "session/page",
                    {
                        "request": {
                            "address": {"kind": "session", "sessionId": session_id},
                            "throughSeq": as_of_seq,
                            "maxMessages": 200,
                        }
                    },
                )
                records = page.get("records") or []
                turn_end = _last_turn_end(records, initial_seq)
                if turn_end is not None:
                    completed_seq = int(turn_end.get("seq", as_of_seq))
                    final_text = _last_assistant_text(records, initial_seq)
                    reason = (turn_end.get("data") or {}).get("reason") or {}
                    if reason.get("kind") == "completed":
                        status = "completed"
                        exit_code = 0
                    else:
                        status = "error"
                        exit_code = 1
                        error_message = str(reason)
                    break
            if time.monotonic() >= deadline:
                status = "timeout"
                exit_code = 124
                error_message = "timeout waiting for new turn/end"
                break
            time.sleep(poll_interval)
    except DesktopBridgeError as exc:
        error_message = str(exc)
        status = "error"
        exit_code = 1
        session_id = session_id or ""

    with events_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    result_path.write_text(
        f"# DeepSeek Desktop Result\n\n"
        f"- Status: `{status}`\n"
        f"- Session: `{session_id or ''}`\n"
        f"- Workspace: `{workspace_id or ''}`\n"
        f"- Exit code: `{exit_code}`\n\n"
        "## Final\n\n"
        f"{final_text or '_没有最终文本_'}\n\n"
        "## Diagnostics\n\n"
        f"{error_message or '_无_'}\n",
        encoding="utf-8",
        newline="\n",
    )
    meta = {
        "item_id": item_id,
        "label": label,
        "backend": "desktop-live",
        "desktop_host_port": client.port,
        "workspace_id": workspace_id,
        "session_id": session_id,
        "cwd": str(cwd),
        "status": status,
        "exit_code": exit_code,
        "initial_seq": initial_seq,
        "completed_seq": completed_seq,
        "error": error_message,
        "request_path": str(request_path),
        "events_path": str(events_path),
        "result_path": str(result_path),
        "finished_at": datetime.now().isoformat(timespec="seconds"),
    }
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _append_index(
        artifact_dir / "INDEX.md",
        f"| {stamp} | {label} | {session_id or '-'} | {status} | "
        f"[{result_path.name}]({result_path.name}) |",
    )
    return DesktopDelegationResult(
        session_id=session_id or "",
        workspace_id=workspace_id,
        status=status,
        final_text=final_text,
        exit_code=exit_code,
        request_path=request_path,
        events_path=events_path,
        result_path=result_path,
        meta_path=meta_path,
    )


def launch_desktop(
    dsh_exe: Path = DEFAULT_DSH_EXE,
    devtools_port: int = DEFAULT_DEVTOOLS_PORT,
) -> None:
    if not dsh_exe.is_file():
        raise FileNotFoundError(f"找不到 DeepSeek Harness: {dsh_exe}")
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{devtools_port}/json",
            timeout=2,
        ):
            return
    except OSError:
        pass

    if any(
        process.info.get("name") == "DeepSeek Harness.exe"
        for process in __import__("psutil").process_iter(["name"])
    ):
        raise DesktopBridgeError(
            "DeepSeek Harness 已用普通模式运行；请关闭后重新执行 launch"
        )

    subprocess.Popen(
        [str(dsh_exe), f"--remote-debugging-port={devtools_port}"],
    )
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{devtools_port}/json",
                timeout=1,
            ):
                return
        except OSError:
            time.sleep(0.5)
    raise DesktopBridgeError("DeepSeek Harness 启动后没有开放本地调试端口")


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (OSError, ValueError):
                pass


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Codex → DeepSeek 桌面实时桥")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--devtools-port", type=int, default=DEFAULT_DEVTOOLS_PORT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("launch", help="以实时控制模式启动桌面 app")
    subparsers.add_parser("doctor", help="检查桌面 app 实时连接")

    delegate_parser = subparsers.add_parser("delegate", help="在桌面 app 中创建可见会话")
    delegate_parser.add_argument("--item", required=True)
    delegate_parser.add_argument("--task-file", type=Path, required=True)
    delegate_parser.add_argument("--cwd", type=Path, required=True)
    delegate_parser.add_argument("--label", default="implement")
    delegate_parser.add_argument("--session-id")
    delegate_parser.add_argument("--timeout", type=float, default=3600)
    delegate_parser.add_argument("--poll-interval", type=float, default=1.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    _configure_utf8_stdio()
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "launch":
            launch_desktop(devtools_port=args.devtools_port)
            print("DEEPSEEK_DESKTOP_LIVE: ready")
            return 0

        connection = discover_desktop(args.devtools_port)
        if args.command == "doctor":
            print(f"DESKTOP_HOST_PORT: {connection.port}")
            print("DESKTOP_CDP_OK: yes")
            print("DESKTOP_HOST_OK: yes")
            return 0

        result = delegate_desktop(
            client=DesktopHostClient(connection.port, connection.cookie),
            root=args.root,
            item_id=args.item,
            task_file=args.task_file,
            cwd=args.cwd,
            label=args.label,
            session_id=args.session_id,
            timeout=args.timeout,
            poll_interval=args.poll_interval,
            focus_callback=lambda workspace, session: focus_session_in_desktop(
                args.devtools_port,
                workspace,
                session,
            ),
        )
        print(f"SESSION_ID: {result.session_id}")
        print(f"WORKSPACE_ID: {result.workspace_id or '-'}")
        print(f"STATUS: {result.status}")
        print(f"EXIT_CODE: {result.exit_code}")
        print(f"RESULT: {result.result_path}")
        print(f"META: {result.meta_path}")
        return 0 if result.status == "completed" else 1
    except (OSError, ValueError, DesktopBridgeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

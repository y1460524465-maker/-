from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DSH = Path(
    r"D:\Apps\DeepSeek Harness\resources\runtime\cli\bin\dsh.cmd"
)
DEFAULT_PATCH = (
    REPO_ROOT / "01-agent-layer" / "tools" / "dsh" / "headless-codex.patch.yml"
)
ALLOWED_PERMISSION_MODES = {"read-only", "workspace-write"}
SECRET_ENV_RE = re.compile(
    r"(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)",
    re.IGNORECASE,
)


@dataclass
class DelegationResult:
    session_id: str | None
    status: str
    final_text: str
    exit_code: int
    request_path: Path
    events_path: Path
    result_path: Path
    meta_path: Path


def build_command(
    dsh: Path,
    patch: Path,
    session_id: str | None = None,
) -> list[str]:
    command = [
        str(dsh),
        "--profile",
        "headless",
        "--patch",
        str(patch),
        "--json",
    ]
    if session_id:
        command.extend(["--session-id", session_id])
    command.append("-")
    return command


def _safe_label(label: str) -> str:
    cleaned = re.sub(r"[^a-z0-9-]+", "-", label.strip().lower()).strip("-")
    if not cleaned:
        raise ValueError("label 仅允许小写字母、数字和连字符")
    return cleaned


def _child_environment(permission_mode: str) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not SECRET_ENV_RE.search(key)
    }
    environment["DSH_PERMISSION_MODE"] = permission_mode
    environment["PYTHONIOENCODING"] = "utf-8"
    return environment


def _git_head(cwd: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def _parse_events(stdout: str) -> tuple[str | None, str, str | None]:
    session_id: str | None = None
    final_text = ""
    error_message: str | None = None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "session" and event.get("sessionId"):
            session_id = str(event["sessionId"])
        if event.get("type") == "final":
            final_text = str(event.get("text", ""))
        if event.get("type") == "status" and event.get("phase") == "turn_end":
            reason = event.get("reason") or {}
            if reason.get("kind") == "error":
                error = reason.get("error") or {}
                error_message = str(error.get("message", "unknown error"))
    return session_id, final_text, error_message


def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            check=False,
        )
        return
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except (OSError, ProcessLookupError):
        process.kill()


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


def delegate_item(
    root: Path,
    item_id: str,
    task_file: Path,
    cwd: Path,
    label: str,
    session_id: str | None,
    permission_mode: str,
    timeout: float,
    dsh: Path,
    patch: Path,
) -> DelegationResult:
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
    if permission_mode not in ALLOWED_PERMISSION_MODES:
        raise ValueError("权限模式只能是 read-only 或 workspace-write")
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
        "# DeepSeek Delegation Request\n\n"
        f"- Item: `{item_id}`\n"
        f"- CWD: `{cwd}`\n"
        f"- Permission mode: `{permission_mode}`\n"
        f"- Session: `{session_id or 'new'}`\n"
        f"- Label: `{label}`\n\n"
        "## Task\n\n"
        f"{task_text}",
        encoding="utf-8",
        newline="\n",
    )

    command = build_command(dsh, patch, session_id)
    head_before = _git_head(cwd)
    creationflags = (
        subprocess.CREATE_NEW_PROCESS_GROUP
        if os.name == "nt" and hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP")
        else 0
    )
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        env=_child_environment(permission_mode),
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=creationflags,
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(input=task_text, timeout=timeout)
        exit_code = process.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        _terminate_process_tree(process)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
        stdout = _as_text(exc.stdout)
        stderr = _as_text(exc.stderr)
        exit_code = 124
    head_after = _git_head(cwd)
    events_path.write_text(stdout, encoding="utf-8", newline="\n")
    parsed_session, final_text, error_message = _parse_events(stdout)
    session_id = parsed_session or session_id
    if timed_out:
        status = "timeout"
    elif error_message or exit_code != 0:
        status = "error"
    elif head_before and head_after and head_before != head_after:
        status = "policy_violation"
    elif final_text:
        status = "completed"
    else:
        status = "incomplete"
    result_path.write_text(
        f"# DeepSeek Result\n\n"
        f"- Status: `{status}`\n"
        f"- Session: `{session_id or ''}`\n"
        f"- Exit code: `{exit_code}`\n\n"
        "## Final\n\n"
        f"{final_text or '_没有 final 事件_'}\n\n"
        "## Diagnostics\n\n"
        f"{stderr or error_message or '_无_'}\n",
        encoding="utf-8",
        newline="\n",
    )
    meta = {
        "item_id": item_id,
        "label": label,
        "cwd": str(cwd),
        "permission_mode": permission_mode,
        "session_id": session_id,
        "status": status,
        "exit_code": exit_code,
        "error": error_message,
        "git_head_before": head_before,
        "git_head_after": head_after,
        "git_head_changed": bool(
            head_before and head_after and head_before != head_after
        ),
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
    return DelegationResult(
        session_id=session_id,
        status=status,
        final_text=final_text,
        exit_code=exit_code,
        request_path=request_path,
        events_path=events_path,
        result_path=result_path,
        meta_path=meta_path,
    )


def doctor(dsh: Path, patch: Path) -> dict[str, object]:
    dsh = Path(dsh)
    patch = Path(patch)
    return {
        "dsh": str(dsh),
        "dsh_ok": dsh.is_file(),
        "patch": str(patch),
        "patch_ok": patch.is_file(),
        "permission_mode": "workspace-write",
    }


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (OSError, ValueError):
                pass


def _add_runtime_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dsh", type=Path, default=DEFAULT_DSH)
    parser.add_argument("--patch", type=Path, default=DEFAULT_PATCH)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Codex → DeepSeek Harness 委派桥")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subparsers.add_parser("doctor", help="检查 dsh 和 patch")
    _add_runtime_options(doctor_parser)

    delegate_parser = subparsers.add_parser("delegate", help="提交一轮实现任务")
    _add_runtime_options(delegate_parser)
    delegate_parser.add_argument("--item", required=True)
    delegate_parser.add_argument("--task-file", type=Path, required=True)
    delegate_parser.add_argument("--cwd", type=Path, required=True)
    delegate_parser.add_argument("--label", default="implement")
    delegate_parser.add_argument("--session-id")
    delegate_parser.add_argument(
        "--permission-mode",
        choices=sorted(ALLOWED_PERMISSION_MODES),
        default="workspace-write",
    )
    delegate_parser.add_argument("--timeout", type=float, default=3600)
    return parser


def main(argv: list[str] | None = None) -> int:
    _configure_utf8_stdio()
    args = _build_parser().parse_args(argv)
    if args.command == "doctor":
        report = doctor(args.dsh, args.patch)
        print(f"DSH_CLI: {report['dsh']}")
        print(f"DSH_CLI_OK: {'yes' if report['dsh_ok'] else 'no'}")
        print(f"PATCH: {report['patch']}")
        print(f"PATCH_OK: {'yes' if report['patch_ok'] else 'no'}")
        return 0 if report["dsh_ok"] and report["patch_ok"] else 1

    try:
        result = delegate_item(
            root=args.root,
            item_id=args.item,
            task_file=args.task_file,
            cwd=args.cwd,
            label=args.label,
            session_id=args.session_id,
            permission_mode=args.permission_mode,
            timeout=args.timeout,
            dsh=args.dsh,
            patch=args.patch,
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"SESSION_ID: {result.session_id or '-'}")
    print(f"STATUS: {result.status}")
    print(f"EXIT_CODE: {result.exit_code}")
    print(f"RESULT: {result.result_path}")
    print(f"META: {result.meta_path}")
    print(f"EVENTS: {result.events_path}")
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

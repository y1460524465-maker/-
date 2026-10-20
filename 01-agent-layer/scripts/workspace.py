from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date as calendar_date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_CONFIG_NAME = ".ai-workspace.json"
PROJECT_CONFIG_SCHEMA_VERSION = 1
ITEM_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ITEM_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
ACTIVE_INDEX_START = "<!-- ACTIVE_ITEMS_START -->"
ACTIVE_INDEX_END = "<!-- ACTIVE_ITEMS_END -->"
ARCHIVED_INDEX_START = "<!-- ARCHIVED_ITEMS_START -->"
ARCHIVED_INDEX_END = "<!-- ARCHIVED_ITEMS_END -->"
ADAPTER_START = "<!-- canonical-adapter:start -->"
ADAPTER_END = "<!-- canonical-adapter:end -->"
ADAPTER_BODY = (
    "Read `01-agent-layer/AGENT_GUIDE.md` before any task action and follow it "
    "as the canonical workspace policy. This file is only an entry adapter; "
    "do not add workspace rules here."
)
ADAPTER_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".cursor/rules/agent-guide.mdc",
    ".github/copilot-instructions.md",
]
ALLOWED_STATUSES = {"planning", "active", "blocked", "review", "done", "archived"}
STATUS_HEADINGS = [
    "已完成",
    "正在做",
    "下一步",
    "阻塞与待确认",
    "最近验证",
    "当前边界与有效不变量",
]
HANDOFF_HEADINGS = [
    "唯一下一步",
    "必读顺序",
    "已完成，不要重复",
    "已知坑与禁止动作",
    "可直接运行的验证",
]
BRIEF_HEADINGS = [
    "用户原始要求",
    "目标",
    "验收标准",
    "范围",
    "非目标",
    "约束",
    "开放问题",
]
REQUIRED_ROOT_FILES = [
    PROJECT_CONFIG_NAME,
    "01-agent-layer/AGENT_GUIDE.md",
    "02-work-items/WORK_INDEX.md",
    "01-agent-layer/router/context-router.md",
    "01-agent-layer/core/invariants.md",
    "01-agent-layer/core/state-contract.md",
    "01-agent-layer/core/git-protocol.md",
    "01-agent-layer/contexts/coding.md",
    "01-agent-layer/contexts/delegation.md",
    "01-agent-layer/contexts/codex-review.md",
    "01-agent-layer/contexts/sync.md",
    "01-agent-layer/githooks/pre-commit",
    "01-agent-layer/scripts/workspace.py",
    "03-session-state/knowledge/INDEX.md",
    "01-agent-layer/templates/work-item/state/STATUS.md",
    "01-agent-layer/templates/work-item/state/handoff.md",
    "01-agent-layer/templates/work-item/work/brief.md",
] + ADAPTER_FILES
REQUIRED_WORK_FILES = ["brief.md"]
REQUIRED_WORK_DIRS = ["workspaces", "drafts", "artifacts", "reviews", "archive"]
REQUIRED_STATE_FILES = ["STATUS.md", "handoff.md", "decisions.md"]
REQUIRED_STATE_DIRS = [
    "journal",
    "knowledge",
]
PLACEHOLDER_RE = re.compile(r"\{\{[^{}\n]+\}\}")
PLACEHOLDER_EXCLUDED_DIRS = {
    ".git",
    ".tools",
    ".venv",
    "node_modules",
    "vendor",
    "venv",
}


def load_project_config(root: Path) -> dict[str, object]:
    path = Path(root) / PROJECT_CONFIG_NAME
    if not path.is_file():
        raise ValueError(f"缺少 {PROJECT_CONFIG_NAME}")
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{PROJECT_CONFIG_NAME} 不是有效 JSON: {exc}") from exc
    if not isinstance(config, dict):
        raise ValueError(f"{PROJECT_CONFIG_NAME} 顶层必须是对象")

    schema_version = config.get("schemaVersion")
    if schema_version != PROJECT_CONFIG_SCHEMA_VERSION:
        raise ValueError(
            f"{PROJECT_CONFIG_NAME} schemaVersion 必须为 "
            f"{PROJECT_CONFIG_SCHEMA_VERSION}"
        )
    mode = config.get("mode")
    if mode not in {"shared-kit", "project"}:
        raise ValueError(f"{PROJECT_CONFIG_NAME} mode 必须为 shared-kit 或 project")
    if not isinstance(config.get("name"), str) or not config["name"].strip():
        raise ValueError(f"{PROJECT_CONFIG_NAME} name 不能为空")

    if mode == "project":
        shared_value = config.get("sharedAgentLayer")
        if not isinstance(shared_value, str) or not shared_value.strip():
            raise ValueError(f"{PROJECT_CONFIG_NAME} project 模式缺少 sharedAgentLayer")
        shared_root = Path(shared_value)
        if not (shared_root / "AGENT_GUIDE.md").is_file():
            raise ValueError(f"{PROJECT_CONFIG_NAME} sharedAgentLayer 无效: {shared_root}")
        project_layer = Path(root) / "01-agent-layer"
        if not project_layer.is_dir():
            raise ValueError("project 模式缺少 01-agent-layer")
        if project_layer.resolve() != shared_root.resolve():
            raise ValueError(
                f"{PROJECT_CONFIG_NAME} sharedAgentLayer 与 01-agent-layer 目标不一致"
            )
    return config


def discover_project_root(start: Path | None = None) -> Path:
    current = Path(start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (
            (candidate / PROJECT_CONFIG_NAME).is_file()
            and (candidate / "02-work-items" / "WORK_INDEX.md").is_file()
            and (candidate / "03-session-state").is_dir()
        ):
            return candidate
    return REPO_ROOT


def resolve_project_root(
    explicit_root: Path | None = None,
    start: Path | None = None,
) -> Path:
    if explicit_root is not None:
        return Path(explicit_root).resolve()
    return discover_project_root(start).resolve()


def _clean_title(title: str) -> str:
    cleaned = " ".join(title.split())
    if not cleaned:
        raise ValueError("标题不能为空")
    return cleaned


def _validate_slug(slug: str) -> str:
    if not isinstance(slug, str) or not ITEM_SLUG_RE.fullmatch(slug):
        raise ValueError("slug 仅允许小写字母、数字和单个连字符，且不能为空")
    return slug


def _validate_workspaces(workspaces: list[str] | None) -> list[str]:
    names = ["main"] if not workspaces else list(workspaces)
    seen: set[str] = set()
    for name in names:
        if not isinstance(name, str) or not ITEM_SLUG_RE.fullmatch(name):
            raise ValueError("工作区名称仅允许小写字母、数字和连字符")
        if name in seen:
            raise ValueError(f"工作区名称重复: {name}")
        seen.add(name)
    return names


def _render(text: str, *, item_id: str, title: str, date: str, stream: str = "") -> str:
    yaml_title = title.replace("\\", "\\\\").replace('"', '\\"')
    return (
        text.replace("{{ID}}", item_id)
        .replace("{{TITLE_YAML}}", yaml_title)
        .replace("{{TITLE}}", title)
        .replace("{{DATE}}", date)
        .replace("{{STREAM}}", stream)
    )


def _markdown_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|")


def _register_active_item(root: Path, item_id: str, title: str, date: str) -> None:
    index_path = root / "02-work-items" / "WORK_INDEX.md"
    if not index_path.is_file():
        raise FileNotFoundError(f"缺少索引文件: {index_path}")

    index = index_path.read_text(encoding="utf-8")
    start = index.find(ACTIVE_INDEX_START)
    end = index.find(ACTIVE_INDEX_END)
    if start < 0 or end < 0 or end < start:
        raise ValueError("02-work-items/WORK_INDEX.md 缺少活动事项标记")

    block = index[start:end]
    if item_id in block:
        raise ValueError(f"事项已在索引中登记: {item_id}")

    row = (
        f"| {item_id} | {_markdown_cell(title)} | planning | {date} | "
        f"`02-work-items/active/{item_id}/` | "
        f"`03-session-state/active/{item_id}/` |"
    )
    before = index[:start]
    content = index[start + len(ACTIVE_INDEX_START) : end].rstrip("\n")
    after = index[end + len(ACTIVE_INDEX_END) :]
    updated = (
        before
        + ACTIVE_INDEX_START
        + content
        + "\n"
        + row
        + "\n"
        + ACTIVE_INDEX_END
        + after
    )
    index_path.write_text(updated, encoding="utf-8", newline="\n")


def create_item(
    root: Path,
    slug: str,
    title: str,
    workspaces: list[str] | None = None,
    date: str | None = None,
) -> Path:
    root = Path(root).resolve()
    slug = _validate_slug(slug)
    title = _clean_title(title)
    workspace_names = _validate_workspaces(workspaces)
    date_text = date or calendar_date.today().isoformat()
    try:
        calendar_date.fromisoformat(date_text)
    except ValueError as exc:
        raise ValueError("日期必须使用 YYYY-MM-DD 格式") from exc

    template_root = root / "01-agent-layer" / "templates" / "work-item"
    work_template = template_root / "work"
    state_template = template_root / "state"
    if not work_template.is_dir() or not state_template.is_dir():
        raise FileNotFoundError(f"缺少事项模板: {template_root}")

    item_id = f"{date_text}-{slug}"
    work_active_root = root / "02-work-items" / "active"
    state_active_root = root / "03-session-state" / "active"
    target = work_active_root / item_id
    state_target = state_active_root / item_id
    if target.exists() or state_target.exists():
        raise ValueError(f"事项已存在: {item_id}")

    work_active_root.mkdir(parents=True, exist_ok=True)
    state_active_root.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copytree(work_template, target)
        shutil.copytree(state_template, state_target)

        stream_template = target / "workspaces" / "_stream"
        for path in sorted(target.rglob("*.md")):
            if stream_template in path.parents:
                continue
            text = path.read_text(encoding="utf-8")
            path.write_text(
                _render(text, item_id=item_id, title=title, date=date_text),
                encoding="utf-8",
                newline="\n",
            )

        for path in sorted(state_target.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            path.write_text(
                _render(text, item_id=item_id, title=title, date=date_text),
                encoding="utf-8",
                newline="\n",
            )

        journal_template = state_target / "journal" / "YYYY-MM-DD.md"
        if journal_template.exists():
            journal_template.rename(
                state_target / "journal" / f"{date_text}.md"
            )

        if not stream_template.is_dir():
            raise FileNotFoundError("事项模板缺少 workspaces/_stream")
        for stream in workspace_names:
            destination = target / "workspaces" / stream
            shutil.copytree(stream_template, destination)
            for path in destination.rglob("*.md"):
                text = path.read_text(encoding="utf-8")
                path.write_text(
                    _render(
                        text,
                        item_id=item_id,
                        title=title,
                        date=date_text,
                        stream=stream,
                    ),
                    encoding="utf-8",
                    newline="\n",
                )
        shutil.rmtree(stream_template)

        _register_active_item(root, item_id, title, date_text)
    except Exception:
        if target.exists():
            shutil.rmtree(target)
        if state_target.exists():
            shutil.rmtree(state_target)
        raise

    return target


def _parse_modes(mode: str) -> list[str]:
    if not isinstance(mode, str) or not mode.strip():
        raise ValueError("场景模式不能为空")
    names = [name.strip() for name in mode.split(",") if name.strip()]
    if "auto" in names and len(names) > 1:
        raise ValueError("auto 不能与其他场景组合使用")
    allowed = {"auto", "coding", "delegation", "review", "sync"}
    unknown = [name for name in names if name not in allowed]
    if unknown:
        raise ValueError(f"未知场景: {', '.join(unknown)}")
    return list(dict.fromkeys(names))


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def context_manifest(root: Path, item_id: str, mode: str = "auto") -> dict[str, list[str]]:
    root = Path(root).resolve()
    if not isinstance(item_id, str) or not ITEM_ID_RE.fullmatch(item_id):
        raise ValueError("事项 ID 格式无效，应为 YYYY-MM-DD-slug")

    work_path = root / "02-work-items" / "active" / item_id
    state_path = root / "03-session-state" / "active" / item_id
    if not work_path.is_dir() or not state_path.is_dir():
        raise FileNotFoundError(f"找不到活动事项: {item_id}")

    modes = _parse_modes(mode)
    latest_journal = ""
    journal_dir = state_path / "journal"
    journal_files = sorted(journal_dir.glob("*.md")) if journal_dir.is_dir() else []
    if journal_files:
        latest_journal = _relative(root, journal_files[-1])

    item_state = [
        _relative(root, state_path / "STATUS.md"),
        _relative(root, state_path / "handoff.md"),
        _relative(root, work_path / "brief.md"),
    ]
    if latest_journal:
        item_state.append(latest_journal)

    scenario: list[str] = []
    for name in modes:
        if name == "auto":
            continue
        filename = "codex-review.md" if name == "review" else f"{name}.md"
        path = f"01-agent-layer/contexts/{filename}"
        if path not in scenario:
            scenario.append(path)

    return {
        "always_load": [
            "01-agent-layer/AGENT_GUIDE.md",
            "01-agent-layer/core/invariants.md",
            "01-agent-layer/router/context-router.md",
        ],
        "item_state": item_state,
        "scenario": scenario,
        "load_on_demand": [
            _relative(root, state_path / "decisions.md"),
            _relative(root, state_path / "knowledge" / "README.md"),
            _relative(root, work_path / "artifacts" / "README.md"),
            _relative(root, work_path / "reviews" / "README.md"),
            _relative(root, work_path / "workspaces" / "README.md"),
        ],
    }


def _has_heading(text: str, heading: str) -> bool:
    return re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE) is not None


def _validate_headings(path: Path, headings: list[str], errors: list[str]) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    for heading in headings:
        if not _has_heading(text, heading):
            errors.append(f"{path}: 缺少标题 ## {heading}")


def _parse_front_matter(path: Path, errors: list[str]) -> dict[str, str]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        errors.append(f"{path}: 缺少 YAML front matter")
        return {}
    try:
        end = lines.index("---", 1)
    except ValueError:
        errors.append(f"{path}: YAML front matter 未闭合")
        return {}

    fields: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        fields[key.strip()] = value
    return fields


def _validate_adapter(path: Path, root: Path, errors: list[str]) -> None:
    if not path.is_file():
        return
    relative = _relative(root, path)
    text = path.read_text(encoding="utf-8")
    if text.count(ADAPTER_START) != 1 or text.count(ADAPTER_END) != 1:
        errors.append(f"{relative}: 适配器必须包含一对规范标记")
        return

    start = text.index(ADAPTER_START)
    end = text.index(ADAPTER_END)
    if end < start:
        errors.append(f"{relative}: 适配器规范标记顺序错误")
        return

    body = text[start + len(ADAPTER_START) : end].strip()
    if body != ADAPTER_BODY:
        errors.append(f"{relative}: 适配器规范正文与统一入口不一致")

    outside = text[:start] + text[end + len(ADAPTER_END) :]
    if outside.startswith("---"):
        lines = outside.splitlines()
        try:
            front_matter_end = lines.index("---", 1)
            outside = "\n".join(lines[front_matter_end + 1 :])
        except ValueError:
            pass
    extra_lines = [
        line
        for line in outside.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if extra_lines:
        errors.append(f"{relative}: 适配器包含额外规则，统一入口已分叉")


def _validate_item_structure(
    work_path: Path,
    state_path: Path,
    root: Path,
    errors: list[str],
) -> dict[str, str]:
    work_relative = _relative(root, work_path)
    state_relative = _relative(root, state_path)
    for filename in REQUIRED_WORK_FILES:
        path = work_path / filename
        if not path.is_file():
            errors.append(f"{work_relative}/{filename}: 缺少必需文件")
    for dirname in REQUIRED_WORK_DIRS:
        path = work_path / dirname
        if not path.is_dir():
            errors.append(f"{work_relative}/{dirname}: 缺少必需目录")
    for filename in REQUIRED_STATE_FILES:
        path = state_path / filename
        if not path.is_file():
            errors.append(f"{state_relative}/{filename}: 缺少必需文件")
    for dirname in REQUIRED_STATE_DIRS:
        path = state_path / dirname
        if not path.is_dir():
            errors.append(f"{state_relative}/{dirname}: 缺少必需目录")

    status_path = state_path / "STATUS.md"
    fields = _parse_front_matter(status_path, errors)
    if fields:
        for key in ["id", "title", "status", "updated", "owner"]:
            if not fields.get(key):
                errors.append(f"{status_path}: front matter 缺少 {key}")
        if fields.get("id") and fields["id"] != work_path.name:
            errors.append(f"{status_path}: id 与工作目录名不一致")
        if fields.get("title") is not None and not fields.get("title"):
            errors.append(f"{status_path}: title 不能为空")
        if fields.get("status") and fields["status"] not in ALLOWED_STATUSES:
            errors.append(f"{status_path}: 未知状态 {fields['status']}")
        if fields.get("updated"):
            try:
                calendar_date.fromisoformat(fields["updated"])
            except ValueError:
                errors.append(f"{status_path}: updated 必须使用 YYYY-MM-DD")

    _validate_headings(status_path, STATUS_HEADINGS, errors)
    _validate_headings(state_path / "handoff.md", HANDOFF_HEADINGS, errors)
    _validate_headings(work_path / "brief.md", BRIEF_HEADINGS, errors)

    journal_dir = state_path / "journal"
    if journal_dir.is_dir() and not list(journal_dir.glob("*.md")):
        errors.append(f"{state_relative}/journal: 至少需要一个过程记录文件")
    workspaces_dir = work_path / "workspaces"
    if workspaces_dir.is_dir():
        stream_dirs = [path for path in workspaces_dir.iterdir() if path.is_dir()]
        if not stream_dirs:
            errors.append(f"{work_relative}/workspaces: 至少需要一个隔离工作区")
        for stream_dir in stream_dirs:
            if not (stream_dir / "README.md").is_file():
                errors.append(
                    f"{_relative(root, stream_dir)}/README.md: 工作区缺少说明文件"
                )

    reviews_dir = work_path / "reviews"
    if reviews_dir.is_dir():
        for task_path in sorted(reviews_dir.iterdir()):
            if task_path.is_file():
                if task_path.name != "README.md":
                    errors.append(
                        f"{_relative(root, task_path)}: 审查证据必须放入 "
                        "reviews/<task-id>/round-N/"
                    )
                continue
            if not ITEM_SLUG_RE.fullmatch(task_path.name):
                errors.append(
                    f"{_relative(root, task_path)}: 审查任务目录名必须是 slug"
                )
                continue
            for round_path in sorted(task_path.iterdir()):
                if not round_path.is_dir() or not re.fullmatch(
                    r"round-[1-9]\d*",
                    round_path.name,
                ):
                    errors.append(
                        f"{_relative(root, round_path)}: 审查轮次必须是 round-N"
                    )
                    continue
                if not (round_path / "review.md").is_file():
                    errors.append(
                        f"{_relative(root, round_path)}/review.md: 缺少审查报告"
                    )

    for item_path in (work_path, state_path):
        for path in item_path.rglob("*.md"):
            relative_parts = path.relative_to(item_path).parts
            if any(part in PLACEHOLDER_EXCLUDED_DIRS for part in relative_parts):
                continue
            text = path.read_text(encoding="utf-8")
            match = PLACEHOLDER_RE.search(text)
            if match:
                errors.append(
                    f"{_relative(root, path)}: 存在未替换占位符 {match.group(0)}"
                )
    return fields


def _index_rows(index: str, start_marker: str, end_marker: str) -> tuple[str, list[str]]:
    start = index.find(start_marker)
    end = index.find(end_marker)
    if start < 0 or end < 0 or end < start:
        return "", []
    block = index[start + len(start_marker) : end]
    ids = re.findall(
        r"^\|\s*(\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*)\s*\|",
        block,
        re.MULTILINE,
    )
    return block, ids


def _active_index_rows(index: str) -> tuple[str, list[str]]:
    return _index_rows(index, ACTIVE_INDEX_START, ACTIVE_INDEX_END)


def _archived_index_rows(index: str) -> tuple[str, list[str]]:
    return _index_rows(index, ARCHIVED_INDEX_START, ARCHIVED_INDEX_END)


def _markdown_row_cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", stripped)[1:-1]]


def validate_workspace(root: Path) -> list[str]:
    root = Path(root).resolve()
    errors: list[str] = []

    for relative in REQUIRED_ROOT_FILES:
        if not (root / relative).is_file():
            errors.append(f"{relative}: 缺少必需文件")
    for relative in [
        "01-agent-layer/templates/work-item",
        "02-work-items/active",
        "02-work-items/archived",
        "03-session-state/active",
        "03-session-state/archived",
        "03-session-state/knowledge",
    ]:
        if not (root / relative).is_dir():
            errors.append(f"{relative}: 缺少必需目录")

    for adapter in ADAPTER_FILES:
        _validate_adapter(root / adapter, root, errors)

    try:
        load_project_config(root)
    except (OSError, ValueError) as exc:
        errors.append(f"{PROJECT_CONFIG_NAME}: {exc}")

    _validate_headings(
        root / "01-agent-layer" / "templates" / "work-item" / "state" / "STATUS.md",
        STATUS_HEADINGS,
        errors,
    )
    _validate_headings(
        root / "01-agent-layer" / "templates" / "work-item" / "state" / "handoff.md",
        HANDOFF_HEADINGS,
        errors,
    )
    _validate_headings(
        root / "01-agent-layer" / "templates" / "work-item" / "work" / "brief.md",
        BRIEF_HEADINGS,
        errors,
    )

    active_work_root = root / "02-work-items" / "active"
    active_state_root = root / "03-session-state" / "active"
    active_items: dict[str, Path] = {}
    active_fields: dict[str, dict[str, str]] = {}
    if active_work_root.is_dir():
        for work_path in sorted(active_work_root.iterdir()):
            if not work_path.is_dir():
                continue
            if not ITEM_ID_RE.fullmatch(work_path.name):
                errors.append(
                    f"02-work-items/active/{work_path.name}: 事项目录名不符合 YYYY-MM-DD-slug"
                )
                continue
            state_path = active_state_root / work_path.name
            if not state_path.is_dir():
                errors.append(
                    f"03-session-state/active/{work_path.name}: 缺少配对状态目录"
                )
                continue
            active_items[work_path.name] = work_path
            active_fields[work_path.name] = _validate_item_structure(
                work_path,
                state_path,
                root,
                errors,
            )
    if active_state_root.is_dir():
        for state_path in sorted(active_state_root.iterdir()):
            if state_path.is_dir() and state_path.name not in active_items:
                errors.append(
                    f"03-session-state/active/{state_path.name}: 缺少配对工作目录"
                )

    archive_work_root = root / "02-work-items" / "archived"
    archive_state_root = root / "03-session-state" / "archived"
    archived_items: set[str] = set()
    if archive_work_root.is_dir():
        for work_path in sorted(archive_work_root.iterdir()):
            if not work_path.is_dir():
                continue
            if not ITEM_ID_RE.fullmatch(work_path.name):
                errors.append(
                    f"02-work-items/archived/{work_path.name}: 事项目录名不符合 YYYY-MM-DD-slug"
                )
                continue
            state_path = archive_state_root / work_path.name
            if not state_path.is_dir():
                errors.append(
                    f"03-session-state/archived/{work_path.name}: 缺少配对状态目录"
                )
                continue
            archived_items.add(work_path.name)
            _validate_item_structure(
                work_path,
                state_path,
                root,
                errors,
            )
    if archive_state_root.is_dir():
        for state_path in sorted(archive_state_root.iterdir()):
            if state_path.is_dir() and state_path.name not in archived_items:
                errors.append(
                    f"03-session-state/archived/{state_path.name}: 缺少配对工作目录"
                )

    duplicates = sorted(set(active_items) & archived_items)
    for item_id in duplicates:
        errors.append(f"{item_id}: 同时存在于活动和归档目录")

    index_path = root / "02-work-items" / "WORK_INDEX.md"
    if index_path.is_file():
        index = index_path.read_text(encoding="utf-8")
        block, row_ids = _active_index_rows(index)
        if not block:
            errors.append("02-work-items/WORK_INDEX.md: 缺少活动事项标记")
        counts = {item_id: row_ids.count(item_id) for item_id in set(row_ids)}
        for item_id, count in sorted(counts.items()):
            if count > 1:
                errors.append(f"02-work-items/WORK_INDEX.md: 活动事项重复登记 {item_id}")
        for item_id in sorted(active_items):
            if item_id not in row_ids:
                errors.append(f"02-work-items/WORK_INDEX.md: 活动事项未登记 {item_id}")
            else:
                row = next(
                    line for line in block.splitlines() if item_id in line
                )
                cells = _markdown_row_cells(row)
                work_cell = cells[4] if len(cells) >= 6 else ""
                state_cell = cells[5] if len(cells) >= 6 else ""
                if f"02-work-items/active/{item_id}/" not in work_cell:
                    errors.append(f"{item_id}: 索引工作路径与目录不一致")
                if f"03-session-state/active/{item_id}/" not in state_cell:
                    errors.append(f"{item_id}: 索引状态路径与目录不一致")
                index_status = cells[2] if len(cells) >= 3 else ""
                status_value = active_fields.get(item_id, {}).get("status")
                if status_value and index_status != status_value:
                    errors.append(
                        f"02-work-items/WORK_INDEX.md: {item_id} 索引状态 {index_status!r} "
                        f"与 STATUS.md 的 {status_value!r} 不一致"
                    )
        for item_id in sorted(set(row_ids) - set(active_items)):
            errors.append(f"02-work-items/WORK_INDEX.md: 已登记但目录不存在 {item_id}")

        archive_block, archive_row_ids = _archived_index_rows(index)
        if not archive_block:
            errors.append("02-work-items/WORK_INDEX.md: 缺少归档事项标记")
        archive_counts = {
            item_id: archive_row_ids.count(item_id)
            for item_id in set(archive_row_ids)
        }
        for item_id, count in sorted(archive_counts.items()):
            if count > 1:
                errors.append(f"02-work-items/WORK_INDEX.md: 归档事项重复登记 {item_id}")
        for item_id in sorted(archived_items):
            if item_id not in archive_row_ids:
                errors.append(f"02-work-items/WORK_INDEX.md: 归档事项未登记 {item_id}")
            else:
                row = next(
                    line for line in archive_block.splitlines() if item_id in line
                )
                cells = _markdown_row_cells(row)
                work_cell = cells[3] if len(cells) >= 5 else ""
                state_cell = cells[4] if len(cells) >= 5 else ""
                if f"02-work-items/archived/{item_id}/" not in work_cell:
                    errors.append(f"{item_id}: 归档索引工作路径与目录不一致")
                if f"03-session-state/archived/{item_id}/" not in state_cell:
                    errors.append(f"{item_id}: 归档索引状态路径与目录不一致")
        for item_id in sorted(set(archive_row_ids) - archived_items):
            errors.append(f"02-work-items/WORK_INDEX.md: 归档已登记但目录不存在 {item_id}")

    return errors


def _print_manifest(manifest: dict[str, list[str]]) -> None:
    labels = [
        ("always_load", "始终加载"),
        ("item_state", "事项状态"),
        ("scenario", "场景上下文"),
        ("load_on_demand", "按需定位，不预读"),
    ]
    for key, label in labels:
        print(f"{label}:")
        values = manifest[key]
        if values:
            for value in values:
                print(f"- {value}")
        elif key == "scenario":
            print("- 由 context-router.md 判断后再加载")
        else:
            print("- 无")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="本地 AI 协作工作区工具")
    parser.add_argument("--root", type=Path, default=None)
    subparsers = parser.add_subparsers(dest="command", required=True)

    new_item = subparsers.add_parser("new-item", help="创建隔离工作事项")
    new_item.add_argument("slug")
    new_item.add_argument("--title", required=True)
    new_item.add_argument("--workspace", action="append", dest="workspaces")
    new_item.add_argument("--date")

    context = subparsers.add_parser("context", help="生成渐进式加载清单")
    context.add_argument("item_id")
    context.add_argument("--mode", default="auto")

    subparsers.add_parser("validate", help="校验工作区结构")
    return parser


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (OSError, ValueError):
                pass


def main(argv: list[str] | None = None) -> int:
    _configure_utf8_stdio()
    parser = _build_parser()
    args = parser.parse_args(argv)
    root = resolve_project_root(args.root, Path.cwd())
    try:
        if args.command == "new-item":
            target = create_item(
                root=root,
                slug=args.slug,
                title=args.title,
                workspaces=args.workspaces,
                date=args.date,
            )
            print(f"已创建事项: {_relative(root, target)}")
            return 0
        if args.command == "context":
            manifest = context_manifest(root, args.item_id, args.mode)
            _print_manifest(manifest)
            return 0
        if args.command == "validate":
            errors = validate_workspace(root)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print("OK")
            return 0
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

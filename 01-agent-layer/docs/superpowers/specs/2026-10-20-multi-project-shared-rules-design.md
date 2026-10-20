# Multi-Project Shared Rules Design

## Intent

把 `E:\多agent协作` 作为本机共享规则源。以后每开一个工程，都建立一个独立工程目录；工程拥有自己的工作和状态数据，但共同使用同一份 Agent 规范、路由、模板、脚本和测试。

## Goals

- 工程 A 与工程 B 的 `02-work-items`、`03-session-state` 和 Git 历史完全隔离。
- 所有工程从同一个物理 `01-agent-layer` 读取规则，规则修改自动生效。
- 新工程通过一个命令生成，不手工复制规则。
- 从工程目录运行共享脚本时，脚本自动识别当前工程根。
- Codex 每轮审查使用独立证据目录，历史轮次不覆盖。

## Non-Goals

- 不支持把工程直接复制到另一台电脑后继续工作。
- 不支持不同工程使用不同规则版本。
- 不允许 DeepSeek 修改治理文件、提交 Git 或写 Codex 审查结论。
- 不引入集中数据库或在线服务。

## Project Layout

```text
Project-A/
  01-agent-layer/      NTFS junction -> E:\多agent协作\01-agent-layer
  02-work-items/       项目本地，Git 跟踪
  03-session-state/    项目本地，Git 跟踪
  .ai-workspace.json   项目模式与共享层绝对路径
  .git/
  AGENTS.md 等         项目本地适配入口
```

项目的 `.gitignore` 排除 `01-agent-layer/`，因为联接目标由共享仓库管理。`.ai-workspace.json` 被项目 Git 跟踪，用于验证共享层绑定。

## Generator

`01-agent-layer/scripts/New-AiProject.ps1`：

1. 确认共享层完整。
2. 拒绝覆盖非空目录。
3. 创建项目目录和 `01-agent-layer` 联接。
4. 复制项目骨架和平台适配文件。
5. 写入 `.ai-workspace.json`。
6. 初始化项目 Git，并设置 `core.hooksPath=01-agent-layer/githooks`。
7. 运行共享 `workspace.py validate`。

## Root Discovery

`workspace.py` 按以下优先级确定工程根：

1. 显式 `--root`。
2. 从当前工作目录向上查找同时包含 `.ai-workspace.json`、`02-work-items/WORK_INDEX.md` 和 `03-session-state/` 的目录。
3. 找不到时回退到脚本所在的共享仓库根。

这样从 `Project-A` 或其子目录运行时，不会误写共享仓库根。

## Review Evidence

审查规则文件：

```text
01-agent-layer/contexts/codex-review.md
```

场景名称仍为 `review`。每轮证据：

```text
02-work-items/{active,archived}/<item-id>/reviews/<task-id>/round-<n>/
  review.md
  diff.patch
  test-output.txt
```

`artifacts/delegation/` 保存 DeepSeek 请求、事件和结果；`reviews/` 保存 Codex 独立验收。两者分离。

## Failure Behavior

- 共享层缺失或联接目标不一致：结构校验失败。
- 非空目录已存在：工程生成中止，不覆盖。
- 项目脚本无法识别工程根：必须显式使用 `--root`，不得猜测写入位置。
- 审查目录出现扁平文件或非法轮次：结构校验失败。
- 共享规则修改未通过测试：不得提交，因为它会影响所有工程。

## Acceptance

- 两个临时工程都能创建并通过结构校验。
- 两个工程读取同一份 `AGENT_GUIDE.md`。
- 一个工程创建的事项不出现在另一个工程。
- 项目 Git 忽略 `01-agent-layer` 联接，并使用共享 hook。
- 全量 `unittest` 与 `workspace.py validate` 通过。

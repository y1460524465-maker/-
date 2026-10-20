# DeepSeek Harness 委派桥实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 Codex 通过本机 DeepSeek Harness 桌面版的 headless 入口委派实现任务，并由 Codex 独立审查和测试。

**Architecture:** 一个 Python 标准库桥负责构造 headless 命令、启用本地凭据、限定 sandbox、保存请求/事件/结果，并解析 session-id。规范层增加 delegation 场景和任务单模板；DeepSeek 只实现，Codex 负责验收与提交。

**Tech Stack:** Markdown、Python 3.12 标准库、DeepSeek Harness `dsh --profile headless`、`unittest`。

**Spec:** `docs/superpowers/specs/2026-10-19-deepseek-harness-bridge-design.md`

**Execution status:** Complete on 2026-10-19. Verification evidence: `docs/verification/2026-10-19-deepseek-bridge-verification.md`.

## Global Constraints

- 只调用 `dsh --profile headless`，不进行桌面 UI 自动化。
- 默认仅允许 `read-only` 或 `workspace-write`，禁止 `danger-full-access`。
- 使用 `tools/dsh/headless-codex.patch.yml` 启用本地凭据和免交互审批。
- DeepSeek 不提交 Git，不修改事项状态、交接、需求基线或规范文件。
- Codex 必须在独立的 review/test 阶段验证，不能采信 DeepSeek 的完成声明。
- 所有委派证据保存在目标事项的 `artifacts/delegation/`。
- 测试不得发起真实模型调用。

## Review Focus

- 子进程继承敏感环境变量时，必须移除 KEY/TOKEN/SECRET/PASSWORD/CREDENTIAL 类变量。
- `--session-id` 续接时，新任务必须复用原会话而不是新建隐含会话。
- 超时或缺少 final 事件时，桥不能返回成功。
- `--cwd` 不存在或不是目录时，必须在发起模型调用前失败。
- 委派期间 Git HEAD 改变时，必须标记策略违规并保留证据。

---

### Task 1: 增加 delegation 场景、模板与行为约束

**Files:**
- Create: `contexts/delegation.md`
- Create: `templates/deepseek-task.md`
- Modify: `AGENT_GUIDE.md`
- Modify: `core/invariants.md`
- Modify: `context-router.md`
- Modify: `contexts/review.md`
- Modify: `contexts/sync.md`
- Modify: `scripts/workspace.py`
- Modify: `tests/test_workspace.py`

**Interfaces:**
- Consumes: 现有渐进式加载与状态契约。
- Produces: 场景名 `delegation`；`context_manifest(..., mode="delegation")` 返回 `contexts/delegation.md`。

- [ ] **Step 1: 写 delegation 模式失败测试**

在现有 context 测试中断言 `delegation,coding,review,sync` 返回四个场景文件。

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m unittest tests.test_workspace.WorkspaceTests.test_context_manifest_for_modes -v`

Expected: FAIL，因为 `delegation` 尚被判定为未知场景。

- [ ] **Step 3: 增加 delegation 路由与文档**

在 `scripts/workspace.py` 的允许模式中加入 `delegation`，并补齐规范、上下文和任务模板。

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m unittest tests.test_workspace.WorkspaceTests.test_context_manifest_for_modes -v`

Expected: PASS。

### Task 2: 实现 DeepSeek headless 桥

**Files:**
- Create: `scripts/dsh_bridge.py`
- Create: `tests/test_dsh_bridge.py`
- Modify: `tools/dsh/headless-credentials.patch.yml` → `tools/dsh/headless-codex.patch.yml`

**Interfaces:**
- Consumes: `dsh` CLI、目标事项、任务文件和 cwd。
- Produces:
  - `build_command(dsh: Path, patch: Path, session_id: str | None) -> list[str]`
  - `delegate_item(root: Path, item_id: str, task_file: Path, cwd: Path, label: str, session_id: str | None, permission_mode: str, timeout: int, dsh: Path, patch: Path) -> DelegationResult`
  - CLI `doctor`、`delegate`。

- [ ] **Step 1: 写成功委派失败测试**

使用临时假 `dsh.cmd` 输出 session、final 和退出码 0，断言桥生成四类证据文件、解析 session-id、写入 INDEX。

Run: `python -m unittest tests.test_dsh_bridge.DshBridgeTests.test_delegate_saves_events_result_and_metadata -v`

Expected: FAIL，因为 `scripts.dsh_bridge` 不存在。

- [ ] **Step 2: 实现最小 delegate 路径**

使用 stdin 传入任务，固定参数 `--profile headless --patch <patch> --json`，设置 `DSH_PERMISSION_MODE=workspace-write`，保存输出。

- [ ] **Step 3: 运行成功路径测试**

Run: `python -m unittest tests.test_dsh_bridge.DshBridgeTests.test_delegate_saves_events_result_and_metadata -v`

Expected: PASS。

- [ ] **Step 4: 写错误、超时、续接和敏感环境测试**

断言非零退出和 error final 返回失败、超时退出码 124、续接命令包含 `--session-id`、秘密环境变量不出现在假子进程环境。

Run: `python -m unittest tests.test_dsh_bridge -v`

Expected: FAIL，直到实现这些分支。

- [ ] **Step 5: 实现失败分支、doctor 与参数校验**

拒绝 `danger-full-access`、缺任务、缺 cwd、缺 dsh、缺 patch。

- [ ] **Step 6: 运行桥全量测试**

Run: `python -m unittest tests.test_dsh_bridge -v`

Expected: PASS。

### Task 3: 真实 DeepSeek 端到端验证

**Files:**
- Create: `work/active/<demo-item>/artifacts/delegation/*`
- Verify: Git diff、测试输出、session-id。

**Interfaces:**
- Consumes: Task 2 桥。
- Produces: 一次真实 DeepSeek 写入文件和测试通过的证据；Codex 独立复跑测试。

- [ ] **Step 1: 创建隔离演示事项与 cwd**

在演示事项的 `workspaces/implementation/` 中放入最小任务单。

- [ ] **Step 2: 调用真实桥**

Run: `python scripts/dsh_bridge.py delegate ...`

Expected: 返回 session-id，final 事件完成，证据文件存在。

- [ ] **Step 3: Codex 独立审查**

读取生成文件和 git status/diff；运行 DeepSeek 声称运行的测试。

Expected: 文件符合任务单，测试真实通过。

- [ ] **Step 4: 记录结果并归档演示**

更新演示事项状态、交接和 journal，验证门禁后提交。

### Task 4: 最终验证与使用说明

**Files:**
- Modify: `README.md`
- Modify: `WORK_INDEX.md` / 当前事项状态文件
- Create: `docs/verification/2026-10-19-deepseek-bridge-verification.md`

**Interfaces:**
- Consumes: 全部前序任务。
- Produces: 用户可直接照做的下单、修复轮次和验收命令。

- [ ] **Step 1: 运行全部测试**

Run: `python -m unittest discover -s tests -v`

Expected: 0 failures。

- [ ] **Step 2: 运行结构校验**

Run: `python scripts/workspace.py validate`

Expected: `OK`。

- [ ] **Step 3: 更新快速开始与验证记录**

说明 Codex 主控、DeepSeek 实现、Codex 审查测试的标准流程。

- [ ] **Step 4: 提交**

Run: `git add ...`，然后 `git commit`；hook 必须输出 `OK`。

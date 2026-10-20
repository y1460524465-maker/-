# 本地 AI 协作工作区实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立一个可被不同 Agent 恢复、隔离记录并渐进加载的本地 Git 工作区。

**Architecture:** 根入口只保存启动协议和统一路由；核心不变量常驻，事项状态按目录物理隔离，场景规范按需加载；Python CLI 负责建项、生成加载清单和机械校验，Git hook 阻止不合规提交。

**Tech Stack:** Markdown、Git、Python 3.12 标准库、`unittest`。

**Spec:** `docs/superpowers/specs/2026-10-19-ai-workspace-design.md`

**Execution status:** Complete on 2026-10-19. Verification evidence: `docs/verification/2026-10-19-workspace-verification.md`.

## Global Constraints

- `AGENT_GUIDE.md` 是唯一规范入口，适配文件不得复制规则。
- 每个活动事项必须有 `STATUS.md`、`handoff.md`、`brief.md`、`decisions.md`、`journal/`、`knowledge/`、`drafts/`、`artifacts/`、`workspaces/`、`archive/`。
- 默认仅本地 Git；推送、合并共享分支和改写历史需用户明确要求。
- 所有命令行工具只依赖 Python 3.10+ 标准库。
- CLI 测试不得修改真实工作区，只能使用临时目录。
- 不在提交前跳过 `python scripts/workspace.py validate`。

## Review Focus

- 事项 ID 含路径分隔符或 `..` 时，工具必须拒绝并保持所有写入位于 `work/active/`。
- 索引中重复登记或存在活动目录未登记时，校验必须失败并指出事项。
- 上下文清单在混合模式或未知模式下不能静默遗漏必要文件。
- 适配文件被加入额外行为规则时，应能通过一致性测试发现入口分叉。
- Git hook 在校验器不可用或校验失败时必须阻止提交，而不是放行。

---

### Task 1: 建立规范入口、核心层与场景路由

**Files:**
- Create: `AGENT_GUIDE.md`
- Create: `AGENTS.md`
- Create: `CLAUDE.md`
- Create: `GEMINI.md`
- Create: `.cursor/rules/agent-guide.mdc`
- Create: `.github/copilot-instructions.md`
- Create: `core/invariants.md`
- Create: `core/state-contract.md`
- Create: `core/git-protocol.md`
- Create: `context-router.md`
- Create: `contexts/coding.md`
- Create: `contexts/review.md`
- Create: `contexts/sync.md`

**Interfaces:**
- Consumes: 规格第 5、6、7、10 节。
- Produces: 新会话可执行的固定启动顺序、权限矩阵、场景模式名 `coding|review|sync`。

- [ ] **Step 1: 创建根入口与适配层**

`AGENT_GUIDE.md` 写明启动顺序、目录职责、必须询问事项和最小完成流程；所有适配文件只包含“读取并遵循 `AGENT_GUIDE.md`”的转发指令及适用平台的固定配置。

- [ ] **Step 2: 创建核心不变量和状态契约**

`core/invariants.md` 固化行为边界；`core/state-contract.md` 固化 STATUS/handoff/journal/brief 的职责与更新时机；`core/git-protocol.md` 固化提交、并发与外部动作规则。

- [ ] **Step 3: 创建场景路由与三个上下文模块**

`context-router.md` 给出关键词、意图、风险和混合模式判定；`coding.md`、`review.md`、`sync.md` 分别给出执行、核验和同步清单。

- [ ] **Step 4: 验证入口一致性**

Run: `rg -n "AGENT_GUIDE\.md" AGENTS.md CLAUDE.md GEMINI.md .cursor/rules/agent-guide.mdc .github/copilot-instructions.md`

Expected: 每个适配文件至少出现一次，且文件内不存在另一套行为规则。

- [ ] **Step 5: 提交**

```bash
git add AGENT_GUIDE.md AGENTS.md CLAUDE.md GEMINI.md .cursor .github core context-router.md contexts
git commit -m "docs: add agent routing and core invariants"
```

### Task 2: 建立事项模板、索引与可恢复结构

**Files:**
- Create: `WORK_INDEX.md`
- Create: `work/README.md`
- Create: `work/active/README.md`
- Create: `work/archive/README.md`
- Create: `templates/work-item/STATUS.md`
- Create: `templates/work-item/handoff.md`
- Create: `templates/work-item/brief.md`
- Create: `templates/work-item/decisions.md`
- Create: `templates/work-item/journal/YYYY-MM-DD.md`
- Create: `templates/work-item/knowledge/README.md`
- Create: `templates/work-item/drafts/README.md`
- Create: `templates/work-item/artifacts/README.md`
- Create: `templates/work-item/workspaces/README.md`
- Create: `templates/work-item/archive/README.md`
- Create: `knowledge/README.md`
- Create: `knowledge/INDEX.md`
- Create: `.gitignore`

**Interfaces:**
- Consumes: Task 1 的状态契约与目录职责。
- Produces: 可供 `workspace.py new-item` 复制的模板根 `templates/work-item`；以下固定标题供校验器检查：STATUS 的 `## 已完成`、`## 正在做`、`## 下一步`、`## 阻塞与待确认`、`## 最近验证`、`## 当前边界与有效不变量`，handoff 的 `## 唯一下一步`、`## 必读顺序`、`## 已完成，不要重复`、`## 已知坑与禁止动作`、`## 可直接运行的验证`。

- [ ] **Step 1: 创建事项模板**

模板中的所有占位符使用 `{{...}}`；STATUS 使用 YAML front matter 记录 `id/title/status/updated`。

- [ ] **Step 2: 创建索引与目录说明**

`WORK_INDEX.md` 使用表头 `| ID | 标题 | 状态 | 最近更新 | 路径 |`；`work/README.md` 解释 active/archive 与每类文件职责。

- [ ] **Step 3: 创建知识提升入口**

根 `knowledge/` 只放已验证、可跨事项复用的知识；`INDEX.md` 记录来源事项、验证状态和入口。

- [ ] **Step 4: 验证模板标题**

Run: `rg -n "^## " templates/work-item/STATUS.md templates/work-item/handoff.md`

Expected: 输出包含 Interfaces 中列出的全部固定标题。

- [ ] **Step 5: 提交**

```bash
git add WORK_INDEX.md work templates knowledge .gitignore
git commit -m "feat: add isolated work item templates"
```

### Task 3: 实现建项、上下文清单与结构校验 CLI

**Files:**
- Create: `scripts/workspace.py`
- Create: `tests/test_workspace.py`

**Interfaces:**
- Consumes: `templates/work-item` 目录与 `WORK_INDEX.md` 表头。
- Produces:
  - `validate_workspace(root: Path) -> list[str]`
  - `create_item(root: Path, slug: str, title: str, workspaces: list[str], date: str) -> Path`
  - `context_manifest(root: Path, item_id: str, mode: str) -> dict[str, list[str]]`
  - CLI `new-item`、`context`、`validate`

- [ ] **Step 1: 写建项行为失败测试**

测试在临时仓库中复制模板并调用 `create_item`，断言事项目录、默认 `main` 工作区、索引登记和状态元数据存在。

Run: `python -m unittest tests.test_workspace.WorkspaceTests.test_create_item_bootstraps_directory_and_index -v`

Expected: FAIL，因为 `scripts.workspace` 尚不存在或函数未定义。

- [ ] **Step 2: 实现最小建项逻辑**

校验 slug 仅含小写字母、数字和连字符；拒绝 `.`、`..`、路径分隔符；以 `YYYY-MM-DD-<slug>` 创建目录；从模板替换 `{{ID}}`、`{{TITLE}}`、`{{DATE}}`；向索引追加一个表格行。

- [ ] **Step 3: 运行建项测试**

Run: `python -m unittest tests.test_workspace.WorkspaceTests.test_create_item_bootstraps_directory_and_index -v`

Expected: PASS。

- [ ] **Step 4: 写上下文清单失败测试**

分别断言 `auto`、`coding`、`review`、`sync` 返回必需文件和无重复路径；模式切换或混合输入 `coding,sync` 同时返回两个上下文文件。

Run: `python -m unittest tests.test_workspace.WorkspaceTests.test_context_manifest_for_modes -v`

Expected: FAIL，因为清单函数尚未存在。

- [ ] **Step 5: 实现上下文清单**

始终返回 `AGENT_GUIDE.md`、`core/invariants.md`、目标事项 `STATUS.md`、`handoff.md`、`brief.md`；按模式返回 `contexts/<mode>.md`。

- [ ] **Step 6: 写结构校验失败测试**

覆盖缺文件、错误状态标题、活动事项未登记、索引重复、模板占位残留和非法目录名。

Run: `python -m unittest tests.test_workspace.WorkspaceTests.test_validate_reports_contract_errors -v`

Expected: FAIL 或断言错误，因为校验器尚未完整实现。

- [ ] **Step 7: 实现校验器与 CLI**

返回可读错误列表；CLI 在错误时退出码 1，成功时退出码 0。

- [ ] **Step 8: 运行全量测试**

Run: `python -m unittest discover -s tests -v`

Expected: 全部 PASS，0 failures。

- [ ] **Step 9: 提交**

```bash
git add scripts/workspace.py tests/test_workspace.py
git commit -m "feat: add workspace creation and validation CLI"
```

### Task 4: 安装 Git 门禁并验证恢复流程

**Files:**
- Create: `.githooks/pre-commit`
- Create: `.githooks/README.md`
- Create: `README.md`
- Create: `docs/verification/2026-10-19-workspace-verification.md`

**Interfaces:**
- Consumes: `workspace.py validate`。
- Produces: 提交前自动校验；一段可供用户直接使用的快速开始说明；验证证据。

- [ ] **Step 1: 创建 pre-commit hook**

Hook 调用 `python scripts/workspace.py validate`；Python 不可用或校验失败时以非零退出。

- [ ] **Step 2: 配置仓库 hooks 路径**

Run: `git config core.hooksPath .githooks`

Expected: `git config --get core.hooksPath` 输出 `.githooks`。

- [ ] **Step 3: 创建带完整状态的首个真实事项并测试上下文恢复**

Run: `python scripts/workspace.py new-item workspace-demo --title "工作区恢复演示" --workspace requirement --workspace investigation`

Expected: 创建 `work/active/<日期>-workspace-demo/`，两个工作区目录和索引登记均存在。

- [ ] **Step 4: 验证上下文清单**

Run: `python scripts/workspace.py context <item-id> --mode coding,sync`

Expected: 同时列出核心、事项状态、交接、brief 以及 `contexts/coding.md`、`contexts/sync.md`。

- [ ] **Step 5: 验证结构门禁**

先运行合法校验；再在临时副本中移除 `STATUS.md`，确认校验返回非零和明确错误。不得修改真实事项来完成负面测试。

- [ ] **Step 6: 写快速开始与验证记录**

README 包含新会话启动、建项、继续、交接、归档和知识提升的最短路径；验证记录附命令、预期和结果摘要。

- [ ] **Step 7: 提交**

```bash
git add .githooks README.md docs/verification
git commit -m "chore: enforce workspace validation before commit"
```

### Task 5: 最终审查与交付

**Files:**
- Modify: 仅修复审查发现的 Critical/Important 问题。

**Interfaces:**
- Consumes: 前四项任务全部接口。
- Produces: 可交付的初始 Git 仓库与验证结论。

- [ ] **Step 1: 按规格逐项核对**

核对统一入口、事项隔离、跨会话恢复、渐进加载、询问规则、Git 状态、知识沉淀、文档连续性、并发边界和机械校验。

- [ ] **Step 2: 运行全量验证**

Run: `python -m unittest discover -s tests -v`

Run: `python scripts/workspace.py validate`

Expected: 测试 0 failures，校验输出 `OK`。

- [ ] **Step 3: 检查 Git 状态与历史**

Run: `git status --short --branch`

Run: `git log --oneline --decorate -n 10`

Expected: 工作树干净，提交历史按任务组织。

- [ ] **Step 4: 最终提交**

仅在存在审查修复时提交；否则保持现有历史，不制造空提交。

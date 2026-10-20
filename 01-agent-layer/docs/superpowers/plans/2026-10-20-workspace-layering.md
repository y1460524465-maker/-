# 本地 AI 工作区三层分层实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将工作区物理分层为 Agent 层、工作事项层和跨会话状态层。

**Architecture:** 系统文件移动到 `01-agent-layer`；事项工作内容移动到 `02-work-items`；事项状态移动到 `03-session-state`。工具通过事项 ID 配对两层。

**Tech Stack:** Windows PowerShell、Git、Python 3.12、unittest。

**Spec:** `docs/superpowers/specs/2026-10-20-workspace-layering-design.md`

## Global Constraints

- 使用移动而非复制，保留文件内容。
- 不删除 `tests/`。
- 不修改并行事项的业务代码内容。
- 平台入口保留在根目录，指向 `01-agent-layer/AGENT_GUIDE.md`。
- 迁移完成后全量测试和结构校验必须通过。

## Review Focus

- 事项 ID 在工作和状态目录中必须一一对应。
- 新事项必须同时创建工作区和状态目录。
- 旧路径不能在迁移后继续被脚本引用。
- DeepSeek 桥写 artifacts 时不能写到状态目录。
- Git hook 必须能调用新位置的校验脚本。

---

### Task 1: 创建三层骨架并移动系统文件

**Files:**
- Create: `01-agent-layer/`, `02-work-items/`, `03-session-state/`
- Move: `AGENT_GUIDE.md`, `core/`, `context-router.md`, `contexts/`, `templates/`, `scripts/`, `tests/`, `tools/`, `docs/`
- Modify: root adapters, README, hooks

- [ ] **Step 1: 创建目标目录**
- [ ] **Step 2: 移动系统文件**
- [ ] **Step 3: 更新平台入口和 hook 路径**
- [ ] **Step 4: 验证根目录只保留入口、Git 基础设施和三层目录**

### Task 2: 拆分现有事项

**Files:**
- Move: active/archive 事项的工作文件到 `02-work-items/`
- Move: STATUS/handoff/decisions/journal/knowledge 到 `03-session-state/`

- [ ] **Step 1: 拆分 simple-html-page**
- [ ] **Step 2: 拆分 go-ttl-cache**
- [ ] **Step 3: 拆分 distributed-rate-limiter**
- [ ] **Step 4: 拆分 archived deepseek-harness-bridge**
- [ ] **Step 5: 移动 WORK_INDEX 并更新双路径**

### Task 3: 更新 workspace.py 与测试

**Files:**
- Modify: `01-agent-layer/scripts/workspace.py`
- Modify: `01-agent-layer/tests/test_workspace.py`

- [ ] **Step 1: 更新测试预期为双目录结构**
- [ ] **Step 2: 运行测试确认失败**
- [ ] **Step 3: 更新建项、context manifest、validate**
- [ ] **Step 4: 运行测试通过**

### Task 4: 更新桥、文档和验证

**Files:**
- Modify: `01-agent-layer/scripts/dsh_desktop_bridge.py`
- Modify: `01-agent-layer/scripts/dsh_bridge.py`
- Modify: `01-agent-layer/AGENT_GUIDE.md`, README, contexts, docs

- [ ] **Step 1: 更新桥的事项工作目录解析**
- [ ] **Step 2: 更新文档路径**
- [ ] **Step 3: 运行全量测试、validate、doctor**
- [ ] **Step 4: 限定路径提交**

# 本地 AI 工作区三层分层设计

## 目标

把当前平铺的文件整理成三个清晰区域：

1. 多 Agent 适配层：规则、路由、上下文、模板、工具和测试；
2. 工作事项分区：每个事项的需求、代码工作区、草稿、交付物和归档；
3. 跨会话状态：每个事项的 STATUS、handoff、决策、日志和知识。

工作事项和状态使用相同事项 ID 配对，但存放位置分离。

## 目标结构

```text
README.md
AGENTS.md / CLAUDE.md / GEMINI.md      平台薄适配入口
.cursor/ .github/                      平台适配入口
01-agent-layer/
  README.md
  AGENT_GUIDE.md
  core/
  router/context-router.md
  contexts/
  templates/
  scripts/
  tests/
  tools/dsh/
  docs/
02-work-items/
  README.md
  WORK_INDEX.md
  active/<item-id>/
    brief.md
    workspaces/
    drafts/
    artifacts/
    archive/
  archived/<item-id>/
03-session-state/
  README.md
  knowledge/
  active/<item-id>/
    STATUS.md
    handoff.md
    decisions.md
    journal/
    knowledge/
  archived/<item-id>/
```

根目录保留 Git 基础设施、平台入口和总说明，不承载业务事项状态。

## 事项配对

同一事项 ID 同时出现在：

```text
02-work-items/active/<item-id>/
03-session-state/active/<item-id>/
```

`02` 只回答“做了什么、产出在哪里”；`03` 只回答“做到哪里、下一步是什么、发生过什么”。

`WORK_INDEX.md` 同时登记工作目录和状态目录，避免隐藏映射。

## 工具变化

- `workspace.py new-item` 同时创建工作与状态目录。
- `workspace.py context` 从 `02` 读取 brief/工作区，从 `03` 读取 STATUS/handoff/journal。
- `workspace.py validate` 校验两个目录、索引和配对关系。
- Git hook 调用 `01-agent-layer/scripts/workspace.py`。
- DeepSeek 桥的工作目录和 artifacts 写入 `02`，不修改 `03` 的治理文件。
- 平台入口仍留在根目录，但统一指向 `01-agent-layer/AGENT_GUIDE.md`。

## 兼容性

- 迁移使用 Git 移动，保留文件内容和历史。
- `go-ttl-cache`、`distributed-rate-limiter`、`simple-html-page` 同步迁移，不修改业务内容。
- 迁移后旧的 `work/`、根 `core/`、根 `contexts/` 等路径不再保留副本。
- 所有系统测试在迁移后必须通过。

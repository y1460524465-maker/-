# 01 Agent Layer

这一层回答“Agent 应该怎样工作”。它是本机所有工程共享的治理层，不放某个具体需求的代码、草稿或交付事实。

## 入口

[`AGENT_GUIDE.md`](AGENT_GUIDE.md) 是唯一规范入口。根目录的 `AGENTS.md`、`CLAUDE.md`、`GEMINI.md`、Cursor 和 Copilot 适配文件只把控制权转到这里。

## 目录职责

| 路径 | 作用 | 何时读取 |
|---|---|---|
| `AGENT_GUIDE.md` | 完整工作区规范 | 每次会话开始 |
| `core/invariants.md` | 不可丢失的行为底线 | 每次会话开始 |
| `core/state-contract.md` | STATUS、handoff、journal 等文件的契约 | 建项、同步、交接 |
| `core/git-protocol.md` | 检查点、暂存、并发和禁止动作 | 提交或处理并发改动 |
| `router/context-router.md` | 从任务判断 coding、delegation、review、sync | 每个任务段开始或切换时 |
| `contexts/` | 各场景的按需执行清单 | 路由选中后 |
| `contexts/codex-review.md` | Codex 独立审查流程，不用于 DeepSeek 自检 | 收回执行结果后 |
| `templates/` | 新事项、DeepSeek 任务单、文档骨架 | 创建或委派时 |
| `scripts/workspace.py` | 建项、生成加载清单、校验结构 | 日常治理 |
| `scripts/New-AiProject.ps1` | 创建共享本层规则的新工程 | 新建工程时 |
| `scripts/dsh_desktop_bridge.py` | Codex 与本机 DeepSeek Harness 桌面宿主之间的桥 | 委派和收回结果 |
| `scripts/dsh_bridge.py` | 明确批准后的 headless 降级入口 | 仅在用户同意时 |
| `githooks/` | 新工程共用的提交前校验 | 初始化工程时 |
| `tools/dsh/` | 桌面实时模式启动脚本和兼容补丁 | 启动 Harness |
| `tests/` | 系统自身测试 | 修改治理工具后 |
| `docs/` | 历史设计、计划和实施证据 | 追溯原因时按需读取 |

`docs/superpowers/` 中的早期文档按当时目录编写，可能保留旧路径；它们不是当前操作入口。当前行为以 `AGENT_GUIDE.md` 为准。

## 共享给多个工程

新工程通过目录联接使用本层：

```text
powershell -NoProfile -File 01-agent-layer/scripts/New-AiProject.ps1 -Path E:\AI-Projects\Project-A
```

工程只拥有自己的 `02-work-items`、`03-session-state` 和 Git 历史。本层变更会立即被所有工程使用，因此提交前必须运行本层测试。

## 渐进式加载

```text
第 0 层  AGENT_GUIDE.md + core/invariants.md + router/context-router.md
第 1 层  02-work-items/WORK_INDEX.md（不知道事项时）
         事项的 STATUS.md + handoff.md + brief.md
第 2 层  contexts/<当前场景>.md（review 场景使用 codex-review.md）
第 3 层  handoff 或用户请求明确引用的代码、文档、知识
```

加载范围可以缩小，已经生效的用户约束、验收标准、风险和禁止动作不能丢。模式切换后要保留这些内容；上下文压缩后从文件和 Git 重新建立事实。

## 修改这一层

修改规范、路由、模板或脚本属于全局治理变更：

1. 先说明原因和影响面。
2. 同步检查 `core/`、`contexts/`、`templates/`、`scripts/` 与测试是否仍一致。
3. 运行：

```text
python 01-agent-layer/scripts/workspace.py validate
python -m unittest discover -s 01-agent-layer/tests -v
```

4. 用 `workspace:` 前缀提交，只暂存本层相关改动。

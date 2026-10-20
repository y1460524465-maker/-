# 本地 AI 协作工作区

这个仓库既是共享规则源，也是当前参考工作区。它用 Markdown、目录约定和 Git 保存工作事实，让新会话、新 Agent 或新文档可以从当前状态继续，而不依赖某一条聊天记录。

本机所有工程共享同一份 `01-agent-layer`。每个工程拥有独立的 `02-work-items`、`03-session-state` 和 Git 历史。

## 三个顶层区域

```text
01-agent-layer/     Agent 如何工作：规范、路由、模板、脚本、测试
02-work-items/      正在做什么：需求、代码、草稿、交付物、证据
03-session-state/   做到哪里：状态、交接、决策、日志、知识
```

三类内容刻意分开：

- `01-agent-layer/` 是稳定规则和工具，不保存某个需求的业务事实。
- `02-work-items/` 是事项的工作现场，代码和文档按事项物理隔离。
- `03-session-state/` 是事项的可恢复记忆，按同一个事项 ID 与工作目录配对。

完整目录：

```text
01-agent-layer/
  AGENT_GUIDE.md              唯一规范入口
  core/                       每次会话都加载的行为不变量
  router/context-router.md    判断当前任务场景
  contexts/                   coding / delegation / codex-review / sync 按需加载
  templates/                  新事项和委派任务模板
  scripts/                    建项、上下文清单、结构校验、桌面桥
  githooks/                   工程共享的提交门禁
  tools/                      DeepSeek Harness 启动辅助文件
  tests/                      系统自身测试
  docs/                       历史设计、计划和实施记录

02-work-items/
  WORK_INDEX.md               活动与归档事项总索引
  active/<item-id>/           进行中事项的工作内容
  archived/<item-id>/         已结束事项的工作内容

03-session-state/
  knowledge/                  已验证、可跨事项复用的知识
  active/<item-id>/           进行中事项的跨会话状态
  archived/<item-id>/         已结束事项的跨会话状态
```

每个事项由一对同 ID 目录组成。例如：

```text
02-work-items/active/2026-10-19-example/
  brief.md                    目标、验收标准、范围、约束
  workspaces/                 实现、排查、实验等隔离工作区
  drafts/                     未定稿文档
  artifacts/                  交付物和验证证据
  reviews/                    每轮 Codex 审查的独立证据包
  archive/                    本事项内部历史版本

03-session-state/active/2026-10-19-example/
  STATUS.md                   已完成、正在做、下一步、阻塞、验证
  handoff.md                  给下一个 Agent 的可执行交接
  decisions.md                有代价的取舍
  journal/                    追加式过程记录
  knowledge/                  本事项沉淀的候选知识
```

## 新工程

在当前 Windows 电脑上创建一个独立工程：

```text
powershell -NoProfile -File 01-agent-layer/scripts/New-AiProject.ps1 -Path E:\AI-Projects\Project-A
```

生成后的工程：

```text
Project-A/
  01-agent-layer/      指向共享规则层
  02-work-items/       本工程独立事项
  03-session-state/    本工程独立状态
  .ai-workspace.json   共享层与本机绑定信息
  .git/
  AGENTS.md 等         本工程适配入口
```

工程之间不共享事项、状态或 Git 历史。修改共享 `01-agent-layer` 后，下一次会话会在所有工程同时生效，因此共享规则变更必须先通过全局校验和测试。

## 新会话如何开始

所有 Agent 都从 [`01-agent-layer/AGENT_GUIDE.md`](01-agent-layer/AGENT_GUIDE.md) 进入。根目录的 `AGENTS.md`、`CLAUDE.md`、`GEMINI.md`、Cursor 和 Copilot 文件只是适配入口。

固定顺序：

1. 读 `AGENT_GUIDE.md` 和 `01-agent-layer/core/invariants.md`。
2. 不知道做哪个事项时，读 `02-work-items/WORK_INDEX.md`。
3. 读目标事项的 `STATUS.md`、`handoff.md`、`brief.md`。
4. 读 `01-agent-layer/router/context-router.md`，只加载当前场景需要的上下文。
5. 检查 `git status`，保留其他人尚未提交的改动。

也可以让脚本列出最小加载清单：

```text
python 01-agent-layer/scripts/workspace.py context <item-id> --mode auto
```

混合任务可以写 `--mode coding,review,sync`。清单只列路径，不代替实际阅读。

## 新建事项

```text
python 01-agent-layer/scripts/workspace.py new-item my-requirement --title "需求标题" --workspace requirement --workspace investigation
```

命令会同时创建 `02-work-items/active/<item-id>/` 和 `03-session-state/active/<item-id>/`，并登记 `02-work-items/WORK_INDEX.md`。

创建后先补齐 `brief.md`。`workspaces/` 下每个子目录代表一条隔离操作流；需要排查时使用独立 stream，不与其他事项共用工作区。

## Codex 主控与 DeepSeek Harness

直接向 Codex 下单即可。Codex 负责建项、写验收标准、写委派任务单、调用桌面版 DeepSeek Harness、回收结果、独立检查和测试。

标准流程：

1. Codex 从 `01-agent-layer/templates/deepseek-task.md` 写任务单。
2. Codex 通过桌面宿主 API 创建可见 Workspace 和 Session。
3. DeepSeek 在指定 cwd 中实现，不提交 Git，不修改事项状态。
4. Codex 检查 diff、独立运行测试，并按 `brief.md` 做行为回归。
5. 有问题时在同一 session 下发修复轮次。
6. 通过后由 Codex 更新状态、交接并提交。

启动和检查桌面实时模式：

```text
python 01-agent-layer/scripts/dsh_desktop_bridge.py launch
python 01-agent-layer/scripts/dsh_desktop_bridge.py doctor
```

手动委派：

```text
python 01-agent-layer/scripts/dsh_desktop_bridge.py delegate --item <item-id> --task-file <task.md> --cwd <execution-workdir> --label implement
```

委派证据保存在 `02-work-items/active/<item-id>/artifacts/delegation/`。DeepSeek 的“完成”只是待审查声明，不是验收结论。

Codex 每轮审查单独保存到：

```text
02-work-items/active/<item-id>/reviews/<task-id>/round-<n>/
  review.md
  diff.patch
  test-output.txt
```

上一轮审查不覆盖。`STATUS.md` 只链接当前审查结论。

## 状态与交接

- `STATUS.md` 回答“现在在哪里”，是当前事实视图。
- `handoff.md` 回答“下一步从哪开始”，必须包含唯一下一步、必读顺序、已知坑和验证命令。
- `journal/` 只追加实际动作、结果和证据。
- `decisions.md` 记录会影响范围、风险或后续会话的取舍。
- `reviews/` 保存 Codex 每轮独立审查，与 DeepSeek 委派记录分开。
- 事项知识验证且可复用后，才提升到 `03-session-state/knowledge/`。

暂停、换 Agent、切换任务或上下文压缩前，必须同步 `STATUS.md` 与 `handoff.md`。

## 归档

归档要同时移动工作和状态两个目录，再更新索引：

```text
git mv 02-work-items/active/<item-id> 02-work-items/archived/<item-id>
git mv 03-session-state/active/<item-id> 03-session-state/archived/<item-id>
```

归档前确保最终状态、交接、验证证据和可复用知识都已落盘。

## 验证与 Git

```text
python 01-agent-layer/scripts/workspace.py validate
python -m unittest discover -s 01-agent-layer/tests -v
```

启用提交前门禁：

```text
git config core.hooksPath .githooks
```

提交信息使用 `workspace: <全局规范或工具结果>` 或 `item(<item-id>): <结果>`。只提交本次范围内的文件，不推送到远端、不合并共享分支、不改写历史，除非用户明确要求。

## 每层入口

- [`01-agent-layer/README.md`](01-agent-layer/README.md)
- [`02-work-items/README.md`](02-work-items/README.md)
- [`03-session-state/README.md`](03-session-state/README.md)

## 安全默认

可逆、低风险、范围内的工作可以自主完成。删除、覆盖未提交内容、改写历史、发布、部署、付费、发送外部消息、推送共享分支，以及会显著改变结果的关键歧义，必须先确认。

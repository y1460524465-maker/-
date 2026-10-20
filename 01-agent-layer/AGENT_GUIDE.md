# AGENT_GUIDE — 本地 AI 工作区统一入口

> 本文件是所有 Agent、会话和文档工作的唯一入口。根目录适配文件只转发到这里，不得复制或改写规则。
>
> 为避免重复加载，详细规则按职责只保留在下列单一正文中；它们都是本规范的组成部分：
>
> - 行为不变量：`core/invariants.md`
> - 场景判断：`router/context-router.md`
> - 状态与交接：`core/state-contract.md`
> - Git 与并发：`core/git-protocol.md`
> - 场景执行：`contexts/{coding,delegation,codex-review,sync}.md`

## 1. 工作区的目标

工作区用文件和 Git 保存工作事实，让新会话、新 Agent 或新文档能从当前状态继续，并保留已经生效的需求、范围、验收标准、风险和禁止动作。

系统分为三层：

```text
01-agent-layer/     Agent 如何工作：规范、路由、模板、脚本、测试
02-work-items/      正在做什么：需求、代码、草稿、交付物、证据
03-session-state/   做到哪里：状态、交接、决策、日志、知识
```

`01-agent-layer` 是共享规则层。每个工程拥有独立的 `02-work-items`、`03-session-state` 和 Git 历史，并通过本机目录联接共同使用同一份 `01-agent-layer`。

## 2. 新工程

在当前 Windows 电脑上创建新工程：

```text
powershell -NoProfile -File 01-agent-layer/scripts/New-AiProject.ps1 -Path E:\AI-Projects\Project-A
```

生成结果：

```text
Project-A/
  01-agent-layer/      指向共享规则层
  02-work-items/       本工程独立事项
  03-session-state/    本工程独立状态
  .ai-workspace.json   工程元数据
  .git/                本工程 Git 历史
  AGENTS.md 等         本工程适配入口
```

修改共享规则后，所有工程立即使用新版本。共享规则变更必须先通过全局结构校验和测试；错误变更会影响所有工程。

## 3. 每次会话的启动顺序

在开始实质工作前：

1. 读取本文件与 `core/invariants.md`。
2. 从当前工程读取 `02-work-items/WORK_INDEX.md`，确定目标事项。
3. 读取该事项的 `STATUS.md`、`handoff.md` 和 `brief.md`。
4. 读取 `router/context-router.md`，判断当前任务段属于 `coding`、`delegation`、`review`、`sync`，或需要组合加载。
5. 只加载被选中的 `contexts/*.md`，再按 handoff 引用读取代码、文档或知识。
6. 检查 `git status` 和最近提交，识别并保护他人尚未提交的工作。
7. 用一句话确认当前事项、目标和边界。

生成加载清单：

```text
python 01-agent-layer/scripts/workspace.py context <item-id> --mode auto
```

清单只列出路径，不代替实际阅读。

## 4. 文件职责

| 文件 | 唯一职责 |
|---|---|
| `core/invariants.md` | 不可丢失的行为底线 |
| `router/context-router.md` | 场景判断和模块组合 |
| `core/state-contract.md` | STATUS、handoff、journal、知识文件契约 |
| `core/git-protocol.md` | 检查点、暂存、并发和禁止动作 |
| `contexts/coding.md` | 实现、修复、测试和构建方法 |
| `contexts/delegation.md` | 写任务单、调用 DeepSeek、收回结果 |
| `contexts/codex-review.md` | Codex 独立审查、测试和判定 |
| `contexts/sync.md` | 状态同步、交接、提交和归档 |

不要把同一规则复制到多个文件。新增规则时先判断它属于哪个单一职责文件，再更新入口或路由。

## 5. 事项结构

每个事项由工作和状态两个同 ID 目录配对：

```text
02-work-items/{active,archived}/<item-id>/
  brief.md
  workspaces/<stream>/
  drafts/
  artifacts/
    delegation/
  reviews/<task-id>/round-<n>/
  archive/

03-session-state/{active,archived}/<item-id>/
  STATUS.md
  handoff.md
  decisions.md
  journal/
  knowledge/
```

- `brief.md` 保存需求和验收基线。
- `workspaces/<stream>/` 保存具体工作现场。
- `artifacts/` 保存交付物和委派证据。
- `reviews/` 保存 Codex 每轮独立审查，不与其他证据堆叠。
- `STATUS.md` 是当前事实，`handoff.md` 是可执行交接。

默认只写当前事项配对的工作和状态目录。全局规范、模板、脚本、索引或其他事项属于显式例外，必须说明原因。

## 6. 创建、恢复与归档

创建事项：

```text
python 01-agent-layer/scripts/workspace.py new-item <slug> --title "<标题>" --workspace <stream>
```

命令同时创建工作和状态目录并登记项目索引。归档时两个目录一起移动：

```text
git mv 02-work-items/active/<item-id> 02-work-items/archived/<item-id>
git mv 03-session-state/active/<item-id> 03-session-state/archived/<item-id>
```

## 7. 自主执行与询问

可以自主完成：只读调查、范围内可逆修改、草稿、journal、状态更新、测试、校验和不含外部副作用的本地提交。

必须先询问：目标或验收存在会改变结果的歧义、删除或覆盖用户内容、改写 Git 历史、发布部署、发送外部消息、使用敏感数据、扩大权限、修改其他事项业务内容，或发现无法调和的规则冲突。

一次只问一个决定性问题，并给出建议默认值。

## 8. 审查与完成

DeepSeek 返回后，Codex 必须加载 `contexts/codex-review.md`，独立检查文件、diff、测试和边界。执行者的“完成”只是待审查声明。

每轮审查写入独立目录：

```text
02-work-items/{active,archived}/<item-id>/reviews/<task-id>/round-<n>/
  review.md
  diff.patch
  test-output.txt
```

不得覆盖上一轮审查。`STATUS.md` 只链接当前审查目录，不复制完整报告。

只有同时满足以下条件才能声称完成：

- 用户要求的交付物存在；
- 对照 `brief.md` 和当前边界完成行为回归；
- 相关测试或检查实际运行并读取结果；
- 审查证据已保存；
- `STATUS.md` 与 `handoff.md` 反映真实状态；
- 结构校验通过，范围内改动已形成 Git 检查点。

## 9. 加载不得丢失行为

- 用户本轮新约束与 `brief.md` 中原有约束同时有效。
- 模式切换后保留事项、验收标准、当前边界和已知坑。
- 上下文压缩、换 Agent 或换会话后，从文件与 Git 重新建立事实。
- 只缩小无关信息的加载，不跳过核心、状态、交接和场景规则。

## 10. 冲突与优先级

1. 用户最新明确指令和 `brief.md` 是需求权威。
2. 实际文件、测试输出和 Git 历史是实施事实。
3. 最新 `STATUS.md` 是当前视图，`handoff.md` 是执行入口。
4. 发现冲突时停止静默猜测，修正记录并在 journal 写明原因。

若本入口与详细规则文件冲突，应先修正冲突；涉及行为底线时以 `core/invariants.md` 为准，并立即同步更新本入口。

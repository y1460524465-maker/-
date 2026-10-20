# State Contract

## 1. 文件职责

| 文件 | 回答的问题 | 写入方式 |
|---|---|---|
| `brief.md` | 为什么做、做到什么算完成、范围与限制是什么 | 需求变化时更新 |
| `STATUS.md` | 现在在哪里、已完成什么、阻塞是什么、最近证据是什么 | 覆盖为最新事实 |
| `handoff.md` | 下一个 Agent 从哪里开始、不要重复什么、要避开什么 | 每次交接或暂停时重写 |
| `decisions.md` | 做过哪些有代价的取舍 | 追加决策表 |
| `journal/YYYY-MM-DD.md` | 今天实际做了什么、发现了什么 | 只追加 |
| `03-session-state/{active,archived}/<item-id>/knowledge/` | 本事项中可复用的候选知识 | 新条目或更新验证状态 |
| `drafts/` | 未定稿文档 | 可迭代 |
| `artifacts/` | 可交付结果与证据 | 定稿后放入 |
| `reviews/<task-id>/round-<n>/` | Codex 对单轮执行结果的独立审查证据 | 每轮新建，不覆盖 |
| `workspaces/<stream>/` | 具体操作工作区 | 按操作流隔离 |
| `archive/` | 本事项内部历史与封存材料 | 不覆盖历史 |

## 2. STATUS 契约

YAML front matter 必须包含：

```yaml
---
id: "YYYY-MM-DD-slug"
title: "标题"
status: planning|active|blocked|review|done|archived
updated: "YYYY-MM-DD"
owner: "agent 或 unassigned"
---
```

正文固定包含：

- `## 已完成`
- `## 正在做`
- `## 下一步`
- `## 阻塞与待确认`
- `## 最近验证`
- `## 当前边界与有效不变量`

要求：

- “已完成”只写已经落地且有凭据的结果；
- “正在做”写当前真实活动；
- “下一步”必须可执行；
- 阻塞必须写明需要谁做什么决定；
- 验证必须写命令/检查与结果；
- 当前边界保存本轮不能丢的约束摘要，指向 `brief.md` 的详细原文。

## 3. handoff 契约

正文固定包含：

- `## 唯一下一步`
- `## 必读顺序`
- `## 已完成，不要重复`
- `## 已知坑与禁止动作`
- `## 可直接运行的验证`

要求：

- 唯一下一步必须指向具体文件、位置或命令；
- 必读顺序只列恢复工作真正需要的文件；
- 不要重复项要说明完成证据；
- 已知坑要写现象、原因和正确做法；
- 验证命令必须可从仓库根目录执行，并写明上次结果。

## 4. journal 契约

每条记录至少包含：

```text
### HH:MM — <Agent/人名> — <步骤>
- 路由：coding / review / sync / mixed（可选）
- 动作：
- 结果：
- 证据：
- 下一步：
```

journal 不做“最终总结”的替代品；最终状态同步到 STATUS 和 handoff。不得删除他人 journal 记录。

## 5. review 契约

每轮 Codex 审查必须创建独立目录：

```text
02-work-items/{active,archived}/<item-id>/reviews/<task-id>/round-<n>/
  review.md
  diff.patch
  test-output.txt
```

- `review.md` 从 `01-agent-layer/templates/review/review.md` 开始，记录审查范围、命令、发现和结论。
- `diff.patch` 保存本次实际检查的变更。
- `test-output.txt` 保存 Codex 独立执行验证的原始输出。
- 同一任务的新一轮审查使用新的 `round-<n>`，禁止覆盖旧结论。
- `STATUS.md` 只记录当前结论和目录入口；完整内容留在 review 目录。

## 6. 更新时机

- 完成有意义步骤：journal。
- 状态改变：STATUS。
- 阻塞或风险：STATUS；若影响下次开始，同时更新 handoff。
- 需求、范围、验收标准变化：先更新 brief，再更新 STATUS，并记录 decision。
- 暂停、交接、切换 Agent：STATUS + handoff + journal。
- 提交、归档：sync 全部完成后提交。

## 7. 冲突处理

如果聊天内容、STATUS、journal、Git 历史互相矛盾：

1. 以用户最新明确指令和 `brief.md` 为需求权威；
2. 以实际文件、测试输出和 Git 历史为实施事实；
3. 以最新 `STATUS.md` 为当前视图；
4. 不静默选择一方，修正记录并在 journal 写明冲突与解决方式。

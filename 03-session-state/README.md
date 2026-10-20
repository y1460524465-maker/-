# 03 Session State

这一层回答“已经做到哪里、下一步是什么、哪些经验可以复用”。它为每个工作事项保存可恢复的跨会话记忆。

## 结构

```text
knowledge/
  INDEX.md
  <verified-knowledge>.md
active/
  <item-id>/
    STATUS.md
    handoff.md
    decisions.md
    journal/
    knowledge/
archived/
  <item-id>/
    STATUS.md
    handoff.md
    decisions.md
    journal/
    knowledge/
```

每个 `<item-id>` 必须与 `02-work-items/` 下同层级、同 ID 的目录配对。

## 核心文件

| 文件 | 回答的问题 | 更新方式 |
|---|---|---|
| `STATUS.md` | 已完成什么、正在做什么、下一步、阻塞、最近验证 | 覆盖为最新事实 |
| `handoff.md` | 下一个 Agent 具体从哪里开始、不要重复什么、避开哪些坑 | 每次暂停、交接或切换 Agent 时重写 |
| `decisions.md` | 哪些取舍会影响范围、风险或后续会话 | 追加 |
| `journal/` | 实际做了什么、看到什么结果、证据是什么 | 只追加 |
| `knowledge/` | 本事项产生但尚未全局复用的知识 | 按条目维护验证状态 |

`STATUS.md` 和 `handoff.md` 不能只在聊天里说，必须写入文件并与工作改动同批提交。

Codex 每轮审查的完整证据保存在工作层：

```text
02-work-items/{active,archived}/<item-id>/reviews/<task-id>/round-<n>/
```

状态层只记录结论和链接，不复制完整审查报告。

## 恢复顺序

1. 从 `02-work-items/WORK_INDEX.md` 确定事项 ID。
2. 读本层该事项的 `STATUS.md` 和 `handoff.md`。
3. 读工作层的 `brief.md`。
4. 按 `01-agent-layer/router/context-router.md` 加载场景上下文。
5. 用 Git diff、实际文件和测试复核记录，不把旧声明直接当成当前事实。

## 知识提升

事项内知识先放 `active/<item-id>/knowledge/`。只有已经验证、可跨事项复用、来源清楚且不含敏感信息的内容，才提升到本层根的 `knowledge/` 并登记 `INDEX.md`。

上传、发布或推送知识属于外部动作，必须得到用户明确指示。

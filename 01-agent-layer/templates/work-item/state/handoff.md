# Handoff — {{TITLE}}

> 给下一个 Agent 的可执行交接。不要写无法定位的动作。

## 唯一下一步

1. 打开 `brief.md`，补齐缺口或确认当前目标与验收标准。
2. 然后读取 `STATUS.md`、`01-agent-layer/router/context-router.md` 和对应场景上下文。

## 必读顺序

1. `01-agent-layer/AGENT_GUIDE.md`
2. `01-agent-layer/core/invariants.md`
3. `STATUS.md`
4. `brief.md`
5. `01-agent-layer/router/context-router.md`
6. 按任务场景选择 `01-agent-layer/contexts/coding.md`、`01-agent-layer/contexts/codex-review.md` 或 `01-agent-layer/contexts/sync.md`

## 已完成，不要重复

- 事项目录已创建，状态、交接、需求、决策、日志和工作区骨架已经存在。

## 已知坑与禁止动作

- 不要把其他事项的状态、草稿或验证结论复制进来。
- 不要在 `brief.md` 仍为空或验收标准不明时进行大范围实现。
- 每轮 Codex 审查写入 `reviews/<task-id>/round-<n>/`，不要覆盖或混堆。
- 不要推送远端、改写 Git 历史或删除用户内容，除非用户明确要求。

## 可直接运行的验证

```text
python 01-agent-layer/scripts/workspace.py validate
```

上次结果：尚未运行。

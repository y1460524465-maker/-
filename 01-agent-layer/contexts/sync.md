# Sync Context

仅在状态同步、交接、提交、归档、知识提升和索引维护类任务中按需加载。

## 同步顺序

1. 重新读取当前事项的 `STATUS.md`、`handoff.md`、`brief.md` 和最近 journal。
2. 检查 `git status`，区分本次改动与他人/无关改动。
3. 追加 journal，记录实际动作、结果、证据和下一步。
4. 更新 `STATUS.md`，只写已经发生的事实。
5. 重写 `handoff.md`，让下一个 Agent 可以直接开始。
6. 如有取舍，更新 `decisions.md`。
7. DeepSeek 或其他执行 Agent 的 session-id、事件和最终结果留在 `artifacts/delegation/`。
8. Codex 每轮独立审查必须写入 `reviews/<task-id>/round-<n>/`，不得把多个轮次堆在同一目录。
9. 运行 `python 01-agent-layer/scripts/workspace.py validate`。
10. 只暂存本次范围，提交。
11. 提交后再次检查状态，确认记录与文件一致。

## STATUS 质量

- 已完成项必须有文件、提交或验证凭据。
- 正在做项保持在当前活动范围，不把计划写成进度。
- 下一步可直接执行。
- 阻塞写清需要谁做什么决定。
- 最近验证写实际结果，不写“应该通过”。
- 审查结论必须链接对应 `reviews/<task-id>/round-<n>/`。
- 当前边界保留本轮不可丢的约束。

## handoff 质量

唯一下一步必须足以行动，例如：

```text
从 `01-agent-layer/scripts/workspace.py` 的 `context_manifest()` 开始，补充非法 mode 的拒绝逻辑；
运行 `python -m unittest 01-agent-layer.tests.test_workspace.WorkspaceTests.test_context_manifest_for_modes -v`；
参考 `STATUS.md` 的“最近验证”和本文件“已知坑与禁止动作”。
```

不要写“继续完成剩余工作”。

## 提交与归档

- 提交信息使用 `item(<item-id>): <结果>`。
- 不提交无关改动。
- 不默认推送或合并共享分支。
- 归档使用 `git mv 02-work-items/active/<id> 02-work-items/archived/<id>`，更新总索引，保留最终 handoff 和验证记录。
- 归档不删除历史，不在归档事项中继续开发；需要新工作就新建事项。

## 知识提升

把事项知识提升到根 `03-session-state/knowledge/` 前，检查：

- 是否已验证；
- 是否可跨事项复用；
- 是否有来源与适用边界；
- 是否含敏感信息；
- 是否已登记到 `03-session-state/knowledge/INDEX.md`。

上传或发布知识属于外部动作，必须得到用户明确要求。

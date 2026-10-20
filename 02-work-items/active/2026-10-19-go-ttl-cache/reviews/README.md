# Reviews

每次 Codex 审查使用独立目录：

```text
<task-id>/round-<n>/
  review.md
  diff.patch
  test-output.txt
```

不得覆盖上一轮审查。

历史审查：

- `task-1-core/round-1/`：任务 1 阶段审查，通过。
- `task-2-cleanup/round-1/`：任务 2 清理逻辑审查，通过。
- `task-3-tests/round-1/`：任务 3 证据不可恢复，打回。
- `task-3-tests/round-2/`：同一 session 修复后的最终复审，通过。

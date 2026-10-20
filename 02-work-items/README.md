# 02 Work Items

这一层只保存“事情本身”：需求、代码工作区、草稿、交付物和证据。它不保存 Agent 规则，也不重复跨会话状态。

## 结构

```text
WORK_INDEX.md
active/
  <item-id>/
    brief.md
    workspaces/
      <stream>/
    drafts/
    artifacts/
    reviews/
    archive/
archived/
  <item-id>/
```

事项 ID 统一为 `YYYY-MM-DD-slug`。工作目录必须与 `03-session-state/` 下同 ID 的状态目录配对存在。

## 文件职责

- `brief.md`：需求基线、验收标准、范围、非目标和约束。
- `workspaces/<stream>/`：具体实现、排查或实验现场。一个事项可以有多条操作流，不同事项不能共用。
- `drafts/`：尚未定稿的文档。
- `artifacts/`：最终交付物、截图、测试输出、委派证据等。
- `reviews/`：Codex 每轮独立审查。`reviews/<task-id>/round-<n>/` 内保存 `review.md`、`diff.patch` 和 `test-output.txt`。
- `archive/`：本事项内部的旧版本或封存材料。

DeepSeek 的请求、事件和返回结果放在 `artifacts/delegation/`；Codex 的审查报告和独立测试证据放在 `reviews/`。两套证据不得混堆。

状态文件不放在这里。当前进度、交接、决策和过程日志位于 `03-session-state/` 的同名事项目录。

## 新建

```text
python 01-agent-layer/scripts/workspace.py new-item <slug> --title "<标题>" --workspace <stream>
```

该命令同时创建工作目录、状态目录并登记总索引。创建后先补齐 `brief.md`。

## 查找与恢复

先读 [`WORK_INDEX.md`](WORK_INDEX.md)，再读取目标的 `brief.md`，并转到 `03-session-state/active/<item-id>/` 阅读 `STATUS.md` 与 `handoff.md`。

## 归档

完成最终状态和验证后，把工作目录与状态目录一起移动到各自的 `archived/`，再更新 `WORK_INDEX.md`。归档表示停止继续开发，不删除历史。

# Active Work

这里只放正在进行的工作事项。事项 ID 默认格式为 `YYYY-MM-DD-<slug>`，并在 `03-session-state/active/` 下拥有同 ID 的状态目录。

创建事项：

```text
python 01-agent-layer/scripts/workspace.py new-item <slug> --title "<标题>" --workspace <stream>
```

完成后把工作目录移到 `02-work-items/archived/`，同时把状态目录移到 `03-session-state/archived/`。不要在已归档事项上继续新工作。

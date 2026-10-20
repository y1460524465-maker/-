# AI Collaboration Project

本工程使用共享的 `01-agent-layer`，并拥有独立的 `02-work-items`、`03-session-state` 和 Git 历史。

从这里开始的 Agent 必须先读取：

```text
01-agent-layer/AGENT_GUIDE.md
```

新事项通过共享工具创建：

```text
python 01-agent-layer/scripts/workspace.py new-item <slug> --title "<标题>" --workspace <stream>
```

工程级校验：

```text
python 01-agent-layer/scripts/workspace.py validate
```

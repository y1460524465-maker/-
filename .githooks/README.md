# Git Hooks

本仓库使用 `.githooks/pre-commit` 在提交前运行：

```text
python 01-agent-layer/scripts/workspace.py validate
```

启用当前仓库：

```text
git config core.hooksPath .githooks
```

Hook 在 Python 不可用、结构校验失败或命令异常时返回非零，阻止提交。不要使用 `--no-verify` 绕过；先修复状态、目录或索引。

新工程由 `New-AiProject.ps1` 自动设置：

```text
git config core.hooksPath 01-agent-layer/githooks
```

因此工程使用共享层中的门禁，不维护第二份 hook。

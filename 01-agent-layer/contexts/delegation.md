# DeepSeek Harness Delegation Context

仅在把实现任务交给本机 DeepSeek Harness 桌面版或其他执行 Agent 时加载。

## 角色边界

- Codex 是主控、验收者和唯一提交者。
- DeepSeek 是实现者，只修改指定 cwd 内的任务范围。
- DeepSeek 不提交 Git，不修改 `STATUS.md`、`handoff.md`、`brief.md`、`01-agent-layer/AGENT_GUIDE.md`，不处理其他事项。
- 用户只向 Codex 下单；Codex 负责把需求转成可执行任务单。

## 下单前

1. 确认目标事项和工作区。
2. 补齐 `brief.md` 的目标、验收标准、范围和非目标。
3. 选择执行 cwd：
   - 优先使用该事项的隔离目录，例如 `workspaces/implementation/`；
   - 外部代码仓库必须是用户确认的路径；
   - 不使用会覆盖他人未提交工作的目录。
4. 从 `01-agent-layer/templates/deepseek-task.md` 写任务单，至少包含：
   - 目标和不做事项；
   - 允许修改的文件/目录；
   - 验收标准；
   - 可直接运行的测试命令；
   - 禁止提交 Git 和修改治理文件的规则；
   - 输出摘要格式。
5. 记录预期的 Git 基线。

## 调用

```text
python 01-agent-layer/scripts/dsh_desktop_bridge.py launch
python 01-agent-layer/scripts/dsh_desktop_bridge.py doctor
python 01-agent-layer/scripts/dsh_desktop_bridge.py delegate --item <item-id> --task-file <task.md> --cwd <cwd> --label implement
```

桌面桥会通过本机回环宿主 API 创建 Workspace 和可见 Session，并自动切换到新会话。桥保存请求、完整事件、最终结果、元数据和 session-id。不要把 API Key 或认证 cookie 写入任务单。

如果桌面 app 当前是普通方式启动的，`doctor` 会失败。关闭 app 后运行 `launch`，再开始委派。不得静默改用 headless。

## 收回后

1. 读取 `artifacts/delegation/` 中的最终结果和元数据。
2. 检查 cwd 的 `git status`、`git diff` 和实际文件。
3. 由 Codex 运行任务单中的测试，不依赖 DeepSeek 的测试声明。
4. 对照 `brief.md` 做行为回归。
5. 把本轮 Codex 审查写入 `reviews/<task-id>/round-<n>/`，保存 `review.md`、`diff.patch` 和 `test-output.txt`。
6. 有问题时，用原 session-id 下发修复任务：

```text
python 01-agent-layer/scripts/dsh_desktop_bridge.py delegate ... --session-id <session-id> --label fix-1
```

7. 审查通过后，由 Codex 更新状态、交接并提交。

## 失败处理

- 桌面 app 普通启动：先关闭，再运行 `launch`。
- 桌面认证失败：重启到 live 模式并重新运行 `doctor`；不要读取或打印认证 cookie。
- 新会话为 `danger-full-access`：桥会拒绝执行；先调整桌面默认权限。
- 超时：保留事件日志，检查 cwd 是否已有半成品；不自动重试有写入副作用的同一任务。
- 非零退出或无 final：视为失败。
- Git HEAD 变化：视为策略违规，先检查提交来源，再决定是否修复；不自动回滚。
- 执行者越界：停止，保留证据，向用户说明影响后再处理。

## Headless 降级

`01-agent-layer/scripts/dsh_bridge.py` 保留为明确降级方案。它不会把实时事件推送到桌面 UI，只会在完成后出现在“未分组”。只有在用户明确同意时才可使用。

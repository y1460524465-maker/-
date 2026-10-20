# Decisions — 接入 DeepSeek Harness 桌面版

只记录会影响实现、范围、风险或后续会话的取舍。普通执行细节写入 `journal/`，小问题不必制造决策。

| 日期 | 决策 | 原因 | 替代方案 | 错误代价 | 记录人 |
|---|---|---|---|---|---|
| 2026-10-19 | 使用 `dsh headless` 而不是桌面 UI 自动化 | 提供稳定 stdin、JSONL、session-id 和 cwd 接口 | 模拟鼠标键盘 | Computer Use 不可用时无法执行，且结果难结构化 | Codex |
| 2026-10-19 | 只允许 read-only/workspace-write | 让实现者能写入指定目录，同时阻止任意系统写入 | danger-full-access | 受限目录外任务需要用户提供更合适 cwd | Codex |
| 2026-10-19 | DeepSeek 不提交 Git | Codex 必须保留独立审查和测试门禁 | 允许执行者提交后审查 | 错误提交需要复杂回滚 | Codex |

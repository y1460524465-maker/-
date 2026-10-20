# Handoff — 分布式限流器中间件

## 唯一下一步

先运行 `python 01-agent-layer/scripts/dsh_desktop_bridge.py doctor` 确认桌面实时模式；若 Go 工具链仍缺失，停止并请用户决定是否恢复，然后把 `drafts/t1-task.md` 重新下发给 T1。

## 必读顺序

`01-agent-layer/AGENT_GUIDE.md` → `01-agent-layer/core/invariants.md` → 本事项 `STATUS.md` → `02-work-items/active/2026-10-19-distributed-rate-limiter/brief.md` → `drafts/implementation-plan.md` → `01-agent-layer/router/context-router.md` → `01-agent-layer/contexts/delegation.md`、`01-agent-layer/contexts/codex-review.md`、`01-agent-layer/contexts/sync.md`。

## 已完成，不要重复

用户已批准开始，指定 DeepSeek Harness；doctor 已通过，事项已建立；无需另问执行方式。

## 已知坑与禁止动作

- 使用桌面宿主实时模式，统一走 `01-agent-layer/scripts/dsh_desktop_bridge.py`；不得静默降级到 headless `dsh_bridge.py`。
- 主控不写实现/测试；Harness 不提交、不改治理。
- 初始 HEAD 36c2d74；等待 Harness 时不要提交改变 HEAD。
- 用户已要求删除本地 Go 工具链；当前不要自行重装。若 T1 需要 Go，先报告环境阻塞并等待用户决定。
- T1 审查前不得下发后端任务。

## 可直接运行的验证

python 01-agent-layer/scripts/dsh_desktop_bridge.py doctor
python 01-agent-layer/scripts/workspace.py validate

Go 工具链已删除，Go 产品测试当前不可运行；桌面桥状态需按当前环境重新检查。

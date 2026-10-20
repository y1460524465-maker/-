---
id: "2026-10-19-deepseek-harness-bridge"
title: "接入 DeepSeek Harness 桌面版"
status: archived
updated: "2026-10-19"
owner: "unassigned"
---

# STATUS — 接入 DeepSeek Harness 桌面版

> 当前事实视图。只写已经发生并有凭据的事实；详细历史写入 `journal/`。

## 已完成

> 历史归档：本事项记录早期 headless 接入。当前标准已切换到桌面宿主实时模式，以 `01-agent-layer/AGENT_GUIDE.md` 为准。

- 已创建 `bridge` 与 `validation` 两个隔离工作区。
- 已确认桌面版安装路径：`D:\Apps\DeepSeek Harness`。
- 已确认无窗口入口 `dsh headless` 支持 cwd、JSON 事件和 session-id。
- 已验证默认 headless profile 缺少桌面凭据，需显式启用 credentials 插件。
- 已验证使用 credential patch 后可以读取工作区并返回模型结果。
- 已实现 `scripts/dsh_bridge.py`，支持 doctor、委派、session 续接、超时、错误、敏感环境过滤和 Git HEAD 变动检测。
- 已增加 `delegation` 渐进式路由、任务模板和 Codex 审查门禁。
- 已完成真实 DeepSeek 写入验证：创建 `src/word_count.py` 和测试，Codex 独立复跑 3/3 通过。
- 已使用同一 session 完成无写入续接验证。

## 正在做

- 无；接入工作已完成并归档。

## 下一步

- [ ] 无后续动作。需要新工作请创建独立事项。

## 阻塞与待确认

- 无。

## 最近验证

- 2026-10-19：`dsh headless --json` 使用 credential patch 后成功返回 `STDIN_OK`。
- 2026-10-19：headless 事件包含 `sessionId`、`cwd`、工具调用和 final 结果。
- 2026-10-19：`python -m unittest discover -s 01-agent-layer/tests -p test_dsh_bridge.py -v` 7/7 通过。
- 2026-10-19：真实 session `session-13295a30-c452-4be7-af41-c02129c3f8cc` 完成实现和同一会话续接。
- 2026-10-19：演示工作区测试 3/3 通过（路径已随分层迁移清理）。

## 当前边界与有效不变量

- 只允许 Codex 通过 `dsh --profile headless` 调用，不依赖桌面 UI 自动化。
- DeepSeek 只负责实现，不得提交 Git 或更新 STATUS/handoff。
- Codex 必须独立审查并运行验证后才能提交。
- 凭据不得进入任务单、日志或 Git。

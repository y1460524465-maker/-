# Handoff — 简单 HTML 网页

> 给下一个 Agent 的可执行交接。不要写无法定位的动作。

## 唯一下一步

1. 页面已实现、测试和浏览器验收完成，没有后续实现任务。
2. 用户要求修改时，在同一事项继续，并先读取本文件和 `STATUS.md`。

## 必读顺序

1. `01-agent-layer/AGENT_GUIDE.md`
2. `01-agent-layer/core/invariants.md`
3. `03-session-state/active/2026-10-19-simple-html-page/STATUS.md`
4. `02-work-items/active/2026-10-19-simple-html-page/brief.md`
5. `01-agent-layer/router/context-router.md`
6. 按任务场景选择 `01-agent-layer/contexts/coding.md`、`01-agent-layer/contexts/codex-review.md` 或 `01-agent-layer/contexts/sync.md`

## 已完成，不要重复

- 页面需求、验收标准和 DeepSeek 任务单已经准备完毕。
- DeepSeek 已创建单文件页面和 6 项结构测试。
- Codex 已独立完成测试、桌面/移动布局检查和按钮交互检查。

## 已知坑与禁止动作

- 不要引入 CDN、框架或构建工具。
- 不要把页面直接写入仓库根目录。
- 不接受 DeepSeek 未实际运行的测试声明。
- 394px 左右的 Edge 普通 headless 截图会被浏览器最小窗口裁切；移动布局应使用 CDP 设备模拟验证。
- 不要推送远端、改写 Git 历史或删除用户内容，除非用户明确要求。

## 可直接运行的验证

```text
python 01-agent-layer/scripts/workspace.py validate
python -m unittest discover -s 02-work-items/active/2026-10-19-simple-html-page/workspaces/implementation/tests -v
```

上次结果：2026-10-19，结构测试 6/6 通过，浏览器布局和交互验证通过。

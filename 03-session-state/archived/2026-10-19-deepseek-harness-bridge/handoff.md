# Handoff — 接入 DeepSeek Harness 桌面版

> 给下一个 Agent 的可执行交接。不要写无法定位的动作。

状态：已归档。委派桥、测试和使用说明已经完成；本事项不再承接新工作。

## 唯一下一步

1. 没有后续开发任务。
2. 需要使用时读取 `README.md` 的“Codex 主控 + DeepSeek Harness 桌面版”章节和 `contexts/delegation.md`。

## 必读顺序

1. `01-agent-layer/AGENT_GUIDE.md`
2. `01-agent-layer/core/invariants.md`
3. `03-session-state/archived/2026-10-19-deepseek-harness-bridge/STATUS.md`
4. `02-work-items/archived/2026-10-19-deepseek-harness-bridge/brief.md`
5. `01-agent-layer/router/context-router.md`
6. 按任务场景选择 `01-agent-layer/contexts/delegation.md`、`01-agent-layer/contexts/codex-review.md` 或 `01-agent-layer/contexts/sync.md`

## 已完成，不要重复

- 已完成 DeepSeek Harness 安装路径、headless 入口、凭据 patch 和读取能力探查。
- 不要再次尝试通过 Computer Use 操作桌面窗口；当前原生管道不可用，也无必要。
- `scripts/dsh_bridge.py`、测试、delegation 路由和任务模板已经实现。
- 真实 DeepSeek 写入与 session 续接已经验证。

## 已知坑与禁止动作

- headless 默认禁用 credentials，必须使用 `tools/dsh/headless-codex.patch.yml`。
- 不要读取或打印 `.credentials.yaml` 的秘密值。
- 不要使用 `danger-full-access`。
- 不要让 DeepSeek 在真实主分支上提交。
- 演示事项 `2026-10-19-dsh-bridge-demo` 中的代码是验证样例，不是当前工作区的业务代码。
- 不要推送远端、改写 Git 历史或删除用户内容，除非用户明确要求。

## 可直接运行的验证

```text
python 01-agent-layer/scripts/workspace.py validate
```

上次结果：2026-10-19 结构校验 `OK`，全量单元测试通过。

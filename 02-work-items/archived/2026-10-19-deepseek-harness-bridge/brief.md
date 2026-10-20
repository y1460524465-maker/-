# Brief — 接入 DeepSeek Harness 桌面版

> 本文件保存需求和验收基线。用户原始表述尽量逐字保留，不要用 Agent 的转述覆盖它。

## 用户原始要求

“我该怎么使用，我希望通过codex进行主任务下单，然后分发到我的deepseek harness 进行代码实习和其他功能实现， 执行后返回codex进行审查和测试”

补充确认：“我希望调用的是 deepseek harness 桌面版”。

## 目标

建立 Codex 主控、DeepSeek Harness 桌面版执行实现、Codex 独立审查和测试的标准工作流，并保存可恢复的会话与证据。

## 验收标准

- [ ] Codex 能通过桌面版附带的 `dsh headless` 提交实现任务。
- [ ] DeepSeek 在受限工作目录中执行，不提交 Git，不修改事项治理文件。
- [ ] 每轮委派保存请求、事件、最终结果、元数据和 session-id。
- [ ] Codex 能读取变更并独立运行测试，不采信 DeepSeek 的完成声明。
- [ ] Codex 能使用同一 session-id 下发修复任务。
- [ ] 文档明确用户如何下单、查看结果和触发修复轮次。

## 范围

- DeepSeek Harness 桌面版 headless 入口。
- 当前 Git 工作区中的委派桥、场景规范、任务模板和测试。
- 单执行者、Codex 审查的单主控流程。

## 非目标

- 不通过鼠标键盘操作桌面 UI。
- 不让 DeepSeek 自动合并、推送或归档。
- 不绕过 Codex 的审查、测试和 Git 门禁。
- 不把 API Key 写入仓库或任务单。

## 约束

- 遵循 `01-agent-layer/AGENT_GUIDE.md` 与 `01-agent-layer/core/invariants.md`。
- 默认只写入本事项目录。
- 委派执行默认使用 `workspace-write` sandbox。
- 凭据只通过桌面版本地 credentials 插件读取。

## 开放问题

- 无。

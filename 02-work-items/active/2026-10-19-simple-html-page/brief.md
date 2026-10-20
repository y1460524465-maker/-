# Brief — 简单 HTML 网页

> 本文件保存需求和验收基线。用户原始表述尽量逐字保留，不要用 Agent 的转述覆盖它。

## 用户原始要求

“我需要你在deepseek harness中写一个简单的html网页”

## 目标

由 DeepSeek Harness 在隔离工作区实现一个可直接打开的单文件“AI 工作台”响应式网页，并由 Codex 审查和测试。

## 验收标准

- [x] 由 DeepSeek 创建 `index.html`。
- [x] 页面为中文、响应式、无外部依赖。
- [x] 三个功能卡片和按钮交互完整。
- [x] 结构测试通过。
- [x] Codex 独立复跑测试。

## 范围

- 单个 `index.html` 与一个标准库结构测试。

## 非目标

- 不接真实后端或数据。
- 不引入前端框架、构建链或 CDN。
- 不发布到线上。

## 约束

- 遵循 `01-agent-layer/AGENT_GUIDE.md` 与 `01-agent-layer/core/invariants.md`。
- 默认只写入本事项目录。
- DeepSeek 不提交 Git。

## 开放问题

- 页面主题采用通用 AI 工作台落地页；若用户需要品牌化视觉，可后续修改。

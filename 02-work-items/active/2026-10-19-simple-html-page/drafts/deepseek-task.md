# DeepSeek Implementation Task

## 事项

- Item ID：2026-10-19-simple-html-page
- 工作目录：当前进程 cwd，即本事项的 `workspaces/implementation/`
- 角色：实现执行者；Codex 是审查者和唯一提交者

## 目标

在当前目录创建一个可直接打开的单文件网页 `index.html`，主题为“AI 工作台”。要求：

- 使用中文，`<html lang="zh-CN">`
- 包含响应式 viewport
- 页面标题和主标题均为“AI 工作台”
- 包含一段简洁介绍：“让工作持续、可见、可交接”
- 包含三个功能卡片，分别介绍：工作事项、跨会话状态、DeepSeek 执行
- 包含一个按钮，id 为 `start-button`，文字为“开始一个事项”
- 包含一个状态区域，id 为 `start-status`
- 点击按钮后，状态文字变为“事项工作区已准备好”，按钮禁用
- CSS 和 JavaScript 内嵌在 `index.html` 中
- 不引用任何外部字体、图片、CSS、JavaScript 或 CDN
- 视觉简洁、现代、适合桌面和手机
- 使用语义化 HTML，并保证基本键盘可访问性

同时创建 `tests/test_index.py`，使用 Python 标准库 `unittest` 和 `html.parser`，至少验证：

1. 页面有正确的 lang、viewport、title 和 h1；
2. 三个功能卡片都存在；
3. 按钮和状态区域的 id 正确；
4. 页面没有引用外部 CDN 资源。

## 验收标准

- [ ] `index.html` 可直接在浏览器打开，不依赖构建工具。
- [ ] 页面满足上述内容与交互要求。
- [ ] `tests/test_index.py` 覆盖指定结构。
- [ ] `python -m unittest discover -s tests -v` 实际通过。
- [ ] 未修改当前工作目录之外的文件。

## 允许修改

- 当前工作目录内的 `index.html`
- 当前工作目录内的 `tests/`

## 禁止动作

- 不提交 Git，不推送，不合并，不改写历史。
- 不修改 `STATUS.md`、`handoff.md`、`brief.md`、`01-agent-layer/AGENT_GUIDE.md` 或其他事项。
- 不读取、打印或复制凭据。
- 不访问网络。
- 不引入 npm、前端框架或构建步骤。
- 不把未运行的检查写成已通过。

## 验证

实际运行并报告：

```text
python -m unittest discover -s tests -v
```

## 输出约定

完成后只回报：

1. 修改了哪些文件；
2. 运行了哪些命令及真实结果；
3. 哪些验收标准已满足；
4. 剩余问题、风险或阻塞。

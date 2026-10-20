# DeepSeek Harness 桌面实时桥设计

## 1. 目标

Codex 下发的任务不再进入独立 headless 进程，而是通过正在运行的 DeepSeek Harness 桌面宿主创建可见会话。用户在桌面窗口中实时看到会话标题、思考、工具调用和输出；Codex 等待 `turn/end` 后再独立审查、测试和提交。

## 2. 根因

- 现有桥调用 `dsh --profile headless`，该进程拥有自己的事件循环和会话日志。
- headless 会话可以持久化，但不会把实时事件推送进桌面 app 的渲染器。
- 桌面 UI 按 Workspace 分组；headless 会话只能作为“未分组”在刷新后出现。
- 桌面 app 已经运行一个本地宿主 HTTP 服务，UI 通过它实时接收事件；应复用这个宿主，而不是另起 headless。

## 3. 接入方式

桌面 app 以本机回环调试端口启动：

```text
DeepSeek Harness.exe --remote-debugging-port=9226
```

桥通过 CDP 读取当前桌面进程的：

- 宿主监听端口；
- `dsh-auth-*` httpOnly cookie。

认证值只在内存中使用，不写仓库、不写任务单、不打印。宿主 API 只访问 `127.0.0.1`。

## 4. 流程

```text
Codex
  -> 连接桌面 app CDP
  -> 识别宿主端口和当前认证 cookie
  -> workspace/create（按 execution cwd）
  -> workspace/rename（item-id + title）
  -> session/create（带 session-id）
  -> session/prompt（任务单全文）
  -> 桌面 UI 实时显示
  -> 轮询 session/page 直到新 turn/end
  -> 保存事件和最终答复
  -> Codex 独立审查、测试、提交
```

修复轮次使用同一 session-id，不创建新会话。

## 5. 命令

```text
python scripts/dsh_desktop_bridge.py launch
python scripts/dsh_desktop_bridge.py doctor
python scripts/dsh_desktop_bridge.py delegate --item <id> --task-file <task.md> --cwd <cwd> --label implement
```

`launch` 启动带回环调试端口的桌面 app。若 app 已以普通方式启动，`doctor` 会明确提示先关闭再运行 `launch`。

## 6. 证据

每轮保存与 headless 相同类型的证据：

```text
artifacts/delegation/<timestamp>-<label>-request.md
artifacts/delegation/<timestamp>-<label>-events.jsonl
artifacts/delegation/<timestamp>-<label>-result.md
artifacts/delegation/<timestamp>-<label>-meta.json
```

元数据额外记录 desktop host port、workspace-id 和实际 session-id，不记录 cookie。

## 7. 安全与失败处理

- 只允许 `workspace-write` 类桌面会话；不操作用户已有 `danger-full-access` 会话。
- 不调用 `headless` 作为桌面模式的实现。
- CDP/宿主连接失败、cookie 无有效项、prompt 被拒绝、超时、未出现 `turn/end` 都视为失败。
- 应用必须先以 live 模式启动；普通启动的 app 无法被可靠控制。
- 不自动推送、合并或改写历史。
- headless 桥保留，作为桌面不可用时的显式降级选项。

## 8. 验收

- 假宿主 API 测试证明请求路径、认证、workspace/session/prompt、轮询和结果解析正确。
- 真实任务在桌面窗口实时出现并完成。
- Codex 从 `session/page` 读取完整事件和最终答复。
- 同一 session-id 能继续修复。
- 全量测试和结构校验通过。

# DeepSeek 桌面实时桥实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将标准 DeepSeek 委派从 headless 切换到桌面宿主，让用户在桌面 app 中实时看到执行过程。

**Architecture:** CDP 发现桌面宿主端口与认证 cookie；客户端通过本地 `/api` 创建 Workspace 和 Session、提交 prompt；轮询 `session/page` 解析新 `turn/end` 和最终答复。

**Tech Stack:** Python 3.12、`websocket-client`、`psutil`、DeepSeek Desktop Host HTTP API、`unittest`。

**Spec:** `docs/superpowers/specs/2026-10-19-desktop-live-bridge-design.md`

**Execution status:** Complete on 2026-10-19. Verification evidence: `docs/verification/2026-10-19-desktop-live-verification.md`.

## Global Constraints

- 只在 `127.0.0.1` 上连接 DeepSeek 桌面宿主。
- 认证 cookie 只在内存中使用，不写文件、不打印。
- 只用桌面宿主 API 创建可见会话；headless 仅保留为显式降级。
- Codex 必须独立审查和测试后才提交。
- 测试不得连接真实 DeepSeek 模型或修改真实桌面状态。

## Review Focus

- 多个 `dsh-auth-*` cookie 中只有当前宿主有效，桥必须逐个探测并选择正确项。
- 桌面 app 普通启动时没有 CDP 端口，桥必须明确失败而不是退回 headless 冒充实时。
- 任务完成发生在轮询间隔内时，桥必须通过新增 `turn/end` 事件判断，不能只看一次 `running=false`。
- 修复轮次必须复用原 session-id 和 cwd。
- 任何失败都不能把未完成的会话标为成功。

---

### Task 1: 桌面宿主客户端与发现

**Files:**
- Create: `scripts/dsh_desktop_bridge.py`
- Test: `tests/test_dsh_desktop_bridge.py`

**Interfaces:**
- Consumes: CDP `Network.getAllCookies`、DeepSeek host HTTP API。
- Produces:
  - `DesktopHostClient(port: int, cookie: str)`
  - `DesktopHostClient.call(endpoint: str, method: str, request: dict) -> dict`
  - `discover_desktop(devtools_port: int = 9226) -> DesktopConnection`

- [ ] **Step 1: 写客户端协议失败测试**

使用本地假 HTTP 服务，断言 `/api/session/list` 的 envelope、Cookie、方法名和错误处理。

Run: `python -m unittest tests.test_dsh_desktop_bridge.DesktopBridgeTests.test_client_uses_desktop_rpc_envelope -v`

Expected: FAIL，因为模块尚不存在。

- [ ] **Step 2: 实现最小 HTTP 客户端**

只接受本机端口、验证 `type=server-response`、`result.ok=true`，返回 `result.value`。

- [ ] **Step 3: 运行测试**

Run: `python -m unittest tests.test_dsh_desktop_bridge.DesktopBridgeTests.test_client_uses_desktop_rpc_envelope -v`

Expected: PASS。

### Task 2: 实时委派流程

**Files:**
- Modify: `scripts/dsh_desktop_bridge.py`
- Modify: `tests/test_dsh_desktop_bridge.py`

**Interfaces:**
- Consumes: `DesktopHostClient`。
- Produces: `delegate_desktop(client, root, item_id, task_file, cwd, label, session_id, timeout) -> DesktopDelegationResult`。

- [ ] **Step 1: 写成功流程失败测试**

假客户端按顺序返回 workspace、session、prompt、projection、page；断言 workspace 路径、prompt 文本、最终消息和证据文件。

Run: `python -m unittest tests.test_dsh_desktop_bridge.DesktopBridgeTests.test_delegate_creates_visible_session_and_collects_result -v`

Expected: FAIL。

- [ ] **Step 2: 实现 workspace/session/prompt 流程**

`workspace/create` → `workspace/rename` → `session/create` → `session/prompt`。

- [ ] **Step 3: 实现轮询和结果解析**

轮询 `session/projections` 与 `session/page`，只接受 prompt 后新增的 `turn/end`；提取最后一条 assistant text。

- [ ] **Step 4: 写超时、错误和 session 复用测试**

覆盖无 `turn/end`、prompt 拒绝、已有 session 复用。

- [ ] **Step 5: 运行桥测试**

Run: `python -m unittest tests.test_dsh_desktop_bridge -v`

Expected: PASS。

### Task 3: 启动器、CLI 和默认路由

**Files:**
- Modify: `scripts/dsh_desktop_bridge.py`
- Create: `tools/dsh/Start-DeepSeekLive.ps1`
- Modify: `AGENT_GUIDE.md`
- Modify: `README.md`
- Modify: `contexts/delegation.md`

**Interfaces:**
- Produces: `launch`、`doctor`、`delegate` CLI。

- [ ] **Step 1: 实现 launch/doctor/delegate**

launch 用 `DeepSeek Harness.exe --remote-debugging-port=9226` 启动 app；doctor 验证 CDP、宿主、cookie。

- [ ] **Step 2: 更新规范**

标准委派改为桌面实时桥；headless 只在用户明确同意时降级。

- [ ] **Step 3: 验证 CLI 帮助与失败信息**

Run: `python scripts/dsh_desktop_bridge.py doctor`

Expected: 当前 live app 检测通过。

### Task 4: 真实桌面端到端验证

**Files:**
- Create: `work/active/2026-10-19-desktop-live-bridge/artifacts/delegation/*`
- Create: `docs/verification/2026-10-19-desktop-live-verification.md`

- [ ] **Step 1: 创建真实可见会话**

在隔离事项 cwd 中提交只读验证任务。

- [ ] **Step 2: 用户窗口实时可见**

确认桌面 UI 侧栏出现对应 workspace/session，执行期间显示 running。

- [ ] **Step 3: Codex 收回并审查**

读取 `session/page` 事件，独立检查并记录结果。

- [ ] **Step 4: 全量验证**

Run: `python -m unittest discover -s tests -v`

Run: `python scripts/workspace.py validate`

Expected: 全绿、`OK`。

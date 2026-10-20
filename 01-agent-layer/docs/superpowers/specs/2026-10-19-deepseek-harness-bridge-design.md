# DeepSeek Harness 委派桥设计

## 1. 目标

Codex 保持主控与验收职责，把明确的实现任务交给本机的 DeepSeek Harness 桌面版执行，再回到 Codex 进行差异审查、测试、状态同步和提交。

## 2. 接入方式

使用 DeepSeek Harness 随桌面版附带的无窗口入口：

```text
D:\Apps\DeepSeek Harness\resources\runtime\cli\bin\dsh.cmd
```

通过 `--profile headless` 提交任务，使用 `--json` 获取会话、工具调用、状态和最终结果。该入口继承调用时的工作目录，并支持 `--session-id` 继续同一会话。

桌面版默认的 headless profile 禁用了本地凭据服务。项目提供一个显式 patch，仅对 Codex 发起的 headless 进程启用：

- `@deepseek-ai/dsh-credentials-local`：复用桌面版已保存的 DeepSeek 凭据；
- `approval.policy: never`：避免无交互执行因审批请求卡住。

安全边界由 `DSH_PERMISSION_MODE=workspace-write` 保持：允许写入指定工作目录，不允许任意扩大权限。桥不得使用 `danger-full-access`。

## 3. 角色

### Codex 主控

- 创建或恢复工作事项；
- 补齐需求、验收标准、范围和验证命令；
- 选择执行工作目录；
- 编写 DeepSeek 任务单；
- 调用桥并监控执行；
- 独立检查差异、运行测试、判断是否需要修复轮次；
- 更新 `STATUS.md`、`handoff.md`、`journal/`；
- 通过门禁后提交 Git。

### DeepSeek 执行者

- 读取任务单和指定工作目录；
- 完成代码、文档或其他实现；
- 运行任务要求的检查；
- 返回变更摘要、证据、阻塞和未完成项；
- 不提交 Git；
- 不修改 `STATUS.md`、`handoff.md`、`brief.md`、`AGENT_GUIDE.md` 或其他事项；
- 不顺带扩大范围，不在阻塞时伪造成功。

## 4. 流程

```text
用户 -> Codex 建项/补齐任务单
     -> dsh_bridge delegate
     -> DeepSeek headless 在隔离 cwd 实现
     -> 返回 JSONL 事件、最终答复、session-id
     -> Codex 检查 diff/文件
     -> Codex 独立运行测试
     -> 通过：同步状态并提交
     -> 不通过：向同一 session 下发修复任务
```

每轮委派保存：

```text
<item>/artifacts/delegation/<timestamp>-<label>-request.md
<item>/artifacts/delegation/<timestamp>-<label>-events.jsonl
<item>/artifacts/delegation/<timestamp>-<label>-result.md
<item>/artifacts/delegation/<timestamp>-<label>-meta.json
<item>/artifacts/delegation/INDEX.md
```

## 5. 命令接口

```text
python scripts/dsh_bridge.py doctor
python scripts/dsh_bridge.py delegate \
  --item <item-id> \
  --task-file <task.md> \
  --cwd <execution-workdir> \
  --label implement \
  --permission-mode workspace-write
```

修复轮次增加：

```text
--session-id <session-id>
```

## 6. 行为约束

- DeepSeek 的“完成”声明不是验收证据。
- Codex 必须实际读取变更并运行测试。
- 默认工作目录必须由 Codex 明确选择，桥不自动扫描其他事项。
- 子进程环境移除名称中包含 KEY/TOKEN/SECRET/PASSWORD/CREDENTIAL 的变量；凭据由本地 credentials 插件读取。
- 请求、事件和最终结果保存在事项内，不写入 DeepSeek 全局会话之外的其他位置。
- 超时、非零退出、缺少 final 事件、策略违规都视为失败。
- 如果 Git HEAD 在委派期间改变，记录策略违规，不自动回滚，交给 Codex/用户检查。
- 外部网络、发布、部署和删除仍遵循 `AGENT_GUIDE.md`。

## 7. 非目标

- 不通过桌面鼠标/键盘 UI 自动化提交任务。
- 不自动合并、推送或归档。
- 不让 DeepSeek 直接审批自己的结果。
- 不替代 Codex 对需求和验收标准的判断。

## 8. 验收

- `doctor` 能找到 dsh、credential patch 并报告可用。
- 单元测试使用假 dsh，验证成功、错误、超时、会话续接、权限模式和秘密环境过滤。
- 真实端到端任务能在隔离目录创建一个实现文件并运行测试。
- Codex 能读取同一 session 的最终结果和事件日志。
- 未通过 Codex 审查前，不产生由 DeepSeek 完成的 Git 提交。

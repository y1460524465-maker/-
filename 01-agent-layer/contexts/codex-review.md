# Codex Review Context

仅定义 Codex 主控对执行结果的独立审查流程，不用于 DeepSeek 执行者自检。仅在审查、核验、回归检查、风险评估或“确认是否完成”类任务中按需加载。

## 原则

- 默认只读；除非用户要求修复，否则不顺便改动。
- 不信任 STATUS 或 handoff 的“已完成”声明，要检查文件、差异和运行结果。
- 审查对象是用户需求和验收标准，不只是代码风格。
- 先判断影响，再决定严重级别。

## 审查流程

1. 读取 `brief.md`，列出验收标准和有效约束。
2. 读取 `STATUS.md`、`handoff.md` 和最近 journal，识别声明的结果与证据。
3. 检查 `git diff`、相关文件、历史提交和未提交改动。
4. 运行相关测试、构建、检查或可复现脚本，读取真实输出。
5. 针对高风险边界、失败路径、并发、权限、数据丢失和兼容性做定向检查。
6. 将发现按严重性记录：Critical / Important / Minor。
7. 对照行为不变量做一次回归检查，确认原有行为没有被新实现挤压。

## 不得省略

- 验证命令必须实际运行；无法运行时明确标记为未验证，不得猜测通过。
- DeepSeek 或其他执行 Agent 的最终答复不是证据；必须检查实际文件、Git diff 和测试输出。
- 检查执行者是否越界修改、是否擅自提交、是否遗漏验收标准。
- 文档任务也要检查术语、版本、引用和连续性。
- 发现测试本身有误时，先修正验证方式，再作结论。
- 对无法确定的问题说明假设和影响，不把推测写成事实。

## 输出

每条发现至少包含：

- 严重性；
- 位置；
- 实际行为与预期行为；
- 复现或证据；
- 建议修复方向。

## 审查证据目录

每轮审查必须写入独立目录，不覆盖上一轮：

```text
02-work-items/{active,archived}/<item-id>/reviews/<task-id>/round-<n>/
  review.md
  diff.patch
  test-output.txt
```

- `review.md` 使用 `01-agent-layer/templates/review/review.md`，记录范围、命令、发现和结论。
- `diff.patch` 保存本轮实际检查的变更。
- `test-output.txt` 保存 Codex 独立运行测试的原始输出。
- DeepSeek 的请求、事件和最终答复继续保存在 `artifacts/delegation/`。

`STATUS.md` 只记录审查结论和目录入口，不复制完整报告。

纯审查任务结束时更新 `STATUS.md` 的“最近验证”和 `handoff.md` 的下一步。若用户要求同时修复，则进入 `coding`，修复后创建新的 review round，最后用 `sync` 收尾。

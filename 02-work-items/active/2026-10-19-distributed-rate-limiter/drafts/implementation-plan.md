# 分布式限流器实施计划

> 事项：2026-10-19-distributed-rate-limiter
> 日期：2026-10-19；前序：用户确认的会话计划、../brief.md；状态：approved
> 执行方式：本机 DeepSeek Harness；主控只规划、审查、验证、文档与提交。

## 目标与架构

Go 独立模块；统一 Limiter + Store.Consume，内存锁保护与 Redis Lua。Redis TIME 与请求 ID 去重；net/http 适配。
规范基线：../brief.md。依赖：T1 → T2/T3/T4 → T5 → T6。桥接使用 scripts/dsh_bridge.py。每次只写任务所属文件，主控冻结公共契约。

## 任务与验收

- [ ] T1：API、规则/错误/请求、存储接口、超时与 ID、fake 测试与环境；非法输入不调用存储；可编译，测试通过。
- [ ] T2（T1 后）：内存三算法，fake clock，拒绝不扣配额，端点/清理/并发；核心函数语句 100% 且行为分支矩阵齐全，race 通过。
- [ ] T3（T1 后）：Redis Lua 三算法，TIME、回拨、TTL、cluster hash slot、安全有界重试；miniredis+mock 证明多实例和响应丢失不重扣。
- [ ] T4（T1 后）：HTTP 适配与示例，允许一次下游，429/503/400 与 context 测试。
- [ ] T5（T2/T3/T4 通过后）：测试文件补强，一致性、并发 cost、重试与时间；test/race/coverage/vet；缺陷返还实现负责人。
- [ ] T6（主控）：README、最终汇总、状态、交接和本地提交；不编写实现或测试代码。

## 关注点

1. 计费已执行但响应丢失：T3 故障测试必须证明去重；关闭隐藏重试。
2. 时间回拨/窗口端点/TTL 清理：T2/T3 通过 fake 时间和 mock/miniredis 复现。
3. 加权 cost 与并发：T2/T3/T5 断言成功累计 cost，不只断言无崩溃。
4. 数值范围与 Lua 精度：T1 定界，T2/T3 验证边界；不允许溢出后放行。
5. 相同业务 key 不同规则与 namespace：T1/T5 验证隔离与同配置共享。

## 审查与返工

每任务主控独立读文件/diff、运行测试，审查接口契约、并发、边界、错误、测试有效性。
记录：严重性、文件:行、函数、实际/预期、证据、修复要求。初审+最多两轮返工，同一 session。
失败任务记录阻塞；继续无依赖任务。初始 Git HEAD：36c2d74。

# T5 — 一致性与测试有效性补强

> 事项：2026-10-19-distributed-rate-limiter；前序：../brief.md、implementation-plan.md、CONTRACT.md；状态：prepared
> cwd：本事项 workspaces/implementation；角色：测试实现者，主控独立验收。

## 功能目标

独立检查测试是否真正证明需求，新增跨后端契约/时间/加权/并发/故障测试。
允许新增 parity_test.go、integration_test.go 及其他 *_test.go；不得修改生产代码。

## 输入输出契约

消费已有 Limiter/MemoryStore/RedisStore API，使用 miniredis/mock 和 fake clock。
输出测试与 TESTING.md（证据和边界），如发现实现 bug 以 file:line/function + reproducer 回报，交主控打回原负责人。

## 边界条件

三算法×双后端；窗口开闭端点；回拨/前跳；同时间多次请求；cost/容量边界；规则隔离；
并发成功累计 cost；响应丢失重试；请求取消；输入与损坏状态；TTL 清理。

## 验收标准

受控时间线比较决定序列；有效断言非只不崩溃；核心函数 100% 语句覆盖与分支清单；
运行 go test ./...、go test -race ./...、go test -coverprofile=coverage.out ./...、go tool cover -func=coverage.out、go vet ./...。
明确 miniredis 与真实 Redis 差异、未验证项；不得使用松散断言消除失败。
新增缺陷回归测试应先证明 RED，待原负责人修复再 GREEN。

## 禁止事项

不直接修生产代码，不删/弱化失败测试，不改治理/契约/其他事项，不提交/暂存/推送，不连生产 Redis。

## 回报

文件、测试断言与需求映射、真实命令/结果、发现含行号、未验证风险。

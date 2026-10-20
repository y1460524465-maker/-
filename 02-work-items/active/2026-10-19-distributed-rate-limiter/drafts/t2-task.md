# T2 — 内存存储与三种限流算法

> 事项：2026-10-19-distributed-rate-limiter；前序：../brief.md、implementation-plan.md、T1 CONTRACT.md；状态：prepared
> cwd：本事项 workspaces/implementation；角色：实现者，Codex 独立审查和唯一提交。

## 功能目标

实现 Store 的内存后端，三算法、并发与可控时钟。先阅读 CONTRACT.md 和实际公共 API，不得自行改契约。
只实现本任务，不实现 Redis/HTTP。

## 输入输出契约

消费已冻结 Store.Consume 与 Request、Rule、Clock。输出 NewMemoryStore(opts ...MemoryOption) *MemoryStore、WithClock(Clock) MemoryOption、MemoryStore.Consume。
允许 memory.go、memory_test.go 及 memory_*.go；可追加 CONTRACT.md 中 Memory 使用段落，不改原公共契约。
内存采用互斥锁/分片锁保证一次 Consume 线性化。无后台 goroutine 的惰性清理优先，可提供可测试清理入口；不要无限制每调用全表扫描。
令牌桶初始 Burst，按 QPS/秒连续补充封顶；拒绝不扣，时间钳制不倒退。
滑动窗口精确 cost 日志：在 (now-1s,now] 累计接受 cost，恰好 1 秒前到期；cost 加权；同时间请求不能覆盖。
固定窗口：有效时间整秒对齐；初始计数 0，窗口到端点重置。
状态 key 已含规则，直接使用 Request.Key；所有直接 Consume 输入也做防御校验，不能 panic/溢出。
尊重 ctx；错误不返回 true；返回 err 与 sentinel 保持一致。

## 边界条件

同 key 并发；不同 key；规范化规则；clock 回拨与大跳；令牌小数与封顶；大 cost 不扣；恰好阈值/端点；内存清理前后等价；nil clock/options、过大规则。
清理保留期必须覆盖恢复成初始状态的时间，时钟回拨时不能过早丢状态；状态访问与清理线程安全。

## 验收标准

先失败测试再实现。fake clock，不用 Sleep 验证时间。
三算法允许/拒绝/恢复/加权/超量/回拨/端点/长空闲、拒绝不扣、清理均测试。
并发测试断言成功累计 cost <= 配额。核心决策函数/状态变更函数 go cover 100% 语句，并附行为分支清单，不能靠注释声称全覆盖。
运行 TOOLCHAIN.md 指定 go test ./...、go test -race ./...、go vet ./...、go test -coverprofile=coverage.out ./...、go tool cover -func=coverage.out。

## 禁止事项

仅 cwd 上述文件；不改公共契约、go.mod、Redis/HTTP 文件、治理/其他事项。不提交/暂存/推送，不读凭据不改全局。
不隐藏测试失败，不为覆盖率删除有效分支。发现契约障碍回报主控。

## 回报

文件、命令实际结果、RED→GREEN、核心覆盖率与分支矩阵、风险/阻塞。

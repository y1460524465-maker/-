# T3 — Redis 原子限流与安全重试

> 事项：2026-10-19-distributed-rate-limiter；前序：../brief.md、implementation-plan.md、CONTRACT.md；状态：prepared
> cwd：本事项 workspaces/implementation；角色：实现者，主控独立审查并唯一提交。

## 功能目标

实现三算法 Redis Store 与 Lua、miniredis 与故障 mock。先读实际冻结契约。
允许 redis.go、redis_*.go、redis*_test.go、scripts/*.lua、go.mod/go.sum。不修改内存/public API。

## 输入输出契约

消费 Store.Consume(ctx,Request)，Request.ID 由 Limiter 单次逻辑调用创建。
产出 Redis Store 的公开构造/选项，使用 go-redis/v9。客户端接口需可 mock；不要要求构造在真实服务执行命令。
Redis TIME 做计费时间，毫秒/微秒精度要与数值安全边界一致；回拨有效时间=max(now,last)。
三种算法完全在 Lua 中验证+决定+更新；拒绝不扣；精确滑动 cost 日志需要唯一成员避免同时间覆盖。
相同 namespace/algorithm/rule/key 相同 state；状态+日志+去重 key 同 hash slot。
Lua 在写前校验所有输入和已有类型/字段，Redis 脚本错误无自动事务回滚。
客户端隐藏重试必须关掉，不能接受任意开启隐藏重试的 caller client 且不检测/约束。
脚本缓存 EVALSHA，NOSCRIPT 有界回退 EVAL；安全重放只限同 Request.ID 且有效时间窗内。
去重记录包含 allow/deny；首次执行后响应丢失，重试返回同决定不重扣；去重 TTL > 整个逻辑调用最大重试期限含余量；过期/不确定不能放行。
重试最大次数、backoff、总 timeout 有默认值/校验；context cancel 立即结束；错误 false,error。
不依赖 Go 本地墙钟计费；可以 monotonic elapsed 控制重试期限。
TTL 不可造成未恢复满桶/未过有效窗口而重置；回拨保留状态的安全性必须测试。
记得 RULE MaxQPS/MaxBurst 1e6，Lua double 2^53 精度，Unix 微秒与分数运算不要溢出/失真放行。

## 边界条件

NOSCRIPT、网络失败前/执行后、context、错误类型、损坏状态、无 final response、重试耗尽、回拨/前跳、TTL、同时间滑动请求、并发多个实例、规则隔离、超量 cost。
miniredis 的 TIME/Lua 支持以实际能力为准，不支持的精确故障用接口 mock 覆盖，并明确限制。

## 验收标准

先 RED 再 GREEN。miniredis 三算法功能/窗口/加权/共享状态/并发/TTL。
接口 mock 测试 NOSCRIPT、cancel、超时、执行后丢响应不重扣、限次/限时、错误传播。
真实执行 go test ./...、go test -race ./...、go vet ./...。报告新增依赖版本和命令。
模拟时钟回拨必须真实验证脚本有效时间钳制，不仅断言脚本文本包含 max。
将 Redis 构造/重试默认值追加 CONTRACT.md，不更改 T1 契约。

## 禁止事项

不连接生产 Redis、不访问凭据、不全局安装、不提交/暂存/推送、不改治理或其他事项。
不悄悄放弃去重/时钟保证，不把 mock 说成真实集群验证；不改其他实现消除测试失败。

## 回报

文件列表；构造 API；重试/去重保证及期限；真实测试结果；RED→GREEN；限制/风险/阻塞。

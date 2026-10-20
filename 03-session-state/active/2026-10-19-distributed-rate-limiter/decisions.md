# 决策

- 2026-10-19：使用本机 Harness，按项目桥接流程；用户已指定。
- Go + go-redis/v9 + miniredis/mock；net/http。
- 窗口 1 秒；Burst 省略默认 QPS，否则必须相等；令牌桶 Burst 独立。
- 冻结规则上限 1e6 以约束 Lua 精度；不提供无限数值范围。
- 为避免同时改 go.mod 和共享契约，T2/T3/T4 可串行委派；用户允许并行但未要求。
- 不创建额外 Git worktree：事项 implementation 目录是规范提供的物理隔离目录，独立 Go 模块无现有业务代码。

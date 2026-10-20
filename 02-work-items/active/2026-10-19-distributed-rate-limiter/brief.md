# Brief — 分布式限流器中间件

## 用户原始要求

实现分布式限流器中间件：三种算法（令牌桶、滑动窗口、固定窗口）；存储接口及内存、Redis 两种实现；Redis Lua 原子性；统一 Allow(key string, cost int) (bool, error)；QPS 与突发容量配置；并发安全、时钟漂移、脚本重试；内存核心路径全覆盖，Redis 使用 miniredis 或 mock；README 说明架构、算法取舍、已知限制。

主控只规划、委派、审查、写文档，不直接编写实现代码或测试代码。先计划待确认，再按依赖下发；每任务包含功能目标、输入输出契约、边界条件、验收、禁止事项。逐项审查接口、并发、边界、错误、测试；意见具体到文件/函数/行；最多两轮返工，仍失败记录阻塞并继续独立任务。最终汇总含任务对照表、各任务审查与打回次数、架构决策、风险、后续改进。
2026-10-19 用户确认开始，并指定使用本项目 DeepSeek Harness 委派流程。

## 目标

交付独立 Go 模块和 net/http 中间件，主控通过 dsh_bridge 调度本机 DeepSeek Harness，独立验收。

## 验收标准

- [ ] T1 公共契约/参数/错误/超时测试与工具链证据。
- [ ] T2 三种内存算法、fake clock、核心函数 100% 语句覆盖及分支矩阵、并发与清理。
- [ ] T3 三种 Redis Lua 算法、服务端 TIME、回拨钳制、有界安全重试、TTL/去重/Cluster key slot 测试。
- [ ] T4 HTTP 允许调用下游一次，拒绝 429、存储错误 503、参数提取错误 400，取消传播。
- [ ] T5 一致性/故障/并发测试；go test、race、coverage、vet，记录未验证能力。
- [ ] T6 README 与最终汇总文档，对照需求记录已通过/阻塞/未验证，更新状态并本地提交。

## 范围

本事项目录内文档和 workspaces/implementation/ 的独立 Go 模块。go-redis/v9；miniredis/mock。
规则：整数 QPS>0，令牌桶 Burst>0 初始满桶；窗口为 1 秒，Burst=0 默认 QPS，否则必须等于 QPS。
Allow 和 AllowContext：拒绝 false,nil；参数错误 false,error；cost 超容量 false,nil；错误不放行；拒绝不扣配额。规则不可变；规则和算法参与状态 key 隔离。
Redis 用服务端 TIME；有效时间不倒退；单次逻辑调用 ID 去重覆盖内部重试期限；不确定网络结果不可盲重放；NOSCRIPT 有界回退；禁止客户端隐藏重试；Lua 先校验后写。
内存注入时钟，并发安全，空闲清理不提前重置配额。
HTTP 使用 net/http，支持 key/cost 提取和请求 context。

## 非目标

部署、生产 Redis 访问、真实集群搭建、性能承诺、跨调用业务幂等、修改其他事项。

## 约束

- 遵循 `01-agent-layer/AGENT_GUIDE.md` 与 `01-agent-layer/core/invariants.md`。只由主控更新治理文件和提交。
- 所有实现/测试代码由本机 Harness 产生；主控只读审查并运行验收。
- 每任务最多两轮修复，同一 session；阻塞依赖显式记录。
- 网络仅用于公开 Go 工具链/依赖；不读取或输出凭据，不推送/部署。
- 主控新建事项时按规范更新 `02-work-items/WORK_INDEX.md`，除此之外只写本事项目录。

## 开放问题

- 当前 PATH 未发现 Go；T1 核查并可在 implementation/.tools 内安装公开官方便携 Go，禁止全局安装。无法取得则报告阻塞。

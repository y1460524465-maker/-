# Brief — Go 带过期时间的并发内存缓存

> 本文件保存需求和验收基线。用户原始表述尽量逐字保留，不要用 Agent 的转述覆盖它。

## 用户原始要求

用户要求：用 Go 实现带过期时间的内存 Cache，接口为 Set(key string, val any, ttl time.Duration)、Get(key string) (any, bool)、Delete(key string)，并发安全，读取时过期不可见，提供 Cleanup() 清理过期条目，附带单元测试。

流程要求：主控不写实现代码；拆成 2–3 项并逐个下发；每项包含功能目标、接口契约、边界与验收；返回后审查并发、过期、边界、测试有效性，意见到函数/行号；每项最多打回两轮；最终输出完成对照表、审查结论/打回次数/遗留问题、关键决策、已知限制。

用户已收到三项拆解，随后指示“阅读我们的agent_guide.md进行下发”。按批准继续执行，通过本机 DeepSeek Harness 桥委派。

## 目标

在 workspaces/implementation/ 交付独立 Go 模块、Cache 实现、测试与使用说明，主控独立验收并留存可复现证据。

## 验收标准

- [x] 零值 Cache 可用；接口为 (*Cache).Set/Get/Delete/Cleanup；仅用 Go 标准库，Go >=1.18。
- [x] ttl>0 从写入开始计时；now>=expiresAt 即过期；ttl<=0 立即失效并使旧值失效。
- [x] key 不存在返回 (nil,false)，Delete 缺失 key 幂等；空 key 和 nil 值合法，nil 命中返回 (nil,true)。
- [x] 重复 Set 替换值和 TTL；四个方法并发安全，清理不能误删并发更新的新值。
- [x] Cleanup 同步执行一轮，可由后台 goroutine 调用；只移除到期条目。
- [x] 单元测试明确断言以上行为，包含临界时刻、物理清除、更新保留与并发交错。
- [x] 主控独立运行 go test ./...、go test -race ./... 并读取结果；不能运行则记录阻塞，不假称通过。
- [x] 最终汇总、逐项行级审查、委派请求/事件/session/result/meta 均落盘。

## 范围

三项串行：1 核心 Cache 与相关基础测试；2 Cleanup 与相关测试；3 完整边界/并发测试、测试有效性证据与 README。前两项带最小测试以支持独立验收，第三项补全测试。

## 非目标

不实现自动清理定时器、容量淘汰、持久化或分布式缓存；不替调用方保护存入对象的内部并发访问；不发布或推送。

## 约束

- 遵循 `01-agent-layer/AGENT_GUIDE.md` 与 `01-agent-layer/core/invariants.md`。
- 默认只写入本事项目录。
- 主控只写治理文档与任务单，不编写或修改实现/测试代码；任何代码问题退回执行者。
- DeepSeek 不提交 Git、不修改治理文件、不接触其他事项；每项最多两轮代码打回。
- `02-work-items/WORK_INDEX.md` 仅登记本事项，是全局索引写入例外，保留已有其他事项行和改动。

## 开放问题

- 无。

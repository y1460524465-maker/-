# Go TTL Cache Implementation Plan

> 事项：2026-10-19-go-ttl-cache；日期：2026-10-19；前序文件：brief.md、聊天中已确认拆解；状态：已执行并验收。
> 执行方式：依 AGENT_GUIDE 第13节及 delegation 上下文，通过 scripts/dsh_bridge.py 串行委派 DeepSeek；主控独立审查，主控不写实现/测试代码。

**Goal:** 交付并发安全、过期不可见的 Go 内存 Cache 与有效单元测试。
**Architecture:** Cache 自有同步原语和条目表；读取判断到期，Cleanup 执行一轮物理删除。零值可用；不增加自动 goroutine。
**Tech Stack:** Go >=1.18、标准库 testing/sync/time；独立模块 example.com/ttlcache。
**Spec:** ../brief.md

## Global Constraints

- Set(key string,val any,ttl time.Duration)、Get(key string)(any,bool)、Delete(key string)、Cleanup()；接收者 *Cache。
- ttl<=0 立即失效；now>=expiresAt 即过期；空 key 和 nil 值合法。
- 四方法并发安全，不误删新写入值；不复制使用过的 Cache。
- 主控不写实现/测试代码；执行者仅修改任务授权文件且禁止提交；每项最多两轮打回。

## Review Focus

- 旧条目过期后 Get/Cleanup 与同 key 更新交错，不能误删新值（任务2/3）。
- ttl<=0 覆盖有效旧值后不能仍命中（任务1/3）。
- nil 命中必须 true、缺失必须 false（任务1/3）。
- 到期等号与覆盖重置 TTL 必须有可控时刻断言（任务3）。
- 并发测试必须有同步、完成等待和结果断言，单凭无 panic 不算充分（任务3）。

## Task 1 — Cache 核心

Files: go.mod、cache.go、cache_test.go（均在 workspaces/implementation/）。
Produces: 零值可用 Cache 及 Set/Get/Delete。锁内判断和操作保证一致性。可预留包私有时间辅助方法支持确定性测试，不能增加公共配置接口。

- [x] 执行者先编写基础测试，记录缺失实现导致的失败。
- [x] 执行者实现接口、覆盖/过期/缺失/nil/空 key 行为并 gofmt。
- [x] 执行者运行 go test ./...；主控读取逐行代码并独立运行；记录审查。

## Task 2 — Cleanup

Files: cache.go 或 cleanup.go、cleanup_test.go。
Consumes: Task1 Cache 和同步策略。Produces: (*Cache).Cleanup()，同步清除一轮到期条目，可被后台调用。

- [x] 先写空/全过期/混合/重复清理与有效更新保留测试，运行缺失方法的失败。
- [x] 实现 Cleanup；不得以未受保护的旧快照删除当前新值。
- [x] 执行 go test ./...；主控复审全部共享状态路径并独立验证。

## Task 3 — 完整测试与证据

Files: *_test.go、README.md；实现文件只有主控明确打回授权才可改。
Consumes: Cache 四方法。Produces: 可复现功能/过期/清理/并发测试及说明。

- [x] 补充零值、缺失、非正TTL、nil/空key、覆盖TTL、到期临界点、物理删除、更新保留测试；优先可控时间而非微小 sleep。
- [x] 并发覆盖 Set/Get/Delete/Cleanup，使用屏障和 WaitGroup，断言可确定的前后置条件。
- [x] 在本事项独立实验目录复制代码，分别注入漏判过期、错误非正TTL、错误清理等缺陷，运行对应测试确认失败；不得破坏交付目录。
- [x] 运行 go test ./...、go test -race ./...、go test -count=20 ./...；主控独立重复验收并检查断言有效性。
- [x] 主控更新逐项审查、最终汇总、STATUS/handoff/journal，结构校验并仅提交本事项及索引中本事项新增行。

## Self-review

需求4条均被3项覆盖；接口一致；测试和实现由执行者编写；任务顺序与最多两轮打回保留。前两项附最小测试是为逐项验收，第三项仍负责完整测试交付。

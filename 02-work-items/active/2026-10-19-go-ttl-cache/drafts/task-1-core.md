# DeepSeek Implementation Task — 1 核心 Cache

事项：2026-10-19-go-ttl-cache；前序：brief.md、implementation-plan.md；状态：待执行。
工作目录：E:\多agent协作\work\active\2026-10-19-go-ttl-cache\workspaces\implementation
角色：你是实现执行者，Codex 是主控、审查者和唯一提交者。

## 必读

- E:\多agent协作\AGENT_GUIDE.md 与 core\invariants.md。
- 本事项 brief.md、drafts\implementation-plan.md、本任务单。

## 功能目标与接口契约

只实现任务1：新建独立 Go 模块 example.com/ttlcache（Go >=1.18），package cache，零值 Cache 可直接使用。
实现 (*Cache).Set(key string,val any,ttl time.Duration)、Get(key string)(any,bool)、Delete(key string)。Cleanup 留到任务2，不要提前实现。
Set 覆盖值与过期时间；ttl>0 自写入计时，当前时刻达到或超过 expiresAt 即无效；ttl<=0 立即失效并使该 key 的旧值不可见。
Get 缺失/过期返回(nil,false)，有效 nil 返回(nil,true)。Delete 缺失 key 无副作用、可重复调用。
用标准库同步原语保护全部 map 及辅助状态。Get 遇过期可以只隐藏不物理删除，避免读后删除新值竞态。
允许包私有的时间判定辅助方法供同包确定性测试；保持公共API简洁，不引入全局可变时钟或自动goroutine。

## 边界条件

- key 不存在：Get(nil,false)，Delete 安全；空字符串 key 合法。
- ttl<=0：包括0和负数，覆盖旧有效值后立即未命中。
- 并发读写：Set/Get/Delete 可并发，锁不得复制、读锁内不得写map；调用方对象内部不在保护范围。
- 零值 Cache 的 map 初始化必须并发安全；nil val 不等于缺失。

## 允许修改

仅 cwd 内 go.mod、cache.go、cache_test.go。可以读取已有 README.md，但此任务不要改它。
不得改 STATUS.md、handoff.md、brief.md、decisions.md、全局规范、其他事项；不得提交/推送/合并Git、删用户数据、外发、读打印凭据。
不得安装系统级依赖或扩大修改范围。go 不存在时先报告事实，不要伪造运行成功。

## 验收标准与验证

先写基础测试并运行确认缺少实现导致失败，再完成代码。
测试必须断言零值、未命中、正常命中、nil、空key、覆盖、0/负TTL覆盖旧值、到期不可见和基础并发路径。
执行 gofmt -w cache.go cache_test.go，go test ./...。若工具链不在PATH，可查找本事项 workspaces/toolchain/go/bin/go.exe；存在则仅当前进程加入 PATH。
返回前逐行自查锁路径及到期等号。主控随后独立验收，不能把你的声明当最终通过。

## 输出约定

只回报：修改文件及关键函数/行号；运行命令和真实结果（含首次失败）；标准满足情况；剩余问题/阻塞。不要执行任务2/3。

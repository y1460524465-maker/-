# DeepSeek Implementation Task — 3 完整测试与证据

事项：2026-10-19-go-ttl-cache；前序：brief.md、implementation-plan.md、任务1/2审查；状态：待任务2通过后下发。
cwd：E:\多agent协作\work\active\2026-10-19-go-ttl-cache\workspaces\implementation
角色：测试实现执行者；Codex 为审查者与唯一提交者。

## 必读

E:\多agent协作\AGENT_GUIDE.md、core\invariants.md、本事项 brief.md、drafts\implementation-plan.md、所有交付Go文件、本任务单。

## 功能目标、接口契约

补全 package cache 的零值 Cache、Set(key string,val any,ttl time.Duration)、Get(key string)(any,bool)、Delete(key string)、Cleanup() 单元测试和 README。
ttl>0 从写入开始计时，now>=expiresAt 过期；ttl<=0 立即失效并覆盖旧值；Get 缺失/过期(nil,false)，有效nil(nil,true)；空key合法；Delete缺失幂等；Cleanup同步执行一轮。

## 边界条件和测试要求

- 分别覆盖0与负TTL、旧值覆盖失效、nil/空key、缺失key、零值。
- 覆盖Set重设TTL、临界点之前/等于/之后，优先利用已有包私有时间辅助方法或测试内受锁保护设置到期值；不能只用微小sleep碰运气。
- Cleanup测试检查物理移除、有效项保留、重复调用、更新后新值保留。
- 并发测试同时覆盖四方法及同key竞争，屏障开始、WaitGroup等待；明确断言阶段性前后置条件，不能只有无panic。不要在goroutine里Fatal后跳过必要信号导致挂死。
- 测试必须能测出问题：在本事项独立 workspaces/mutation-checks/ 复制交付代码，分别注入漏判过期、ttl<=0残留旧值、错误清理有效项三类缺陷，运行对应测试，记录期望失败/实际失败。不得在交付目录注入缺陷。

## 允许修改和禁止动作

仅 cwd 的 *_test.go 与 README.md，允许在本事项 workspaces/mutation-checks/ 创建独立实验副本。cache.go/cleanup.go/go.mod 只读；发现实现bug向主控报告，由主控明确打回后才可修改。
禁止改治理文档/规范/其他事项；禁止提交/推送/合并Git、删除用户数据、外发、读取打印凭据、系统级安装。

## 验收标准与命令

使用 ..\toolchain\go\bin\go.exe 或PATH中的go；CGO_ENABLED=1，使用 ..\toolchain\llvm-mingw-20261006-ucrt-x86_64\bin\clang.exe，配置当前进程PATH和CC=clang；不支持race则如实报告，不能替换为非race后宣称race通过。
执行 gofmt -w 实际修改测试；go test ./...；go test -race ./...；go test -count=20 ./...。
修正前期审查观察：cache_test.go 原114–125先写200ms TTL再断言有效，可能因调度暂停偶发失败；改为确定性的内部expiresAt设置和断言，缩短/移除不必要sleep。cleanup_test.go 原93–97 captured now后调用Cleanup并非精确等号测试，等号由TestIsExpiredBoundary验证；修正容易误读注释。
README说明接口、非正TTL、零值、调用方对象并发责任、Cleanup后台调用方式与无自动清理、测试命令。
返回文件/测试函数行号、真实命令输出、缺陷注入明细及失败证据、标准满足情况、剩余问题。主控将独立运行验收。

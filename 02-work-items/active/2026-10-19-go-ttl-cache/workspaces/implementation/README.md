# cache — 带过期时间的并发内存缓存

`example.com/ttlcache` 是一个只依赖 Go 标准库的并发安全内存缓存。条目在写入时带上
TTL，读取时过期条目不可见；`Cleanup` 同步清理一轮已过期条目。

## 接口

```go
type Cache struct{ /* 未导出字段 */ }

func (c *Cache) Set(key string, val any, ttl time.Duration)
func (c *Cache) Get(key string) (any, bool)
func (c *Cache) Delete(key string)
func (c *Cache) Cleanup()
```

### 零值

`Cache` 的零值可直接使用，不需要构造函数：

```go
var c cache.Cache
c.Set("answer", 42, time.Minute)
v, ok := c.Get("answer") // 42, true
```

`Cache` 首次使用后不可复制；请通过 `*Cache` 共享同一个实例，而不是按值传递。

### Set

- `ttl > 0`：从本次 `Set` 调用开始计时，到期时刻为 `time.Now().Add(ttl)`。
- `ttl <= 0`：条目立即失效，并删除同 key 的旧值；不会留下一个“已过期但仍在表里”的旧条目。
- 同一个 key 重复 `Set` 会同时替换值和 TTL。
- 空字符串是合法 key；`nil` 是合法值。

### Get

- key 不存在或已过期：返回 `(nil, false)`。
- key 存在且值就是 `nil`：返回 `(nil, true)`，用第二个返回值区分“nil 值”与“未命中”。
- 过期判定为 `now >= expiresAt`，即到达到期时刻的瞬间就视为过期。
- `Get` 只隐藏过期条目，不负责物理删除；物理删除由 `Cleanup` 完成。

### Delete

删除指定 key。删除不存在的 key 是幂等的空操作，不会影响其他条目。

### Cleanup

同步执行一轮清理：遍历当前条目，只删除调用时刻已经过期的条目，有效条目保持原值、
原到期时间不变。可以重复调用，也可以从后台 goroutine 调用。`Cleanup` 自己不会启动
goroutine 或定时器，缓存也不会自动清理；需要周期性清理时，由调用方自行调度，例如：

```go
ctx, cancel := context.WithCancel(context.Background())
defer cancel()

go func() {
	ticker := time.NewTicker(time.Minute)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			c.Cleanup()
		}
	}
}()
```

`Cleanup` 在整轮清理期间持有写锁，因此不会与并发的 `Set`/`Get`/`Delete` 交错，
也不会用旧快照误删并发写入的新值。

## 并发责任

- `Set`、`Get`、`Delete`、`Cleanup` 对同一个 `*Cache` 的并发调用是安全的。
- 缓存只保护自己的条目表和过期时间，不保护存入对象的内部状态。若 `val` 是
  map、slice、指针或其他可变对象，并被多个 goroutine 同时访问，调用方需要自行同步。
- 不要复制已经使用过的 `Cache`；复制会复制锁和 map，导致两个实例行为不一致。

## 测试

测试覆盖零值、缺失 key、空 key、nil 值、0/负 TTL、旧值覆盖、TTL 重设、到期临界点、
物理清理、有效项保留、重复清理、并发更新保留，以及四方法在同 key 上的并发竞争。
到期时刻使用测试内受锁保护的内部 `expiresAt` 注入，临界等号由 `isExpired` 直接断言，
不依赖微小 sleep。

在 `workspaces/implementation` 目录执行。此前用于验收的本地 Go/LLVM-MinGW 工具链已按用户要求删除；若要重新运行，需先取得用户同意并恢复可用的 Go 环境。

```powershell
go test ./...
go test -race ./...
go test -count=20 ./...
```

`go test -race` 需要 CGO 和 64 位 C 编译器。历史验收结果仍保存在 `artifacts/final-verification.txt`。

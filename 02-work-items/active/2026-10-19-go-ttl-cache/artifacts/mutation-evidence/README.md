# .mutation-checks — 测试有效性实验

本目录是 `2026-10-19-go-ttl-cache` 任务3的独立缺陷注入实验，用于证明主目录测试能够
检出违反接口契约的实现。它不是交付包的一部分：

- 目录名以 `.` 开头，Go 的 `./...` 匹配会跳过它；
- 每个子目录都有自己的 `go.mod`，是独立模块；
- 主目录 `go list ./...` 只输出 `example.com/ttlcache`（见 `evidence/07-root-go-list.txt`）。

实验只修改副本，不修改主目录的 `cache.go`、`cleanup.go`、`go.mod`、测试或 README。

## 目录

```text
.mutation-checks/
├─ delivery/                          # 未变异基线：全部 Go 文件与主目录一致
├─ defect-1-missed-expiry/            # isExpired 恒为 false
├─ defect-2-nonpositive-keeps-old/    # ttl<=0 不再删除旧值
├─ defect-3-cleanup-deletes-valid/    # Cleanup 删除所有条目
└─ evidence/
   ├─ 01-baseline.txt
   ├─ 02-defect-1-missed-expiry.txt
   ├─ 03-defect-2-nonpositive-keeps-old.txt
   ├─ 04-defect-3-cleanup-deletes-valid.txt
   ├─ 05-compile-check.txt
   ├─ 06-root-go-test.txt
   ├─ 07-root-go-list.txt
   ├─ 08-hashes.txt
   ├─ 09-root-go-test-race.txt
   └─ SUMMARY.txt
```

每个 `delivery/`、`defect-*/` 都包含：

```text
cache.go  cleanup.go  cache_test.go  cleanup_test.go  go.mod
```

## 缺陷定义

1. **漏判过期**（`defect-1-missed-expiry/cache.go`）
   - 变异：`isExpired` 直接 `return false`。
   - 预期失败：`TestIsExpiredBoundary`、`TestExpiryHidesValue`、
     `TestCleanupRemovesOnlyExpiredEntries`、`TestCleanupAllExpired`、
     `TestCleanupKeepsConcurrentlyUpdatedValue`。

2. **非正 TTL 残留旧值**（`defect-2-nonpositive-keeps-old/cache.go`）
   - 变异：`Set` 的 `ttl <= 0` 分支只 `return`，不再 `delete(c.items, key)`。
   - 预期失败：`TestNonPositiveTTLExpiresImmediately`、
     `TestCleanupDoesNotResurrectNonPositiveTTLEntries`。

3. **Cleanup 删除有效项**（`defect-3-cleanup-deletes-valid/cleanup.go`）
   - 变异：清理条件改为 `c.isExpired(e, now) || !c.isExpired(e, now)`，恒为 true。
   - 预期失败：`TestCleanupRemovesOnlyExpiredEntries`、
     `TestCleanupKeepsAllValidEntriesAndIsIdempotent`、
     `TestCleanupConcurrentWithSetGetDelete`。

## 重跑命令

以下命令从主目录 `workspaces/implementation` 开始，使用任务指定的本地 Go/clang：

```powershell
$env:PATH = '..\toolchain\go\bin;..\toolchain\llvm-mingw-20261006-ucrt-x86_64\bin;' + $env:PATH
$env:CC = 'clang'
$env:CGO_ENABLED = '1'

# 沙箱中默认 GOCACHE 可能不可写；使用可写临时目录
$env:GOCACHE = Join-Path $env:TEMP 'ttl-cache-mutation-gocache'
$env:GOTMPDIR = Join-Path $env:TEMP 'ttl-cache-mutation-gotmp'
New-Item -ItemType Directory -Force -Path $env:GOCACHE, $env:GOTMPDIR | Out-Null
```

### 1. 基线

```powershell
Push-Location .mutation-checks\delivery
go test -count=1 ./...
$code = $LASTEXITCODE
Pop-Location
# 预期 exit 0，输出 ok example.com/ttlcache
```

### 2. 三类缺陷

```powershell
Push-Location .mutation-checks\defect-1-missed-expiry
go test -run 'TestIsExpiredBoundary|TestExpiryHidesValue|TestCleanupRemovesOnlyExpiredEntries|TestCleanupAllExpired|TestCleanupKeepsConcurrentlyUpdatedValue' -count=1 ./...
$code = $LASTEXITCODE
Pop-Location
# 预期 exit 1，断言失败

Push-Location .mutation-checks\defect-2-nonpositive-keeps-old
go test -run 'TestNonPositiveTTLExpiresImmediately|TestCleanupDoesNotResurrectNonPositiveTTLEntries' -count=1 ./...
$code = $LASTEXITCODE
Pop-Location
# 预期 exit 1，断言失败

Push-Location .mutation-checks\defect-3-cleanup-deletes-valid
go test -run 'TestCleanupRemovesOnlyExpiredEntries|TestCleanupKeepsAllValidEntriesAndIsIdempotent|TestCleanupConcurrentWithSetGetDelete' -count=1 ./...
$code = $LASTEXITCODE
Pop-Location
# 预期 exit 1，断言失败
```

### 3. 编译检查

每个缺陷副本都能编译，只是断言失败：

```powershell
Push-Location .mutation-checks\defect-1-missed-expiry
go test -run '^$' -count=1 ./...
Pop-Location
# 预期 exit 0，[no tests to run]

# defect-2、defect-3 同理
```

### 4. 主目录回归

```powershell
go test -count=1 ./...
# 预期 exit 0

go list ./...
# 预期只输出 example.com/ttlcache
```

### 5. 哈希核对

```powershell
Get-FileHash cache.go, cleanup.go, cache_test.go, cleanup_test.go, go.mod -Algorithm SHA256
```

`evidence/08-hashes.txt` 保存了主目录与各副本的 SHA256 对照及断言结果：

- `delivery`：5 个文件全部 `MATCH`；
- `defect-1-missed-expiry`：仅 `cache.go` 为 `DIFF`；
- `defect-2-nonpositive-keeps-old`：仅 `cache.go` 为 `DIFF`；
- `defect-3-cleanup-deletes-valid`：仅 `cleanup.go` 为 `DIFF`。

## 已保存的真实结果

| 实验 | 预期 | 实际 exit | 日志 |
|---|---|---:|---|
| baseline delivery | 通过 | 0 | `evidence/01-baseline.txt` |
| defect-1 missed expiry | 断言失败 | 1 | `evidence/02-defect-1-missed-expiry.txt` |
| defect-2 nonpositive keeps old | 断言失败 | 1 | `evidence/03-defect-2-nonpositive-keeps-old.txt` |
| defect-3 cleanup deletes valid | 断言失败 | 1 | `evidence/04-defect-3-cleanup-deletes-valid.txt` |
| 三个缺陷副本编译 | 编译成功 | 0 | `evidence/05-compile-check.txt` |
| 根交付 `go test` | 通过 | 0 | `evidence/06-root-go-test.txt` |
| 根 `go list` | 只含主模块 | 0 | `evidence/07-root-go-list.txt` |
| 根交付 `go test -race`（附加） | 通过 | 0 | `evidence/09-root-go-test-race.txt` |

每次运行的实际命令、原始输出和 exit code 都写在对应日志中。

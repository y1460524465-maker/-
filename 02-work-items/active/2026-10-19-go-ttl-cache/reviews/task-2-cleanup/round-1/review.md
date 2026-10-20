# 子任务2审查

事项：2026-10-19-go-ttl-cache；前序：drafts/task-2-cleanup.md、委派task-2结果；状态：通过，打回0次。

## 行级审查

- cleanup.go:15–25：16获取写锁，19在锁内取一次now，20–23遍历时复用cache.go:71的到期判定并删除；整轮排他保证不会按旧条目快照误删新条目。nil map遍历安全、无锁升级或嵌套锁。
- cleanup_test.go:13–54：辅助函数加锁访问内部map，确实验证物理清除，不以Get未命中替代清除验证。
- cleanup_test.go:89–124：混合条目断言仅剩两项，并分别校验有效值；126–182检查全部过期和全部有效及幂等。
- cleanup_test.go:213起并发更新测试：初始过期条件经断言确认，屏障释放Set/Cleanup，两者完成后校验新值。该测试是调度压力验证，未声称穷举所有交错。
- cleanup_test.go:262起覆盖两个清理协程与八个读写删除协程，完成等待及超时检测有效。

## 独立验证

- 主控 go test -v -count=1 ./...：16项PASS，exit0，task-2-test.txt。
- 主控使用本地64位LLVM-MinGW、CC=clang、CGO_ENABLED=1运行 go test -race -count=1 ./...：PASS，exit0，race-toolchain-check.txt。环境阻塞已解除。
- bridge meta：HEAD未变，无执行者提交；新增文件仅cleanup.go与cleanup_test.go。

## 观察与结论

Minor：cleanup_test.go:93–97 captured now后调用Cleanup，真实调用时已晚于该时刻，不能单独证明精确等号；等号已由cache_test.go:129–142直接测试，任务3修正文案并减少sleep。无阻断问题，任务2通过；继续任务3完整测试与缺陷注入。

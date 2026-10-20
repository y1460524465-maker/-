# 子任务1审查

事项：2026-10-19-go-ttl-cache；前序：drafts/task-1-core.md、artifacts/delegation/*task-1-core-result.md；状态：阶段通过，打回0次。

## 主控独立核对

- cache.go:27–42 Set：写锁内初始化/覆盖，31–34 非正TTL删除旧值，40 写入时计算过期时间，满足约定。
- cache.go:47–59 Get：读锁保护全部查表和到期判断，55 使用71–72的 >= 语义；不写map，不存在读后误删新值窗口。
- cache.go:62–66 Delete：写锁，nil map/缺失key安全。
- cache_test.go:83–111 明确断言0/负TTL覆盖旧值及恢复写入；49–63 区分nil命中/缺失；129–142 到期等号直接测试。
- cache_test.go:145–179 并发初始化有屏障、等待和800个值逐一断言。182–224 共享key基础竞争，完整并发清理待任务3。
- 主控运行 go test -v ./...：9项PASS，exit0，详见 task-1-test.txt。meta确认Git HEAD未变。

## 非阻断观察（转任务3处理）

- Minor，cache_test.go:114–125：200ms TTL下先断言有效，若机器调度长暂停可能偶发失效；76–77 使用短sleep。任务3改为确定性过期断言，保留必要的真实时间集成测试时使用宽松窗口。
- 环境限制：现有gcc为32位 mingw32，执行者race构建报64-bit mode not compiled in。任务1门槛为基础单测，已通过；最终race验收尚未通过，主控准备本地64位编译器。

## 结论

任务1范围通过；无需要代码打回的问题。Cleanup尚未实现符合分阶段范围，继续下发任务2。主控未修改实现或测试代码。

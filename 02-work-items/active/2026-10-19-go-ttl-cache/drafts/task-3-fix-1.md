# 任务3审查打回第1轮 — 缺陷证据未持久化

事项：2026-10-19-go-ttl-cache；前序：task-3-tests结果；状态：需补齐证据。复用原session。
cwd：E:\多agent协作\work\active\2026-10-19-go-ttl-cache\workspaces\implementation。

## 具体问题

Important：任务3结果“缺陷注入明细”引用 C:\Users\user\AppData\Local\Temp\dsh-TRqXnS\ttlcache-mutation-20261019-201924。会话返回后主控 Test-Path 为False，无法读取副本、日志或重跑；临时目录生命周期结束，不能作为持久交付证据。原最终答复和events虽有输出，但没有可独立重跑的副本。功能测试本身初步通过。

## 修复目标与边界

仅在 cwd/.mutation-checks/ 重新建立delivery基线与三类缺陷实验，每个子目录包含独立go.mod确保主交付 go test ./... 跳过实验模块。每类：漏判过期、非正TTL残留旧值、Cleanup删除有效项。先运行基线通过，再运行缺陷测试得到断言失败，保存原始命令/输出/exit code与实际副本。不要修改cwd根任何.go文件、go.mod或README，不改治理文档，不提交Git。
保持原接口和边界：key缺失(nil,false)、ttl<=0立即旧值失效、四方法并发安全；实验仅验证测试能检出违反契约。

## 验收

- .mutation-checks/README.md说明重跑命令，evidence/*.txt保存真实日志。
- 三类注入均编译成功但测试断言失败（exit1），基线exit0。
- 测试副本与主目录Go文件哈希除预期变异外一致；返回路径主控能读取。不要只写临时目录。
- 根交付go test ./...仍通过。
- 使用同一已配好的本地Go/clang；禁止系统安装、外发、打印凭据或扩大范围。

只返回修改文件、重跑命令与真实结果、遗留问题。此次为任务3第1轮打回，最多两轮。

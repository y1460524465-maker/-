# T4 — net/http 中间件与示例

> 事项：2026-10-19-distributed-rate-limiter；前序：../brief.md、implementation-plan.md、CONTRACT.md；状态：prepared
> cwd：本事项 workspaces/implementation；角色：实现者，主控验收并唯一提交。

## 功能目标

提供 net/http 限流适配，不重复算法。先阅读真实 API 与 CONTRACT。
允许 middleware.go、middleware_test.go、examples/**。

## 输入输出契约

中间件接收具有 AllowContext 的限流器及 key/cost 提取函数，可用小接口便于 mock。
key/cost 提取函数可返回 error；默认 cost=1 可选，但行为要文档化。
允许调用下游一次；拒绝返回 429；存储错误返回 503；参数/提取错误 400；nil 配置构造报错不 panic。
把 r.Context() 传给 AllowContext；不要泄露内部 Redis 错误或原始 key。
示例展示三算法和双后端，默认运行不要求 Redis；Redis 示例仅显式启用。
不要编造 Retry-After；当前 API 没有精确重试时间。

## 边界条件

nil limiter/next/extractor、提取失败/空 key/非法 cost、取消、超时、false,nil、true,error 异常后端。
错误路径不得调用 next，不得重复写响应。
依赖已有 go.mod，不擅自增加 Web 框架。

## 验收标准

httptest 逐分支断言状态/调用次数/context 传播。
示例可编译；go test ./...、go test -race ./...、go vet ./... 实际执行。
先 RED 再 GREEN；不运行常驻 server 阻塞验收。

## 禁止事项

不改公共 API、内存、Redis、治理、go.mod，不提交/暂存/推送，不读凭据，不编写算法。

## 回报

修改文件、导出中间件契约、真实测试命令/结果、RED→GREEN、剩余问题。

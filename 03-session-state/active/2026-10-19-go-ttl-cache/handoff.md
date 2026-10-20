# Handoff — Go TTL Cache

## 唯一下一步
本事项功能与测试已验收，无需重新委派。目录分层后从仓库根目录运行 `python 01-agent-layer/scripts/workspace.py validate`；通过后把本事项 `STATUS.md` 与 `02-work-items/WORK_INDEX.md` 的状态改为 done，只暂存本事项和索引本事项行，再按 `item(2026-10-19-go-ttl-cache): deliver reviewed TTL cache and verification evidence` 提交。不得绕过 hook。

## 必读顺序
`01-agent-layer/AGENT_GUIDE.md`、`01-agent-layer/core/invariants.md`、本事项 `STATUS.md`、`02-work-items/active/2026-10-19-go-ttl-cache/brief.md`、`01-agent-layer/router/context-router.md`、`01-agent-layer/contexts/codex-review.md`、`01-agent-layer/contexts/sync.md`、工作层 `artifacts/final-summary.md`。

## 已完成，不要重复
三项DSH串行执行与主控审查，任务3补证据打回1次后通过。实现、测试、最终验证与缺陷副本均已落盘。所有实现/测试由执行者编写。不要为相同已通过的目标重新派发。

## 已知坑与禁止动作
主控不得写实现/测试；保留其他事项和原WORK_INDEX改动。默认gcc是32位，race需要本地64位clang；不要把早期环境失败当最终测试结果。初返DSH临时缺陷目录已消失，使用artifacts/mutation-snapshots和mutation-evidence持久证据。Minor TTL文案应理解为实际写入时起算。未授权推送、发布、删除或跨事项修复。

## 可直接运行的验证
在 `02-work-items/active/2026-10-19-go-ttl-cache/workspaces/implementation` 运行 `go test -count=1 ./...`、`go test -race -count=1 ./...`、`go test -count=20 ./...`。用户在 2026-10-20 要求删除本地 Go 工具链，因此当前不能直接复跑；上次结果见工作层 `artifacts/final-verification.txt`。恢复 Go 环境属于新的环境变更，先取得用户同意。
仓库根目录运行 `python 01-agent-layer/scripts/workspace.py validate` 已验证分层结构。

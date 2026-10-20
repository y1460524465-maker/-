# Reviews

这里保存 Codex 对执行结果的独立审查证据。

每次审查使用独立目录，不覆盖上一轮：

```text
reviews/
  <task-id>/
    round-1/
      review.md
      diff.patch
      test-output.txt
    round-2/
      review.md
      diff.patch
      test-output.txt
```

`review.md` 保存结论和检查范围；`diff.patch` 保存本轮实际变更；`test-output.txt` 保存 Codex 独立运行验证的原始输出。

DeepSeek 的请求、事件和返回结果仍放在 `artifacts/delegation/`，不要混入这里。

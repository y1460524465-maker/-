# DeepSeek Implementation Task — T2
Item ID: 2026-10-20-tri-model-probe
唯一工作目录: E:\多agent协作\02-work-items\active\2026-10-20-tri-model-probe\workspaces\t2
你是 DeepSeek 1017 实现者；Codex 主控，GLM 独立复核。
仅阅读本任务单、必要的入口规范及允许的两个源文件，不读其他事项。
# T2 brief / acceptance
实现 duration.py 的 parse_duration(value: str) -> int，返回精确毫秒数。
支持单位 ms、s、m、h、d，严格按 d、h、m、s、ms 顺序出现，可以跳过单位，同一单位不重复。
不允许任何空白。每段为 ASCII 十进制正整数（允许前导零但数值须 >0）；唯一零值例外是完整输入 "0s"，返回 0。
空字符串、负数、小数、未知单位、重复单位、单位顺序错误、零值组合均抛 ValueError。大小写单位不扩展。
超大值不得静默截断：在合理资源下返回 Python 任意精度精确整数；解释器资源/数字转换限制若拒绝，必须显式报错，不能给截断结果。
test_duration.py 使用 unittest，覆盖所有单单位、正常组合、零值、重复单位、顺序错误、空白输入、负数小数未知单位和超大值（至少超过 64 位）。
验证命令：python -B -m unittest discover -s . -p test_duration.py -v
只创建 duration.py 与 test_duration.py，使用 Python 标准库。

测试先行：先写 unittest，实际运行红灯，再实现并运行完整相关测试。保持实现简单。
禁止 Git 提交/暂存/推送；禁止修改 STATUS、handoff、brief、治理文件、其他事项；禁止创建 README 或额外交付文件。
完成只回报：修改文件列表；实际测试命令与原始结果（红灯和最终）；验收覆盖；剩余问题；本轮读取的去重文件数及路径；实际 token 若可见。

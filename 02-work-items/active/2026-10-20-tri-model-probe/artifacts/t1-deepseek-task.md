# DeepSeek Implementation Task — T1
Item ID: 2026-10-20-tri-model-probe
唯一工作目录: E:\多agent协作\02-work-items\active\2026-10-20-tri-model-probe\workspaces\t1
你是 DeepSeek 1017 实现者；Codex 主控，GLM 独立复核。
仅阅读本任务单、必要的入口规范及允许的两个源文件，不读其他事项。
# T1 brief / acceptance
实现 tags.py 的 normalize_tag(value: str) -> str。
按顺序：去首尾空白；转小写（str.lower）；连续 Unicode 空白合并为一个 ASCII 连字符；去结果首尾 ASCII 连字符。
保留 Unicode 字母、数字及其余标点，不做 ASCII 过滤或 Unicode 归一化。
空字符串、全空白抛 ValueError。非空但仅连字符可得到空串，不追加未要求的错误。
test_tags.py 使用 unittest，覆盖大小写、连续空格、制表符、换行、首尾空白、空输入、Unicode、标点及连字符边界。
验证命令：python -B -m unittest discover -s . -p test_tags.py -v
只创建 tags.py 与 test_tags.py，使用 Python 标准库。

测试先行：先写 unittest，实际运行红灯，再实现并运行完整相关测试。保持实现简单。
禁止 Git 提交/暂存/推送；禁止修改 STATUS、handoff、brief、治理文件、其他事项；禁止创建 README 或额外交付文件。
完成只回报：修改文件列表；实际测试命令与原始结果（红灯和最终）；验收覆盖；剩余问题；本轮读取的去重文件数及路径；实际 token 若可见。

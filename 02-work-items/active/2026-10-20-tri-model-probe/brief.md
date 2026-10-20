# Brief — 三模型协作探针 T1/T2
## 用户原始要求
三模型流程验证，不做正式业务开发。独立事项，不修改现有业务事项，不提交 Git。T3 暂不执行。
## 目标
Codex brief → DeepSeek 1017 实现自测 → Codex 冻结哈希/diff/摘要 → GLM 5.3 临时只读副本测试及功能审查 → Codex 过滤 → 同一 DeepSeek session 修复，最多两轮 → GLM 通过后 Codex 每任务仅一次最小关键验收及终审。
## 验收标准
# T1 brief / acceptance
实现 tags.py 的 normalize_tag(value: str) -> str。
按顺序：去首尾空白；转小写（str.lower）；连续 Unicode 空白合并为一个 ASCII 连字符；去结果首尾 ASCII 连字符。
保留 Unicode 字母、数字及其余标点，不做 ASCII 过滤或 Unicode 归一化。
空字符串、全空白抛 ValueError。非空但仅连字符可得到空串，不追加未要求的错误。
test_tags.py 使用 unittest，覆盖大小写、连续空格、制表符、换行、首尾空白、空输入、Unicode、标点及连字符边界。
验证命令：python -B -m unittest discover -s . -p test_tags.py -v
只创建 tags.py 与 test_tags.py，使用 Python 标准库。

# T2 brief / acceptance
实现 duration.py 的 parse_duration(value: str) -> int，返回精确毫秒数。
支持单位 ms、s、m、h、d，严格按 d、h、m、s、ms 顺序出现，可以跳过单位，同一单位不重复。
不允许任何空白。每段为 ASCII 十进制正整数（允许前导零但数值须 >0）；唯一零值例外是完整输入 "0s"，返回 0。
空字符串、负数、小数、未知单位、重复单位、单位顺序错误、零值组合均抛 ValueError。大小写单位不扩展。
超大值不得静默截断：在合理资源下返回 Python 任意精度精确整数；解释器资源/数字转换限制若拒绝，必须显式报错，不能给截断结果。
test_duration.py 使用 unittest，覆盖所有单单位、正常组合、零值、重复单位、顺序错误、空白输入、负数小数未知单位和超大值（至少超过 64 位）。
验证命令：python -B -m unittest discover -s . -p test_duration.py -v
只创建 duration.py 与 test_duration.py，使用 Python 标准库。

## 范围
仅本事项配对目录和创建时登记 WORK_INDEX。代码分别隔离在 workspaces/t1、t2。
## 非目标
不执行 T3；不升级正式协作规范；不提交 Git；不重复跑完整测试。
## 约束
DeepSeek 只写代码和 unittest，不写状态/交接。GLM 仅收到当轮 brief、diff、改动文件列表、DeepSeek 测试结果及必要执行指令；不发送仓库、旧 journal、无关事项。
每轮记录 session-id、输入/输出 Unicode 字符数、可见实际 token、墙钟耗时、读取去重文件数和测试结果；不可见必须标明，不以字符估算 token。
## 开放问题
无。T2 的正整数与 0s 特例按本 brief 明确解释。

# T2 brief / acceptance
实现 duration.py 的 parse_duration(value: str) -> int，返回精确毫秒数。
支持单位 ms、s、m、h、d，严格按 d、h、m、s、ms 顺序出现，可以跳过单位，同一单位不重复。
不允许任何空白。每段为 ASCII 十进制正整数（允许前导零但数值须 >0）；唯一零值例外是完整输入 "0s"，返回 0。
空字符串、负数、小数、未知单位、重复单位、单位顺序错误、零值组合均抛 ValueError。大小写单位不扩展。
超大值不得静默截断：在合理资源下返回 Python 任意精度精确整数；解释器资源/数字转换限制若拒绝，必须显式报错，不能给截断结果。
test_duration.py 使用 unittest，覆盖所有单单位、正常组合、零值、重复单位、顺序错误、空白输入、负数小数未知单位和超大值（至少超过 64 位）。
验证命令：python -B -m unittest discover -s . -p test_duration.py -v
只创建 duration.py 与 test_duration.py，使用 Python 标准库。

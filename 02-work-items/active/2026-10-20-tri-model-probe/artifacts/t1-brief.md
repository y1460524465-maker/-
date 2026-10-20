# T1 brief / acceptance
实现 tags.py 的 normalize_tag(value: str) -> str。
按顺序：去首尾空白；转小写（str.lower）；连续 Unicode 空白合并为一个 ASCII 连字符；去结果首尾 ASCII 连字符。
保留 Unicode 字母、数字及其余标点，不做 ASCII 过滤或 Unicode 归一化。
空字符串、全空白抛 ValueError。非空但仅连字符可得到空串，不追加未要求的错误。
test_tags.py 使用 unittest，覆盖大小写、连续空格、制表符、换行、首尾空白、空输入、Unicode、标点及连字符边界。
验证命令：python -B -m unittest discover -s . -p test_tags.py -v
只创建 tags.py 与 test_tags.py，使用 Python 标准库。

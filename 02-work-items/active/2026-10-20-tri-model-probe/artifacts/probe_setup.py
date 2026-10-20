from pathlib import Path
import json, shutil, tempfile

ROOT = Path(r'E:\多agent协作')
ITEM = '2026-10-20-tri-model-probe'
WORK = ROOT / '02-work-items/active' / ITEM
STATE = ROOT / '03-session-state/active' / ITEM

T1 = '''# T1 brief / acceptance
实现 tags.py 的 normalize_tag(value: str) -> str。
按顺序：去首尾空白；转小写（str.lower）；连续 Unicode 空白合并为一个 ASCII 连字符；去结果首尾 ASCII 连字符。
保留 Unicode 字母、数字及其余标点，不做 ASCII 过滤或 Unicode 归一化。
空字符串、全空白抛 ValueError。非空但仅连字符可得到空串，不追加未要求的错误。
test_tags.py 使用 unittest，覆盖大小写、连续空格、制表符、换行、首尾空白、空输入、Unicode、标点及连字符边界。
验证命令：python -B -m unittest discover -s . -p test_tags.py -v
只创建 tags.py 与 test_tags.py，使用 Python 标准库。
'''
T2 = '''# T2 brief / acceptance
实现 duration.py 的 parse_duration(value: str) -> int，返回精确毫秒数。
支持单位 ms、s、m、h、d，严格按 d、h、m、s、ms 顺序出现，可以跳过单位，同一单位不重复。
不允许任何空白。每段为 ASCII 十进制正整数（允许前导零但数值须 >0）；唯一零值例外是完整输入 "0s"，返回 0。
空字符串、负数、小数、未知单位、重复单位、单位顺序错误、零值组合均抛 ValueError。大小写单位不扩展。
超大值不得静默截断：在合理资源下返回 Python 任意精度精确整数；解释器资源/数字转换限制若拒绝，必须显式报错，不能给截断结果。
test_duration.py 使用 unittest，覆盖所有单单位、正常组合、零值、重复单位、顺序错误、空白输入、负数小数未知单位和超大值（至少超过 64 位）。
验证命令：python -B -m unittest discover -s . -p test_duration.py -v
只创建 duration.py 与 test_duration.py，使用 Python 标准库。
'''

for name, brief in [('t1', T1), ('t2', T2)]:
    cwd = WORK / 'workspaces' / name
    cwd.mkdir(parents=True, exist_ok=True)
    (WORK / 'artifacts' / f'{name}-brief.md').write_text(brief, encoding='utf-8')
    request = f'''# DeepSeek Implementation Task — {name.upper()}
Item ID: {ITEM}
唯一工作目录: {cwd}
你是 DeepSeek 1017 实现者；Codex 主控，GLM 独立复核。
仅阅读本任务单、必要的入口规范及允许的两个源文件，不读其他事项。
{brief}
测试先行：先写 unittest，实际运行红灯，再实现并运行完整相关测试。保持实现简单。
禁止 Git 提交/暂存/推送；禁止修改 STATUS、handoff、brief、治理文件、其他事项；禁止创建 README 或额外交付文件。
完成只回报：修改文件列表；实际测试命令与原始结果（红灯和最终）；验收覆盖；剩余问题；本轮读取的去重文件数及路径；实际 token 若可见。
'''
    (WORK / 'artifacts' / f'{name}-deepseek-task.md').write_text(request, encoding='utf-8')

(WORK / 'brief.md').write_text('''# Brief — 三模型协作探针 T1/T2
## 用户原始要求
三模型流程验证，不做正式业务开发。独立事项，不修改现有业务事项，不提交 Git。T3 暂不执行。
## 目标
Codex brief → DeepSeek 1017 实现自测 → Codex 冻结哈希/diff/摘要 → GLM 5.3 临时只读副本测试及功能审查 → Codex 过滤 → 同一 DeepSeek session 修复，最多两轮 → GLM 通过后 Codex 每任务仅一次最小关键验收及终审。
## 验收标准
''' + T1 + '\n' + T2 + '''
## 范围
仅本事项配对目录和创建时登记 WORK_INDEX。代码分别隔离在 workspaces/t1、t2。
## 非目标
不执行 T3；不升级正式协作规范；不提交 Git；不重复跑完整测试。
## 约束
DeepSeek 只写代码和 unittest，不写状态/交接。GLM 仅收到当轮 brief、diff、改动文件列表、DeepSeek 测试结果及必要执行指令；不发送仓库、旧 journal、无关事项。
每轮记录 session-id、输入/输出 Unicode 字符数、可见实际 token、墙钟耗时、读取去重文件数和测试结果；不可见必须标明，不以字符估算 token。
## 开放问题
无。T2 的正整数与 0s 特例按本 brief 明确解释。
''', encoding='utf-8')
baseline = Path(tempfile.gettempdir()) / 'tri-model-probe-baseline.json'
shutil.copy2(baseline, WORK / 'artifacts' / 'workspace-baseline.json')
(STATE / 'STATUS.md').write_text(f'''---
id: "{ITEM}"
title: "三模型协作流程验证 T1 T2"
status: active
updated: "2026-10-20"
owner: "Codex"
---
## 已完成
- 创建独立事项，已写 T1/T2 brief 及任务单；原始文件 SHA256 和 HEAD 已记录。
## 正在做
- 启动 DeepSeek 桌面实时模式并准备 T1 委派。
## 下一步
- T1 自测后冻结快照，交 GLM 5.3。
## 阻塞与待确认
- 无。
## 最近验证
- 尚未执行功能测试。
## 当前边界与有效不变量
- 仅探针目录；不提交 Git；T3 不执行；以 brief.md 为验收基线。
''', encoding='utf-8')
(STATE / 'handoff.md').write_text('''## 唯一下一步
执行 artifacts/t1-deepseek-task.md，cwd 为 workspaces/t1，使用桌面实时桥。
## 必读顺序
AGENT_GUIDE → 本事项 STATUS → handoff → brief → 当轮 reviews。
## 已完成，不要重复
已建事项和基线；不读其他事项。
## 已知坑与禁止动作
不提交 Git；不执行 T3；GLM 不接触原目录；Codex 不重复完整测试。
## 可直接运行的验证
GLM 通过后由 Codex 执行当轮 review 中的唯一最小验收命令。
''', encoding='utf-8')
(STATE / 'journal/2026-10-20.md').write_text('''### 启动 — Codex — 独立探针
- 路由：delegation+review+sync。
- 动作：读取规范、保存全工作区既有文件哈希/HEAD、创建事项与 brief。
- 结果：保护既有未提交改动；用户禁止 Git 优先于规范检查点要求。
- 证据：artifacts/workspace-baseline.json。
- 下一步：依次执行 T1、T2，不启动 T3。
''', encoding='utf-8')
print(WORK)

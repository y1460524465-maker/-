from pathlib import Path
import json, datetime, subprocess
ROOT=Path(r'E:\多agent协作'); ITEM='2026-10-20-tri-model-probe'
WORK=ROOT/'02-work-items/active'/ITEM; STATE=ROOT/'03-session-state/active'/ITEM
index=ROOT/'02-work-items/WORK_INDEX.md'
s=index.read_text(encoding='utf-8'); s=s.replace(f'| {ITEM} | 三模型协作流程验证 T1 T2 | planning |',f'| {ITEM} | 三模型协作流程验证 T1 T2 | done |'); index.write_text(s,encoding='utf-8')
(STATE/'STATUS.md').write_text(f'''---
id: "{ITEM}"
title: "三模型协作流程验证 T1 T2"
status: done
updated: "2026-10-20"
owner: "Codex"
---
## 已完成
- T1/T2 实现与 unittest；DeepSeek 桌面实时 1017；GLM 桌面 5.3 临时副本测试审查；Codex 最小验收与终审。
- T1 15 unittest+37 GLM 边界；T2 29 unittest+36 GLM 边界；均通过；修复 0 轮。
- 冻结哈希、diff、模型事件、统计和原目录不变证据已保存。
## 正在做
- 无；本次探针已收尾。
## 下一步
- 本轮不继续 T3。正式启用前另行验证修复回路并改进隔离与统计。
## 阻塞与待确认
- 不影响本次功能结论；完整流程认证未满足：Codex 无每任务独立计量、文件读取总数未精确埋点、T1 首次验收命令转义失败。
## 最近验证
- reviews/t1/round-1：PASS（有命令转义流程偏差）。
- reviews/t2/round-1：PASS。
- artifacts/integrity.json：既有业务不变、HEAD 不变、原始实现与副本哈希一致。
## 当前边界与有效不变量
- 无 Git 暂存/提交；T3 未执行；仅探针配对目录和索引登记；详见 brief.md。
''',encoding='utf-8')
(STATE/'handoff.md').write_text('''## 唯一下一步
阅读 artifacts/final-summary.md 与 metrics.json；本次无需继续代码工作。
## 必读顺序
AGENT_GUIDE → STATUS → brief → 两个 reviews/round-1/review.md → artifacts/final-summary.md。
## 已完成，不要重复
T1/T2 均 GLM PASS 并经 Codex 最小验收。不要重复完整测试。
## 已知坑与禁止动作
不提交 Git；不执行 T3；不要把可选建议当缺陷。文件只读属性不是进程级沙箱。计量 scope 不同不得直接解释为账单。
## 可直接运行的验证
python 02-work-items/active/2026-10-20-tri-model-probe/artifacts/integrity.py
上次：源文件/副本冻结 SHA256 相同；既有业务文件不变；HEAD 不变。
''',encoding='utf-8')
with (STATE/'journal/2026-10-20.md').open('a',encoding='utf-8') as f:
    f.write('''\n### 收尾 — Codex — T1/T2 探针
- 动作：两项 DeepSeek 实现，GLM 首轮通过，Codex 最小验收；保留全部事件与分轮证据。
- 结果：功能通过，GLM 有效问题/误报/修复轮均 0；T3 未执行。T1 首条 python -c 因 shell quoting SyntaxError 未执行测试，脚本有效执行一次。GLM 2 轮计量完整；Codex 共享 session 不能精确按任务分摊，读取数只提供明确范围及缺口。
- 证据：reviews/t1/round-1、reviews/t2/round-1、artifacts/metrics.json、integrity.json。
- 下一步：不建议立即正式启用，另行验证修复回路、隔离及低成本自动化。
''')
subprocess.run(['python',str(WORK/'artifacts/codex_metrics.py')],check=True)
codex=json.loads((WORK/'artifacts/codex-metrics.json').read_text(encoding='utf-8'))
codex['test_result']['t2']='single minimal acceptance passed'
(WORK/'artifacts/codex-metrics.json').write_text(json.dumps(codex,ensure_ascii=False,indent=2),encoding='utf-8')
metrics={'codex_shared_session':codex,'rounds':[],'glm_valid_findings':0,'glm_false_positives':0,'glm_optional_notes':4,'repair_rounds':{'t1':0,'t2':0},'limitations':['Codex same turn/session across tasks; no trustworthy per-task token split','Codex total content-read file count not instrumented; 9799 baseline hash reads known','visible character counts exclude hidden prompts/tool input; token usage includes model request contexts and caches','T1 initial shell SyntaxError then one effective minimal acceptance script','No failure encountered; fix loop not exercised','Windows readonly attributes and scope instructions are not OS enforced access isolation']}
for t in ['t1','t2']:
    metrics['rounds'].append(json.loads((WORK/'artifacts'/f'{t}-ds-metrics.json').read_text(encoding='utf-8')))
    metrics['rounds'].append(json.loads((WORK/'reviews'/t/'round-1/glm-metrics.json').read_text(encoding='utf-8')))
(WORK/'artifacts/metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
table='|Task/model|Input chars|Output chars|Actual tokens|Elapsed s|Read files|\n|---|---:|---:|---:|---:|---:|\n'
for r in metrics['rounds']:
    tok=r['actual_tokens'].get('totalTokens',r['actual_tokens'].get('total_tokens'))
    table+=f"|{r['task']}/{r['model']}|{r['input_chars']}|{r['output_chars']}|{tok}|{r['elapsed_s']}|{r['read_files']}|\n"
(WORK/'artifacts/final-summary.md').write_text('''# 三模型流程探针结果
T1：15 unittest、37 GLM 边界通过；Codex 最小验收通过（首次 shell quoting 失败，实际脚本执行一次）。
T2：29 unittest、36 GLM 边界通过；Codex 唯一最小验收通过。均首轮 PASS，未修复，T3 未执行。
## 每轮统计
'''+table+f'''\nCodex shared session {codex['session_id']}：截至 {codex['token_usage_as_of']}，实际累计 token {codex['actual_tokens']['total_tokens']}，缓存输入 {codex['actual_tokens']['cached_input_tokens']}；墙钟 {codex['elapsed_s']:.1f}s。输入/输出可见字符 {codex['input_chars_user_messages']}/{codex['output_chars_assistant_visible']}。无法可信拆分 T1/T2；全量内容读取数未埋点，基线哈希读取 9799 个。
## 问题与结论
GLM 有效缺陷 0，误报 0，非阻塞建议/观察 4。修复闭环未触发，不能宣称已验证。
GLM 手工转换“必要”的描述被 Codex 过滤：brief 允许超资源显式拒绝，因此不是强制做法。
本次文件只读属性不等于 OS 权限隔离，模型有完整权限，本轮仅证明其遵守边界和哈希未变。
桌面切换及长上下文重复请求导致主控成本过大。暂不建议正式全面启用；可继续有限试运行，先补自动采集、硬隔离、修复路径验证。无 Git 提交。
''',encoding='utf-8')
print(json.dumps({'codex_tokens':codex['actual_tokens'],'elapsed_s':codex['elapsed_s']},ensure_ascii=True))

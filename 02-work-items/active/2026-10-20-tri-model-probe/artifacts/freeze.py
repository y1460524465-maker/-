from pathlib import Path
import json, hashlib, difflib, tempfile, shutil, sys, datetime, os
ITEM='2026-10-20-tri-model-probe'
WORK=Path(r'E:\多agent协作\02-work-items\active')/ITEM

task=sys.argv[1]
files={'t1':['tags.py','test_tags.py'],'t2':['duration.py','test_duration.py']}[task]
review=WORK/'reviews'/task/'round-1'
review.mkdir(parents=True,exist_ok=True)
cwd=WORK/'workspaces'/task
snapshot=Path(tempfile.gettempdir())/f'{ITEM}-{task}-r1'
snapshot.mkdir(exist_ok=False)
diff=''
hashes={}
for name in files:
    data=(cwd/name).read_bytes()
    hashes[name]=hashlib.sha256(data).hexdigest()
    diff+=''.join(difflib.unified_diff([],data.decode('utf-8').splitlines(keepends=True),fromfile='/dev/null',tofile=name))
    shutil.copy2(cwd/name,snapshot/name)
    os.chmod(snapshot/name,0o444)
(review/'diff.patch').write_text(diff,encoding='utf-8')
(review/'hashes.json').write_text(json.dumps({'frozen_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(cwd),'snapshot':str(snapshot),'sha256':hashes},ensure_ascii=False,indent=2),encoding='utf-8')
result=next((WORK/'artifacts/delegation').glob(f'*-{task}-implement-result.md')).read_text(encoding='utf-8')
tests=result.split('实际测试命令与原始结果',1)[-1].split('验收覆盖')[0].strip().rstrip('#').strip()
request=f'''三模型流程探针 {task.upper()} / GLM round 1。你是 GLM 5.3 独立审查者，只使用以下四项输入，不读取记忆、仓库、journal、AGENTS 或任何其他材料。不要修改源文件、不要 Git。
测试副本目录（仅含改动文件，文件已设只读）：{snapshot}
仅在此目录实际运行 brief 中 unittest（-B 禁止字节码写入），并做必要的独立边界验证及代码审查；不要读取 E:\\多agent协作 原目录。结果只在最终答复中输出，禁止写文件。
请报告 PASS/FAIL、实际命令与完整结果、每条有效问题的位置/复现/预期、读取的去重文件数、session-id 和实际 token（若可见，否则标明不可见）。区分需求缺陷与可选建议。不要扩展验收标准。报告自身执行耗时。

## 1 当前 brief 验收标准
{(WORK/'artifacts'/f'{task}-brief.md').read_text(encoding='utf-8')}
## 2 diff
```diff
{diff}```
## 3 改动文件列表
{', '.join(files)}
## 4 DeepSeek 测试结果
{tests}
'''
(review/'glm-input.txt').write_text(request,encoding='utf-8')
print(json.dumps({'snapshot':str(snapshot),'input_chars':len(request),'hashes':hashes},ensure_ascii=True))

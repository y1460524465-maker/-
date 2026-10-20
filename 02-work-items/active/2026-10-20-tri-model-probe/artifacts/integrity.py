from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(r'E:\多agent协作')
ITEM='2026-10-20-tri-model-probe'
WORK=ROOT/'02-work-items/active'/ITEM
b=json.loads((WORK/'artifacts/workspace-baseline.json').read_text(encoding='utf-8'))
changed=[]; missing=[]
for name,sha in b['files'].items():
    p=ROOT/name
    if not p.is_file(): missing.append(name)
    elif hashlib.sha256(p.read_bytes()).hexdigest()!=sha: changed.append(name)
frozen={}
for task in ['t1','t2']:
    f=json.loads((WORK/'reviews'/task/'round-1/hashes.json').read_text(encoding='utf-8'))
    frozen[task]={kind:all(hashlib.sha256((Path(f[kind])/n).read_bytes()).hexdigest()==h for n,h in f['sha256'].items()) for kind in ['source','snapshot']}
new_files=[str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.relative_to(ROOT).parts and str(p.relative_to(ROOT)) not in b['files']]
unexpected_new=[p for p in new_files if ITEM not in p.split('\\')]
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
result=dict(baseline_files=len(b['files']),changed_existing=changed,missing_existing=missing,unexpected_new=unexpected_new,head_unchanged=head==b['head'],frozen_hash_match=frozen,existing_business_unchanged=not missing and changed==['02-work-items\\WORK_INDEX.md'])
(WORK/'artifacts/integrity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=True))

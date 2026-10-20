from pathlib import Path
import json,datetime
ITEM='2026-10-20-tri-model-probe'
WORK=Path(r'E:\多agent协作\02-work-items\active')/ITEM
sid='01a1579a-87db-72d1-bd1a-62001f849482'
p=next((Path.home()/'.codex/sessions').rglob(f'*{sid}*'))
rows=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
counts=[r for r in rows if r.get('type')=='event_msg' and r.get('payload',{}).get('type')=='token_count']
last=counts[-1]
messages=[r['payload'] for r in rows if r.get('type')=='response_item' and r.get('payload',{}).get('type')=='message']
def chars(ms,role):
    return sum(len(b.get('text','')) for m in ms if m.get('role')==role for b in m.get('content',[]))
start=datetime.datetime.fromisoformat(rows[0]['timestamp'].replace('Z','+00:00'))
now=datetime.datetime.now(datetime.timezone.utc)
result=dict(model=next(r['payload'].get('model') for r in rows if r.get('type')=='turn_context'),session_id=sid,scope='shared orchestration session: setup + T1 + T2; cannot honestly split per-task model usage',as_of=now.isoformat(),token_usage_as_of=last['timestamp'],actual_tokens=last['payload']['info']['total_token_usage'],input_chars_user_messages=chars(messages,'user'),output_chars_assistant_visible=chars(messages,'assistant'),elapsed_s=(now-start).total_seconds(),read_files={'baseline_hash_reads':9799,'t1_implementation_and_tests_content':2,'t2_implementation_and_tests_content':2,'total_content_read_count':'not exactly observable; command-level calls batched policy/files/events reads, not instrumented'},test_result={'t1':'minimal passed; initial shell quoting SyntaxError before import, then single effective script run','t2':'pending'},character_scope='visible user message content and assistant text only; excludes tools, reasoning and system/developer prompts')
(WORK/'artifacts/codex-metrics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=True))

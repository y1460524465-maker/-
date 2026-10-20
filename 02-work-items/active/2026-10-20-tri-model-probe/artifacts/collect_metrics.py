from pathlib import Path
import json, sys, datetime
ITEM='2026-10-20-tri-model-probe'
WORK=Path(r'E:\多agent协作\02-work-items\active')/ITEM

def ds_metrics(task):
    meta=next((WORK/'artifacts/delegation').glob(f'*-{task}-implement-meta.json'))
    m=json.loads(meta.read_text(encoding='utf-8'))
    rs=[json.loads(l) for l in Path(m['events_path']).read_text(encoding='utf-8').splitlines()]
    es=[r['event'] for r in rs if r.get('type')=='event']
    messages=[e['data'] for e in es if e['type']=='assistant/message']
    usages=[x['usage'] for x in messages if x.get('usage')]
    prompt=(WORK/'artifacts'/f'{task}-deepseek-task.md').read_text(encoding='utf-8')
    user_messages=[e['data'] for e in es if e['type']=='user/message']
    def chars(content):
        if isinstance(content,str): return len(content)
        if isinstance(content,list): return sum(len(b.get('text','')) for b in content)
        return 0
    visible_user_chars=sum(chars(x.get('content',[])) for x in user_messages)
    output=''.join(b.get('text','') for x in messages for b in x['message'].get('content',[]) if b.get('type')=='text')
    final=Path(m['result_path']).read_text(encoding='utf-8').split('## Final\n',1)[-1].split('\n## Diagnostics')[0].strip()
    return dict(model='DeepSeek 1017',task=task,round=1,session_id=m['session_id'],input_chars=len(prompt),visible_user_message_chars=visible_user_chars,output_chars=len(output),final_output_chars=len(final),actual_tokens={k:sum(u.get(k,0) for u in usages) for k in usages[0]},elapsed_s=(es[-1]['time']-es[0]['time'])/1000,read_files=2 if task=='t1' else 3,test_result='see saved events and result',character_scope='explicit task / all assistant text; reasoning and tool arguments excluded')

def glm_metrics(task):
    p=next((Path.home()/'.workbuddy/projects').glob(f'*{ITEM}-{task}-r1/*.jsonl'))
    rs=[json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
    assistants=[r for r in rs if r.get('type')=='message' and r.get('role')=='assistant']
    seen={}
    for r in rs:
        d=r.get('providerData') or {}
        if d.get('rawUsage'):
            seen[(d.get('conversationRequestId'),d.get('messageId'),d.get('stepSeq'))]=d['rawUsage']
    final=''.join(b.get('text','') for b in assistants[-1].get('content',[]) if b.get('type')=='output_text') if assistants else ''
    out=''.join(b.get('text','') for r in assistants for b in r.get('content',[]) if b.get('type')=='output_text')
    review=WORK/'reviews'/task/'round-1'
    (review/'glm-events.jsonl').write_text(p.read_text(encoding='utf-8'),encoding='utf-8')
    (review/'glm-result.md').write_text(final,encoding='utf-8')
    tools='\n\n'.join(json.dumps(r.get('providerData',{}).get('toolResult',{}),ensure_ascii=False) for r in rs if r.get('type')=='function_call_result')
    (review/'glm-test-output.txt').write_text(tools,encoding='utf-8')
    m=dict(model='GLM 5.3',task=task,round=1,session_id=p.stem,input_chars=len((review/'glm-input.txt').read_text(encoding='utf-8')),output_chars=len(out),final_output_chars=len(final),actual_tokens={k:sum(u.get(k,0) for u in seen.values()) for k in ['prompt_tokens','completion_tokens','total_tokens','prompt_cache_hit_tokens','prompt_cache_miss_tokens']},elapsed_s=(assistants[-1]['timestamp']-next(r['timestamp'] for r in rs if r.get('role')=='user'))/1000 if assistants else None,read_files=2,character_scope='explicit input package / all assistant output_text; hidden system input and tool output excluded',test_result='see glm-result.md')
    (review/'glm-metrics.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(m,ensure_ascii=True)); print(final.encode('ascii','backslashreplace').decode()[:25000])
    return m

if __name__=='__main__':
    task=sys.argv[1]
    if sys.argv[2]=='ds':
        m=ds_metrics(task)
        (WORK/'artifacts'/f'{task}-ds-metrics.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(m,ensure_ascii=True))
    else:
        glm_metrics(task)

#!/usr/bin/env python3
"""Elapsed-time decay for the existing integer-valued Emotion Engine."""
import argparse, contextlib, datetime as dt, fcntl, hashlib, json, math, os, pathlib, tempfile, time

DIMS = ('pleasure','arousal','stress','curiosity','trust','social','fatigue')
DEFAULT_ROOT = pathlib.Path('/home/ubuntu/.openclaw/workspace/memory/emotion')

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def validate(state):
    for k in DIMS:
        v=state[k]
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):
            raise ValueError('invalid dimension: '+k)
    if state.get('updated_at') is not None: timestamp(state['updated_at'])

def timestamp(value):
    x=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    if x.tzinfo is None: raise ValueError('timestamp must include timezone')
    return x.timestamp()

def iso(value):
    return dt.datetime.fromtimestamp(value,dt.timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')

def fingerprint(state):
    return hashlib.sha256(json.dumps({k:state.get(k) for k in (*DIMS,'updated_at')},sort_keys=True).encode()).hexdigest()

def dominant(s):
    p,a,st,c,t,so,f=(s[k] for k in DIMS); tags=[]
    if p>70:tags.append('愉悦')
    elif p<30:tags.append('低落')
    if st>70:tags.append('压力大')
    elif st>50:tags.append('有些压力')
    elif st<20:tags.append('放松')
    if a>70:tags.append('兴奋')
    elif a<30:tags.append('迟缓')
    if c>70:tags.append('好奇')
    elif c<30:tags.append('保守')
    if f>70:tags.append('疲惫')
    elif f<20:tags.append('精力充沛')
    if p>50 and st<40 and a<60:tags.append('平静')
    return '、'.join(tags) or '中性'

def context(s):
    labels=(('pleasure','愉悦度'),('stress','压力'),('fatigue','疲劳'),('curiosity','好奇'),('trust','信任'),('social','社交需求'),('arousal','兴奋度'))
    return ('Emotion Context\n\n当前情绪状态：\n'+s['dominant_emotion']+'。\n\n情绪系统：\nEmotion Engine v1\n\n状态摘要：\n'+
            ''.join(f'- {label}: {s[key]}\n' for key,label in labels)+'\n注意：\n当前情绪只用于辅助 Agent 表达和行为倾向，不改变安全规则、权限、Provider 或系统配置。\n')

def encode(v):return json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n'

def atomic(path,text):
    data=text.encode('utf-8')
    if path.exists() and path.read_bytes()==data:return
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        os.fchmod(fd,path.stat().st_mode & 0o777 if path.exists() else 0o600)
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        if path.suffix=='.json':json.loads(pathlib.Path(tmp).read_text())
        os.replace(tmp,path)
        dfd=os.open(path.parent,os.O_DIRECTORY)
        try:os.fsync(dfd)
        finally:os.close(dfd)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

@contextlib.contextmanager
def locked(root,timeout,dry):
    path=root/'.emotion.lock'
    # A dry run never creates even a lock file.
    fd=os.open(path,os.O_RDONLY) if dry and path.exists() else (os.open(root,os.O_RDONLY) if dry else os.open(path,os.O_CREAT|os.O_RDWR,0o600))
    start=time.monotonic()
    try:
        while True:
            try:fcntl.flock(fd,(fcntl.LOCK_SH if dry else fcntl.LOCK_EX)|fcntl.LOCK_NB);break
            except BlockingIOError:
                if time.monotonic()-start>=timeout:raise TimeoutError('emotion lock busy')
                time.sleep(.025)
        yield
    finally:os.close(fd)

def run(root,config,now,dry=False,lock_timeout=10):
    root=pathlib.Path(root); cfg=load(pathlib.Path(config))
    if set(cfg['dimensions'])!=set(DIMS):raise ValueError('dimension configuration mismatch')
    for k,v in cfg['dimensions'].items():
        if not 0<=v['baseline']<=100 or v['half_life_hours']<=0:raise ValueError('invalid decay config')
    with locked(root,lock_timeout,dry):
        state=load(root/'state.json');validate(state)
        if state.get('updated_at'):now=max(now,timestamp(state['updated_at']))
        cursor_path=root/'decay-cursor.json'
        cursor=load(cursor_path) if cursor_path.exists() else {}
        # An event writer changes the fingerprint, so reset to that real event.
        if cursor.get('last_fingerprint')!=fingerprint(state):
            cursor={'anchor_at':state.get('updated_at') or iso(now),'anchor':{k:state[k] for k in DIMS},'last_logged':{k:state[k] for k in DIMS},'last_log_at':0}
        elapsed=max(0,now-timestamp(cursor['anchor_at']))
        out=dict(state)
        for k in DIMS:
            v=cfg['dimensions'][k];anchor=max(0,min(100,cursor['anchor'][k]));base=v['baseline']
            value=base+(anchor-base)*math.exp2(-elapsed/(v['half_life_hours']*3600))
            out[k]=int(max(0,min(100,math.floor(value+.5))))
        out['dominant_emotion']=dominant(out)
        changed=any(out[k]!=state[k] for k in DIMS)
        # A backwards clock never advances the cursor or double-applies decay.
        previous=timestamp(state['updated_at']) if state.get('updated_at') else None
        if previous is None or now>previous:out['updated_at']=iso(now)
        validate(out)
        distance=max(abs(out[k]-cursor['last_logged'][k]) for k in DIMS)
        should_log=changed and distance>=cfg['history_threshold'] and now-cursor.get('last_log_at',0)>=cfg['history_min_interval_seconds']
        row={'timestamp':iso(now),'event_type':'decay','elapsed_seconds':elapsed,'delta':{k:out[k]-state[k] for k in DIMS if out[k]!=state[k]},'new_state':{k:out[k] for k in (*DIMS,'dominant_emotion')}}
        result={'dry_run':dry,'elapsed_seconds':elapsed,'dimensions_changed':changed,'history_recorded':bool(should_log and not dry),'state':out}
        if dry:return result
        # All serialization and validation occurs before replacing state.
        state_text=encode(out);ctx=context(out)
        atomic(root/'context.md',ctx);atomic(root/'state.json',state_text)
        if should_log:
            with (root/'history.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
            cursor['last_logged']={k:out[k] for k in DIMS};cursor['last_log_at']=now
        cursor['last_fingerprint']=fingerprint(out)
        atomic(cursor_path,encode(cursor))
        return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=pathlib.Path,default=DEFAULT_ROOT);ap.add_argument('--config',type=pathlib.Path);ap.add_argument('--dry-run',action='store_true');ap.add_argument('--now');ap.add_argument('--lock-timeout',type=float,default=10)
    a=ap.parse_args()
    try:print(json.dumps(run(a.root,a.config or a.root/'decay-config.json',timestamp(a.now) if a.now else time.time(),a.dry_run,a.lock_timeout),ensure_ascii=False))
    except Exception as e:print(json.dumps({'ok':False,'error':type(e).__name__+': '+str(e)}));raise SystemExit(1)

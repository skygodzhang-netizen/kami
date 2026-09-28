#!/usr/bin/env python3
"""Bounded infrastructure checks; existing OpenClaw scheduler is authoritative."""
import argparse,datetime as dt,fcntl,hashlib,json,os,pathlib,re,shutil,socket,sqlite3,ssl,subprocess,sys,time,urllib.request
ROOT=pathlib.Path('/home/ubuntu/.openclaw');WS=ROOT/'workspace';OUT=WS/'reports/health-checks'

def command(argv,timeout=20):
    p=subprocess.run(argv,capture_output=True,text=True,timeout=timeout)
    return p.returncode,p.stdout.strip(),p.stderr.strip()

def cli_json(argv,timeout=35):
    code,out,err=command(['openclaw',*argv],timeout)
    if code:raise RuntimeError('OpenClaw command failed: '+str(code))
    return json.loads(out)

def atomic(path,obj):
    tmp=path.with_name('.'+path.name+'.'+str(os.getpid()))
    try:
        with tmp.open('x',encoding='utf-8') as f:os.chmod(tmp,0o600);json.dump(obj,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if tmp.exists():tmp.unlink()

def get_json(url,headers=None,attempts=2):
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=headers or {}),timeout=8) as response:return response.status,json.load(response)
        except Exception:
            if attempt+1==attempts:raise
            time.sleep(1)

def run(kind,test=False,deliver=True):
    OUT.mkdir(parents=True,exist_ok=True,mode=0o700)
    with (OUT/'.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('another health check is active')
        config=json.loads((ROOT/'openclaw.json').read_text());policy=json.loads((WS/'config/health-check-policy.json').read_text())
        report={'kind':kind,'test':test,'started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'timezone':'Asia/Shanghai','checks':{},'recovery':[]}
        def check(name,fn):
            started=time.monotonic()
            try:value=fn();report['checks'][name]={'ok':True,'value':value,'duration_ms':round((time.monotonic()-started)*1000)}
            except Exception as e:report['checks'][name]={'ok':False,'error':type(e).__name__,'duration_ms':round((time.monotonic()-started)*1000)}
        def services():
            result={}
            for name in ['openclaw-gateway','caddy']:
                active=command(['systemctl','is-active',name])[1]
                if active!='active' and not pathlib.Path('/run/openclaw-maintenance').exists() and command(['systemctl','is-enabled',name])[0]==0:
                    allowed=name=='openclaw-gateway'
                    if name=='caddy':
                        path=pathlib.Path(policy['caddy_config_path'])
                        allowed=hashlib.sha256(path.read_bytes()).hexdigest()==policy['caddy_config_sha256'] and command(['sudo','-n','caddy','validate','--config',str(path)],15)[0]==0
                    if allowed:
                        rc,_,_=command(['sudo','-n','systemctl','restart',name],25);time.sleep(1)
                        report['recovery'].append({'service':name,'attempts':1,'exit':rc})
                        active=command(['systemctl','is-active',name])[1]
                result[name]=active
            return result
        check('services',services)
        check('gateway_port',lambda: port())
        check('nodes',lambda:[{k:n.get(k) for k in ['nodeId','displayName','connected','paired','caps']} for n in cli_json(['nodes','status','--json'])['nodes']])
        def ha():
            token=(WS/'config/ha-token').read_text().strip();headers={'Authorization':'Bearer '+token}
            status,data=get_json('http://127.0.0.1:8123/api/states',headers)
            return {'status':status,'entity_count':len(data)}
        check('ha',ha)
        def telegram():
            accounts={}
            for account in ('default','skykami'):
                status,data=get_json('https://api.telegram.org/bot'+config['channels']['telegram']['accounts'][account]['botToken']+'/getMe')
                accounts[account]={'status':status,'ok':data['ok'],'username':data['result']['username']}
            return accounts
        check('telegram',telegram)
        used=shutil.disk_usage('/');check('disk',lambda:{'total':used.total,'used':used.used,'free':used.free,'used_percent':round(used.used/used.total*100,1)})
        hours=1 if kind=='quick' else (24 if kind=='evening' else 12)
        def errors():
            code,text,_=command(['journalctl','-u','openclaw-gateway','--since',str(hours)+' hours ago','--no-pager','-o','cat'],20)
            patterns={'crash':r'uncaughtException|segmentation fault|core dumped','database_lock':r'SQLITE_BUSY|SQLITE_LOCKED','provider_429':r'status=429','telegram_send_failed':r'sendMessage failed','polling_conflict':r'409 Conflict|terminated by other getUpdates','timeouts':r'timed out|TimeoutError'}
            return {'hours':hours,'counts':{k:len(re.findall(v,text,re.I)) for k,v in patterns.items()}}
        check('errors',errors)
        if kind!='quick':
            check('versions',lambda:{'openclaw':json.loads(pathlib.Path('/usr/lib/node_modules/openclaw/package.json').read_text())['version'],'node':command(['node','--version'])[1]})
            check('resources',lambda:{'load':os.getloadavg(),'meminfo':{k:int(v.split()[0]) for k,v in (line.split(':',1) for line in pathlib.Path('/proc/meminfo').read_text().splitlines()) if k in ['MemTotal','MemAvailable','SwapTotal','SwapFree']}})
            def database():
                rows=[]
                for path in [ROOT/'state/openclaw.sqlite',ROOT/'agents/main/agent/openclaw-agent.sqlite',ROOT/'agents/ops/agent/openclaw-agent.sqlite']:
                    start=time.monotonic();db=sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True,timeout=2)
                    try:
                        db.set_progress_handler(lambda:1 if time.monotonic()-start>8 else 0,10000)
                        rows.append({'path':str(path),'bytes':path.stat().st_size,'quick_check':db.execute('pragma quick_check').fetchone()[0],'journal':db.execute('pragma journal_mode').fetchone()[0]})
                    finally:db.close()
                return rows
            check('sqlite',database)
            check('agents',lambda:{agent:{'workspace_exists':pathlib.Path(config['agents']['entries'][agent]['workspace']).is_dir(),'database_exists':(ROOT/'agents'/agent/'agent/openclaw-agent.sqlite').is_file()} for agent in ['main','ops']})
            def emotion():
                s=json.loads((WS/'memory/emotion/state.json').read_text());dims=('pleasure','arousal','stress','curiosity','trust','social','fatigue')
                assert all(isinstance(s[k],(int,float)) and 0<=s[k]<=100 for k in dims)
                assert s['dominant_emotion'] in (WS/'memory/emotion/context.md').read_text()
                return {'valid':True,'updated_at':s.get('updated_at'),'dominant':s['dominant_emotion'],'decay_config_exists':(WS/'memory/emotion/decay-config.json').exists()}
            check('emotion',emotion)
            def evolution():
                s=json.loads((ROOT/'evolution/controller/state.json').read_text());safety=s['safety']
                assert s['status']=='STABLE' and safety['kill_switch'] is True and safety['production_apply_enabled'] is False
                return {'status':s['status'],'kill_switch':True,'production_apply_enabled':False}
            check('evolution',evolution)
            def tls():
                ctx=ssl.create_default_context()
                with socket.create_connection(('claw.wsszlh.icu',18443),timeout=8) as sock:
                    with ctx.wrap_socket(sock,server_hostname='claw.wsszlh.icu') as secure:
                        cert=secure.getpeercert();expiry=ssl.cert_time_to_seconds(cert['notAfter']);return {'verified':True,'not_after':cert['notAfter'],'days_remaining':round((expiry-time.time())/86400,1)}
            check('tls',tls)
            check('scheduler',lambda:[{k:j.get(k) for k in ['id','name','enabled','nextRunAtMs','lastRunStatus']} for j in cli_json(['cron','list','--json'])['jobs']])
        if kind=='evening':
            check('backup',lambda:{'recent_directories':[p.name for p in sorted((ROOT/'backups').iterdir(),key=lambda p:p.stat().st_mtime,reverse=True)[:5]],'count':len(list((ROOT/'backups').iterdir()))})
            prior=OUT/'latest-evening.json'
            if prior.exists():
                old=json.loads(prior.read_text());previous=old.get('checks',{}).get('disk',{}).get('value',{}).get('used');check('disk_growth',lambda:{'used_bytes_delta':used.used-previous if previous is not None else None})
            else:check('disk_growth',lambda:{'used_bytes_delta':None,'reason':'first baseline'})
            def provider():
                p=config['models']['providers']['agnes'];status,data=get_json(p['baseUrl'].rstrip('/')+'/models',{'Authorization':'Bearer '+p['apiKey'],'User-Agent':'curl/8.0'})
                return {'http_status':status,'models_available':isinstance(data,dict) and 'data' in data,'scope':'authenticated catalog, no paid generation'}
            check('provider',provider)
        warnings=[k for k,v in report['checks'].items() if not v['ok']]
        values={k:v.get('value') for k,v in report['checks'].items()}
        for name,status in (values.get('services') or {}).items():
            if status!='active':warnings.append(name+':'+status)
        for n in values.get('nodes') or []:
            if n['nodeId'].startswith(('43691e92','ae58d203')) and not n['connected']:warnings.append(n['displayName']+' offline')
        for row in values.get('sqlite') or []:
            if row['quick_check']!='ok':warnings.append('sqlite integrity')
        if values.get('disk',{}).get('used_percent',0)>85:warnings.append('disk >85%')
        report['warnings']=warnings;report['completed_at']=dt.datetime.now(dt.timezone.utc).isoformat()
        stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S');path=OUT/(stamp+'-'+kind+('-test' if test else '')+'.json')
        # Send one concise report to the pre-existing owner. No retry after ambiguous send.
        report['delivery']={'requested':deliver,'ok':False}
        atomic(path,report)
        if deliver:
            assert config['channels']['telegram']['accounts']['default']['allowFrom']==[policy['owner_telegram_id']]
            lines=[f'OpenClaw {kind.title()} Check'+(' [TEST]' if test else ''),dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')+' Asia/Shanghai', '检查完成；'+('发现事项：'+', '.join(warnings) if warnings else '检查项正常'),f'Gateway/Caddy: {values.get("services")}',f'HA: {values.get("ha")}',f'Disk: {values.get("disk",{}).get("used_percent")}%']
            if kind!='quick':lines.extend([f'Emotion: {values.get("emotion")}',f'Evolution: {values.get("evolution")}',f'TLS: {values.get("tls")}',f'DB: {len(values.get("sqlite") or [])} checked'])
            lines.append('日志：'+str(path))
            try:
                response=cli_json(['message','send','--channel','telegram','--account','default','--target',str(policy['owner_telegram_id']),'--message','\n'.join(lines),'--json'],60)
                report['delivery']={'requested':True,'ok':True,'receipt':response}
            except Exception as e:report['delivery']={'requested':True,'ok':False,'error':type(e).__name__,'blind_retry':False}
        atomic(path,report);atomic(OUT/('latest-'+kind+'.json'),report)
        print(json.dumps({'kind':kind,'checks':len(report['checks']),'warnings':warnings,'delivery':report['delivery'],'log':str(path)},ensure_ascii=False))
        return 0 if not deliver or report['delivery']['ok'] else 2

def port():
    with socket.create_connection(('127.0.0.1',18789),timeout=3):return {'listening':True,'port':18789}

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('kind',choices=['morning','quick','evening']);a.add_argument('--test',action='store_true');a.add_argument('--no-deliver',action='store_true');args=a.parse_args()
    try:sys.exit(run(args.kind,args.test,not args.no_deliver))
    except Exception as e:print(json.dumps({'error':type(e).__name__,'ok':False}));sys.exit(1)

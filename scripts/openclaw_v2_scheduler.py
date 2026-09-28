#!/usr/bin/env python3
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--cron',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();d=json.loads(a.cron.read_text());jobs=d.get('jobs',[]);ids=[j.get('id') for j in jobs];names=[j.get('name') or j.get('declarationKey') for j in jobs]
r={'generatedAt':datetime.now(timezone.utc).isoformat(),'total':len(jobs),'enabled':sum(j.get('enabled',False) for j in jobs),'duplicateIds':len(ids)!=len(set(ids)),'duplicateNames':len(names)!=len(set(names)),'policy':'observe/evaluate only; no scheduler production apply','healthy':all(j.get('state',{}).get('lastStatus') in (None,'ok') for j in jobs)}
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps(r,ensure_ascii=False))
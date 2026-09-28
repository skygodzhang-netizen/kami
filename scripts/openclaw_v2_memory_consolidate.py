#!/usr/bin/env python3
"""Non-destructive OpenClaw memory consolidation planner."""
import argparse, hashlib, json, re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

STOP={"the","and","for","with","this","that","from","的","和","是","在","了","以及"}
def tokens(text): return {x.lower() for x in re.findall(r"[\w\u4e00-\u9fff]{2,}",text) if x.lower() not in STOP}
def score(p,t):
    age=max(1,(datetime.now(timezone.utc).timestamp()-p.stat().st_mtime)/86400)
    return round(min(1,0.3+min(len(t)/800,0.45)+min(0.2,30/age)),3)
def scan(root):
    rows=[]
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in {'.md','.txt','.log'}: continue
        if any(x in p.parts for x in ('backup-20260817-122921','.git','.dreams')): continue
        try: text=p.read_text(encoding='utf-8',errors='ignore')
        except OSError: continue
        digest=hashlib.sha256(text.encode()).hexdigest()
        rows.append({'path':str(p.relative_to(root)),'sha256':digest,'tokens':sorted(tokens(text)),'score':score(p,text),'bytes':len(text.encode())})
    return rows
def plan(rows):
    exact=defaultdict(list)
    for r in rows: exact[r['sha256']].append(r['path'])
    findings=[]; linked=set()
    for paths in exact.values():
        if len(paths)>1:
            canonical=sorted(paths)[0]; findings.append({'status':'DUPLICATE_CANDIDATE','kind':'exact','canonical':canonical,'related':sorted(paths)[1:]}); linked.update(paths)
    for i,a in enumerate(rows):
        if a['path'] in linked: continue
        ta=set(a['tokens'])
        for b in rows[i+1:]:
            if b['path'] in linked: continue
            tb=set(b['tokens']); union=ta|tb
            similarity=len(ta&tb)/len(union) if union else 0
            if similarity>=.82:
                canonical=min(a['path'],b['path']); related=max(a['path'],b['path'])
                findings.append({'status':'DUPLICATE_CANDIDATE','kind':'semantic','similarity':round(similarity,3),'canonical':canonical,'related':[related]}); linked.update({a['path'],b['path']})
    high=[r['path'] for r in rows if r['score']>=.72]
    return {'inputDigest':hashlib.sha256(json.dumps([(r['path'],r['sha256']) for r in rows], ensure_ascii=False).encode()).hexdigest(),'records':len(rows),'exactGroups':sum(1 for x in findings if x['kind']=='exact'),'semanticPairs':sum(1 for x in findings if x['kind']=='semantic'),'findings':findings,'highValueCandidates':high}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--apply',action='store_true'); args=ap.parse_args()
    report=plan(scan(args.root)); args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'memory-consolidation-plan.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Memory Consolidation Report','',f"Records: {report['records']}",f"Exact duplicate groups: {report['exactGroups']}",f"Semantic duplicate pairs: {report['semanticPairs']}",f"High-value candidates: {len(report['highValueCandidates'])}",'','No source memory was deleted or rewritten.']
    (args.out/'memory-consolidation-report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if args.apply:
        links={'status':'ACTIVE','mode':'non-destructive','findings':report['findings']}
        (args.out/'canonical-links.json').write_text(json.dumps(links,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'ok':True,'apply':args.apply,**{k:report[k] for k in ('records','exactGroups','semanticPairs')}}))
if __name__=='__main__': main()
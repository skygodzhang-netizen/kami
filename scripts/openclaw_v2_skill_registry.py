#!/usr/bin/env python3
import argparse,json,re
from datetime import datetime,timezone
from pathlib import Path
def skills(root):
 out=[]
 for p in root.rglob('SKILL.md'):
  text=p.read_text(encoding='utf-8',errors='ignore'); fm=text.split('---',2)[1] if text.startswith('---') and text.count('---')>=2 else ''
  name=re.search(r'^name:\s*(.+)$',fm,re.M); desc=re.search(r'^description:\s*(.+)$',fm,re.M)
  out.append({'name':name.group(1).strip() if name else p.parent.name,'path':str(p.relative_to(root.parent)),'status':'ACTIVE' if desc else 'BROKEN','usage_count':0,'success_count':0,'failure_count':0,'success_rate':None})
 return sorted(out,key=lambda x:x['name'])
def main():
 a=argparse.ArgumentParser();a.add_argument('--skills',type=Path,required=True);a.add_argument('--out',type=Path,required=True);x=a.parse_args();rows=skills(x.skills); x.out.parent.mkdir(parents=True,exist_ok=True);x.out.write_text(json.dumps({'generatedAt':datetime.now(timezone.utc).isoformat(),'skills':rows},ensure_ascii=False,indent=2));print(json.dumps({'skills':len(rows),'broken':sum(r['status']=='BROKEN' for r in rows)}))
if __name__=='__main__':main()
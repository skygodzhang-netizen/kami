import json,subprocess,tempfile
from pathlib import Path
s=Path('/home/ubuntu/.openclaw/workspace/scripts/openclaw_v2_skill_registry.py')
with tempfile.TemporaryDirectory() as d:
 r=Path(d)/'skills';(r/'good').mkdir(parents=True);(r/'bad').mkdir();(r/'good'/'SKILL.md').write_text('---\nname: good\ndescription: test\n---\n');(r/'bad'/'SKILL.md').write_text('# bad')
 o=Path(d)/'r.json'; subprocess.run(['python3',str(s),'--skills',str(r),'--out',str(o)],check=True);x=json.loads(o.read_text());assert len(x['skills'])==2 and any(y['status']=='BROKEN' for y in x['skills'])
print('skill registry fixture PASS')
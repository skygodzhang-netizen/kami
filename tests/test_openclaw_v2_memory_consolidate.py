import json, subprocess, tempfile
from pathlib import Path
script=Path('/home/ubuntu/.openclaw/workspace/scripts/openclaw_v2_memory_consolidate.py')
with tempfile.TemporaryDirectory() as d:
 r=Path(d)/'memory'; o=Path(d)/'out'; r.mkdir()
 (r/'a.md').write_text('OpenClaw gateway is healthy memory test')
 (r/'b.md').write_text('OpenClaw gateway is healthy memory test')
 (r/'c.md').write_text('OpenClaw gateway healthy test memory')
 q=subprocess.run(['python3',str(script),'--root',str(r),'--out',str(o),'--apply'],capture_output=True,text=True,check=True)
 x=json.loads(q.stdout); assert x['exactGroups']==1; assert (o/'canonical-links.json').exists(); assert (r/'a.md').exists()
print('memory consolidation fixture PASS')
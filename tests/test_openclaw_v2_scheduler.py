import json,subprocess,tempfile
from pathlib import Path
s='/home/ubuntu/.openclaw/workspace/scripts/openclaw_v2_scheduler.py'
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'c.json';o=Path(d)/'o.json';p.write_text(json.dumps({'jobs':[{'id':'a','name':'a','enabled':True,'state':{'lastStatus':'ok'}}]}));subprocess.run(['python3',s,'--cron',str(p),'--out',str(o)],check=True);assert json.loads(o.read_text())['healthy']
print('scheduler fixture PASS')
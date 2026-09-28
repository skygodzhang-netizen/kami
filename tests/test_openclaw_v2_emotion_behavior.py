import json,subprocess,tempfile
from pathlib import Path
s=Path('/home/ubuntu/.openclaw/workspace/scripts/openclaw_v2_emotion_behavior.py')
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'s.json';o=Path(d)/'o.json';p.write_text(json.dumps({'stress':80,'trust':80,'curiosity':80,'fatigue':80}))
 subprocess.run(['python3',str(s),str(p),'--out',str(o)],check=True); x=json.loads(o.read_text())['behavior'];assert x['policyCeiling']=='R3' and x['verification']=='increased' and x['proactiveWork']=='reduced'
print('emotion fixture PASS')
import json,subprocess,tempfile
from pathlib import Path
s='/home/ubuntu/.openclaw/workspace/scripts/openclaw_v2_evolution.py'
with tempfile.TemporaryDirectory() as d:
 for risk,mode in [('R0','AUTO_OBSERVE'),('R3','SANDBOX_CANARY_POLICY_GATE'),('R5','PROPOSE_ONLY')]:
  o=Path(d)/(risk+'.json');subprocess.run(['python3',s,'--risk',risk,'--action','test','--out',str(o)],check=True);x=json.loads(o.read_text());assert x['mode']==mode and not x['productionApply']
print('evolution fixture PASS')
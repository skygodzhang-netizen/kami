#!/usr/bin/env python3
import argparse,json,uuid
from datetime import datetime,timezone
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--risk',choices=['R0','R1','R2','R3','R4','R5'],required=True);p.add_argument('--action',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
mode={'R0':'AUTO_OBSERVE','R1':'AUTO_SANDBOX','R2':'SNAPSHOT_VERIFY','R3':'SANDBOX_CANARY_POLICY_GATE','R4':'PROPOSE_ONLY','R5':'PROPOSE_ONLY'}[a.risk]
apply=a.risk in ('R0','R1')
x={'id':'EV2-'+uuid.uuid4().hex[:12],'createdAt':datetime.now(timezone.utc).isoformat(),'risk':a.risk,'action':a.action,'mode':mode,'productionApply':False,'requiresSnapshot':a.risk!='R0','requiresRollback':a.risk!='R0','status':'PROPOSED' if not apply else 'SANDBOX_READY','policy':'fail-closed'}
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(x,indent=2));print(json.dumps(x))
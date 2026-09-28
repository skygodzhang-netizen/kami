#!/usr/bin/env python3
import argparse,json
from pathlib import Path
def behavior(s):
 r={'verification':'standard','lowRiskConfirmation':'standard','safeExploration':'disabled','proactiveWork':'standard','policyCeiling':'R3'}
 if s.get('stress',0)>=70: r.update(verification='increased',proactiveWork='reduced')
 if s.get('trust',0)>=70: r['lowRiskConfirmation']='reduced'
 if s.get('curiosity',0)>=70: r['safeExploration']='enabled'
 if s.get('fatigue',0)>=70: r['proactiveWork']='reduced'
 return r
p=argparse.ArgumentParser();p.add_argument('state',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
s=json.loads(a.state.read_text()); a.out.write_text(json.dumps({'state':s,'behavior':behavior(s)},ensure_ascii=False,indent=2));print('emotion behavior PASS')
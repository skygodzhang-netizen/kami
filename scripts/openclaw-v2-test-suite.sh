#!/usr/bin/env bash
set -euo pipefail
root=/home/ubuntu/.openclaw/workspace
python3 "$root/tests/test_openclaw_v2_memory_consolidate.py"
python3 "$root/tests/test_openclaw_v2_emotion_behavior.py"
python3 "$root/tests/test_openclaw_v2_evolution.py"
python3 "$root/tests/test_openclaw_v2_scheduler.py"
python3 "$root/tests/test_openclaw_v2_skill_registry.py"
systemctl is-active --quiet openclaw-gateway.service
openclaw --version
python3 - <<'PY'
import json
r=json.load(open('/home/ubuntu/.openclaw/workspace/skills/registry/registry.json'))
assert len(r['skills'])>0
assert json.load(open('/home/ubuntu/.openclaw/workspace/reports/scheduler-report.json'))['healthy']
assert json.load(open('/home/ubuntu/.openclaw/workspace/evolution/autonomous/proposer/latest-proposal.json'))['productionApply'] is False
print('V2 integration assertions PASS')
PY
python3 /home/ubuntu/.openclaw/workspace/tests/openclaw_v2_production_assertions.py

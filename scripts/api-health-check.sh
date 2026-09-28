#!/bin/bash
# Agnes API health check — Token Plan / .com route.
set -u
LOG_FILE="/home/ubuntu/.openclaw/workspace/memory/api-health-log.txt"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S UTC')
KEY_FILE="/home/ubuntu/.openclaw/secrets/provider/agnes-api-key"
BASE_URL="https://apihub.agnes-ai.com/v1"
NOTIFY=0
echo "=== API 健康检查 $TIMESTAMP ===" | tee -a "$LOG_FILE"
for model in agnes-2.0-flash agnes-2.5-flash agnes-2.5-pro-alpha; do
  result=$(AGNES_HEALTH_MODEL="$model" AGNES_HEALTH_KEY_FILE="$KEY_FILE" AGNES_HEALTH_BASE="$BASE_URL" python3 - <<'PY'
import os,time,requests
from pathlib import Path
model=os.environ["AGNES_HEALTH_MODEL"];key=Path(os.environ["AGNES_HEALTH_KEY_FILE"]).read_text().strip()
url=os.environ["AGNES_HEALTH_BASE"].rstrip("/")+"/chat/completions";started=time.monotonic()
try:
 r=requests.post(url,headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},json={"model":model,"messages":[{"role":"user","content":"ping"}],"max_tokens":3},timeout=(10,30))
 ms=round((time.monotonic()-started)*1000)
 if 200 <= r.status_code < 300: print(f"OK {ms}")
 else:
  try:
   e=r.json().get("error") or {};print(f"FAIL {ms} HTTP_{r.status_code} {e.get('type') or ''} {e.get('code') or ''}")
  except Exception: print(f"FAIL {ms} HTTP_{r.status_code}")
except Exception as exc: print(f"FAIL {round((time.monotonic()-started)*1000)} {type(exc).__name__}")
PY
)
  read -r state detail <<< "$result"
  if [ "$state" = "OK" ]; then echo "$model ✅ $detail ms" | tee -a "$LOG_FILE"
  else echo "$model ❌ $detail" | tee -a "$LOG_FILE"; NOTIFY=1; fi
done
echo "" | tee -a "$LOG_FILE"
if [ "$NOTIFY" -eq 1 ]; then echo "🔴 API 异常告警 - 请检查：" | tee -a "$LOG_FILE"; exit 1; fi

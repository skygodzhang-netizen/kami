#!/bin/bash
# Agnes API 健康检查脚本
# 直接调用 curl，不走模型，避免超时

LOG_FILE="/home/ubuntu/.openclaw/workspace/memory/api-health-log.txt"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S UTC')
NOTIFY=0

# 读取 API key
API_KEY=$(python3 -c "import json;d=json.load(open('/home/ubuntu/.openclaw/openclaw.json'));print(d['models']['providers']['agnes']['apiKey'])")

echo "=== API 健康检查 $TIMESTAMP ===" | tee -a "$LOG_FILE"

for model in agnes-2.0-flash agnes-2.5-flash agnes-2.5-pro-alpha; do
  t0=$(date +%s.%N)
  result=$(curl -s --connect-timeout 10 --max-time 30 -X POST https://apihub.agnes-ai.cn/v1/chat/completions \
    -H "Authorization: Bearer $API_KEY" \
    -H "content-type: application/json" \
    -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}],\"max_tokens\":3}" 2>&1)
  t1=$(date +%s.%N)
  ms=$(echo "$t1 - $t0" | bc | xargs printf "%.0f")
  
  if echo "$result" | grep -q '"id"'; then
    echo "$model ✅ ${ms}ms" | tee -a "$LOG_FILE"
  else
    echo "$model ❌ ${ms}ms $result" | tee -a "$LOG_FILE"
    NOTIFY=1
  fi
done

echo "" | tee -a "$LOG_FILE"

# 发送通知（如果有异常）
if [ "$NOTIFY" -eq 1 ]; then
  echo "🔴 API 异常告警 - 请检查：" | tee -a "$LOG_FILE"
  exit 1
fi

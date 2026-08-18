#!/bin/bash
# heartbeat-ha.sh — HA 巡检脚本
# 在 Heartbeat 中调用，检测 HA 状态变化并记录

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
HA_LOG="$MEM_BASE/ha-status.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S CST")

echo "[$TIMESTAMP] === HA 巡检开始 ===" >> "$HA_LOG"

# 检查 HA API 连通性
HA_URL="http://192.168.100.108:8123"
HA_TOKEN_FILE="/home/ubuntu/.openclaw/workspace/config/ha-token"

if [ ! -f "$HA_TOKEN_FILE" ]; then
    echo "[$TIMESTAMP] ❌ HA Token 未配置" >> "$HA_LOG"
    exit 1
fi

HA_TOKEN=$(cat "$HA_TOKEN_FILE" | tr -d '[:space:]')

# 测试连接
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $HA_TOKEN" \
    "$HA_URL/api/" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" != "200" ]; then
    echo "[$TIMESTAMP] ❌ HA API 连接失败 (HTTP $HTTP_CODE)" >> "$HA_LOG"
    exit 1
fi

# 获取实体数量
ENTITY_COUNT=$(curl -s -H "Authorization: Bearer $HA_TOKEN" \
    "$HA_URL/api/states" 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(len(data))
except:
    print('0')
" 2>/dev/null || echo "0")

echo "[$TIMESTAMP] ✅ HA 在线 | 实体数: $ENTITY_COUNT" >> "$HA_LOG"

# 检查关键实体状态
curl -s -H "Authorization: Bearer $HA_TOKEN" \
    "$HA_URL/api/states" 2>/dev/null | python3 -c "
import json, sys

data = json.load(sys.stdin)

# 关键实体类型
critical_types = ['person', 'motion', 'door', 'window', 'alarm', 'smoke', 'gas', 'water']

print('[$TIMESTAMP] 关键实体状态:')
for item in data:
    eid = item.get('entity_id', '')
    state = item.get('state', '')
    etype = eid.split('.')[0]
    
    if etype in critical_types:
        print(f\"  [{etype.upper()}] {eid}: {state}\")
" >> "$HA_LOG"

echo "[$TIMESTAMP] === HA 巡检完成 ===" >> "$HA_LOG"

# 输出摘要到 stdout (用于 Heartbeat 报告)
echo "HA: ✅ 在线 ($ENTITY_COUNT 实体)"

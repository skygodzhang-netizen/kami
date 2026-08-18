#!/bin/bash
# ha-integration.sh — HA 深度集成
# 状态变化检测 → Memory → 事件记录 → 通知

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
HA_LOG="$MEM_BASE/ha-state-history.jsonl"
STATE_DIR="$MEM_BASE/ha-states"
NOTIFICATION_QUEUE="$MEM_BASE/ha-notifications/queue.txt"
mkdir -p "$STATE_DIR" "$(dirname "$NOTIFICATION_QUEUE")"

LAST_STATES_FILE="/tmp/ha-last-states.json"

echo "=== HA 深度集成 ==="
echo "时间: $(date "+%Y-%m-%d %H:%M:%S CST")"
echo ""

source "$HOME/.openclaw/workspace/scripts/ha/ha-api.sh"
load_token 2>/dev/null || {
    echo "⚠️  HA Token 未配置，跳过集成"
    exit 0
}

curl -s -H "Authorization: Bearer $HA_TOKEN" \
     "$HA_URL/api/states" 2>/dev/null > "$STATE_DIR/last.json" 2>/dev/null || true

echo "🔄 检测状态变化..."
if [ -f "$LAST_STATES_FILE" ]; then
    changes=$(python3 -c "
import json, sys
from datetime import datetime

try:
    with open('$LAST_STATES_FILE') as f:
        old_states = {item['entity_id']: item['state'] for item in json.load(f)}
    with open('$STATE_DIR/last.json') as f:
        new_data = json.load(f)
    new_states = {item['entity_id']: item['state'] for item in new_data}
    
    changes = []
    for eid, new_state in new_states.items():
        old_state = old_states.get(eid)
        if old_state != new_state:
            changes.append({
                'entity_id': eid,
                'old_state': old_state,
                'new_state': new_state,
                'timestamp': datetime.now().isoformat()
            })
    
    print(json.dumps(changes))
except Exception as e:
    print('[]')
" 2>/dev/null || echo "[]")
    
    change_count=$(echo "$changes" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    
    if [ "$change_count" -gt 0 ]; then
        echo "  发现 $change_count 个状态变化"
        
        for change in $(echo "$changes" | python3 -c "import json,sys; [print(json.dumps(c)) for c in json.load(sys.stdin)]"); do
            entity=$(echo "$change" | python3 -c "import json,sys; print(json.load(sys.stdin)['entity_id'])")
            old=$(echo "$change" | python3 -c "import json,sys; print(json.load(sys.stdin)['old_state'])")
            new=$(echo "$change" | python3 -c "import json,sys; print(json.load(sys.stdin)['new_state'])")
            ts=$(echo "$change" | python3 -c "import json,sys; print(json.load(sys.stdin)['timestamp'])")
            
            importance="low"
            notification="no"
            
            case "$entity" in
                *motion*|*pir*|*door*|*window*)
                    importance="medium"
                    if [ "$new" = "on" ] || [ "$new" = "open" ]; then
                        notification="yes"
                    fi
                    ;;
                *person*|*device_tracker*)
                    importance="high"
                    notification="yes"
                    ;;
                *alarm*|*smoke*|*gas*|*water*)
                    importance="critical"
                    notification="yes"
                    ;;
            esac
            
            echo "[$ts] $entity: $old → $new (重要度: $importance)" >> "$MEM_BASE/episodes/ha-changes.log"
            
            if [ "$notification" = "yes" ]; then
                echo "[$ts] $entity: $old → $new" >> "$NOTIFICATION_QUEUE"
            fi
        done
        
        echo "$changes" >> "$HA_LOG"
        
        if [ -s "$NOTIFICATION_QUEUE" ]; then
            echo "📢 有待处理通知"
            tail -5 "$NOTIFICATION_QUEUE"
        fi
    else
        echo "  无状态变化"
    fi
else
    echo "  首次运行，记录初始状态"
fi

cp "$STATE_DIR/last.json" "$LAST_STATES_FILE" 2>/dev/null || true

echo ""
echo "✅ HA 集成检查完成"

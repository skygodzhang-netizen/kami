#!/bin/bash
# ha-api.sh — Home Assistant API 封装
# 提供安全、低频率的 HA 状态查询和控制

set -euo pipefail

HA_URL="${HA_URL:-http://192.168.100.108:8123}"
HA_TOKEN_FILE="${HA_TOKEN_FILE:-/home/ubuntu/.openclaw/workspace/config/ha-token}"
HA_TOKEN=""

# 加载 Token
load_token() {
    if [ -f "$HA_TOKEN_FILE" ]; then
        HA_TOKEN=$(cat "$HA_TOKEN_FILE" | tr -d '[:space:]')
    fi
    if [ -z "$HA_TOKEN" ]; then
        echo "❌ HA Token 未配置: $HA_TOKEN_FILE" >&2
        exit 1
    fi
}

# 安全请求 - 避免高频调用
# 限制: 同一实体最多每 30 秒查询一次
declare -A LAST_QUERY
RATE_LIMIT=30

safe_query() {
    local entity_id="$1"
    local now=$(date +%s)
    local last="${LAST_QUERY[$entity_id]:-0}"
    
    if [ $((now - last)) -lt $RATE_LIMIT ]; then
        echo "⏱️  实体 $entity_id 查询过于频繁，跳过" >&2
        return 1
    fi
    LAST_QUERY[$entity_id]=$now
}

# 获取实体状态
get_state() {
    local entity_id="$1"
    safe_query "$entity_id" || return 0
    
    curl -s -H "Authorization: Bearer $HA_TOKEN" \
         "$HA_URL/api/states/$entity_id" 2>/dev/null | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(f\"{d.get('state', 'unknown')}\")
except:
    print('error')
" 2>/dev/null || echo "error"
}

# 获取多个实体状态
get_states() {
    local entities="$1"  # 逗号分隔的实体 ID
    
    curl -s -H "Authorization: Bearer $HA_TOKEN" \
         "$HA_URL/api/states" 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    entity_list = sys.argv[1].split(',') if sys.argv[1] else []
    for item in data:
        eid = item.get('entity_id', '')
        if not entity_list or eid in entity_list:
            print(f\"{eid}: {item.get('state', 'unknown')}\")
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
" "$entities" 2>/dev/null
}

# 控制设备 (低风险)
# 安全级别: low=直接执行, high=需要确认
call_service() {
    local service="$1"      # 如 light.turn_on
    local entity_id="$2"    # 如 light.living_room
    local params="${3:-{}}"
    local safety_level="${4:-low}"  # low 或 high
    
    case "$safety_level" in
        high)
            echo "⚠️  高风险操作: $service $entity_id" >&2
            echo "请确认是否执行 (yes/no): " >&2
            read -r confirm 2>/dev/null || confirm="no"
            if [ "$confirm" != "yes" ]; then
                echo "❌ 操作已取消"
                return 1
            fi
            ;;
        low)
            # 低风险直接执行
            ;;
    esac
    
    curl -s -X POST \
         -H "Authorization: Bearer $HA_TOKEN" \
         -H "Content-Type: application/json" \
         -d "{\"entity_id\": \"$entity_id\", $params}" \
         "$HA_URL/services/$service" 2>/dev/null
}

# 获取环境快照
snapshot() {
    load_token
    
    echo "=== HA 环境快照 ==="
    echo "时间: $(date "+%Y-%m-%d %H:%M:%S CST")"
    echo ""
    
    # 获取所有实体
    curl -s -H "Authorization: Bearer $HA_TOKEN" \
         "$HA_URL/api/states" 2>/dev/null | python3 -c "
import json, sys
from datetime import datetime

data = json.load(sys.stdin)
snapshots = {
    'temperature': [],
    'humidity': [],
    'light': [],
    'switch': [],
    'motion': [],
    'door_window': [],
    'person': [],
    'binary_sensor': [],
    'climate': []
}

for item in data:
    eid = item.get('entity_id', '')
    state = item.get('state', '')
    attrs = item.get('attributes', {})
    
    if 'temperature' in eid or 'temp' in eid:
        snapshots['temperature'].append(f'{eid}: {state}')
    elif 'humidity' in eid:
        snapshots['humidity'].append(f'{eid}: {state}')
    elif eid.startswith('light.'):
        snapshots['light'].append(f'{eid}: {state}')
    elif eid.startswith('switch.'):
        snapshots['switch'].append(f'{eid}: {state}')
    elif 'motion' in eid or 'pir' in eid:
        snapshots['motion'].append(f'{eid}: {state}')
    elif 'door' in eid or 'window' in eid or 'contact' in eid:
        snapshots['door_window'].append(f'{eid}: {state}')
    elif eid.startswith('person.'):
        snapshots['person'].append(f'{eid}: {state}')
    elif eid.startswith('binary_sensor.'):
        snapshots['binary_sensor'].append(f'{eid}: {state}')
    elif eid.startswith('climate.'):
        snapshots['climate'].append(f'{eid}: {state} (setpoint: {attrs.get('temperature', 'N/A')})')

# 输出
for cat, items in snapshots.items():
    if items:
        print(f'[{cat.upper()}]')
        for item in items[:10]:  # 限制输出数量
            print(f'  {item}')
        print()
" 2>/dev/null
}

# 命令分发
case "${1:-help}" in
    state)
        load_token
        get_state "${2:-}"
        ;;
    states)
        load_token
        get_states "${2:-}"
        ;;
    snapshot)
        snapshot
        ;;
    service)
        load_token
        call_service "${2:-}" "${3:-}" "${4:-{}}" "${5:-low}"
        ;;
    *)
        echo "用法: $0 {state|states|snapshot|service}"
        echo "  state <entity_id>        - 获取单个实体状态"
        echo "  states <entity1,entity2> - 获取多个实体状态"
        echo "  snapshot                 - 获取环境快照"
        echo "  service <svc> <entity> [params] [safety]"
        echo "    safety: low (默认) 或 high (需确认)"
        ;;
esac

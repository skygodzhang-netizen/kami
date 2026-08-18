#!/bin/bash
# ha-query.sh — 自然语言查询 HA 状态

set -euo pipefail

source "$HOME/.openclaw/workspace/scripts/ha/ha-api.sh"
load_token

QUERY="${1:-}"

if [ -z "$QUERY" ]; then
    echo "用法: $0 '<查询内容>'"
    echo "示例:"
    echo "  $0 '客厅灯开着吗'"
    echo "  $0 '家里有人吗'"
    echo "  $0 '温度多少'"
    exit 0
fi

echo "=== 查询 HA 状态 ==="
echo "查询: $QUERY"
echo "时间: $(date "+%Y-%m-%d %H:%M:%S CST")"
echo ""

curl -s -H "Authorization: Bearer $HA_TOKEN" \
     "$HA_URL/api/states" 2>/dev/null | python3 -c "
import json, sys

data = json.load(sys.stdin)
query = '''$QUERY'''

entity_map = {
    '灯': 'light',
    '开关': 'switch',
    '温度': 'temperature',
    '湿度': 'humidity',
    '人体': 'motion',
    '人': 'person',
    '门': 'door',
    '窗': 'window',
    '传感器': 'sensor',
    '空调': 'climate',
}

results = []
query_lower = query.lower()

for item in data:
    eid = item.get('entity_id', '')
    state = item.get('state', '')
    name = item.get('attributes', {}).get('friendly_name', eid)
    
    matched = False
    for cn, en in entity_map.items():
        if en in eid and cn in query_lower:
            matched = True
            break
        if en in query_lower and cn in eid:
            matched = True
            break
    
    if not matched:
        if query_lower in eid.lower() or query_lower in name.lower():
            matched = True
    
    if matched:
        results.append(f'{name} ({eid}): {state}')

if results:
    print('找到结果:')
    for r in results[:20]:
        print(f'  📍 {r}')
else:
    print('未找到匹配的实体')
    print('')
    print('可用实体类型:')
    types = set()
    for item in data:
        eid = item.get('entity_id', '')
        etype = eid.split('.')[0] if '.' in eid else eid
        types.add(etype)
    for t in sorted(types):
        print(f'  - {t}')
"

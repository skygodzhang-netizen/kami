#!/bin/bash
# ha-control.sh — 自然语言控制 HA 设备

set -euo pipefail

source "$HOME/.openclaw/workspace/scripts/ha/ha-api.sh"
load_token

ACTION="${1:-}"
TARGET="${2:-}"
PARAMS="${3:-}"

if [ -z "$ACTION" ] || [ -z "$TARGET" ]; then
    echo "用法: $0 '<动作>' '<目标>' [参数]"
    echo "示例:"
    echo "  $0 '打开' '客厅灯'"
    echo "  $0 '关闭' '空调'"
    echo "  $0 '设置温度' '空调' '26度'"
    echo "  $0 '查看' '所有灯'"
    exit 0
fi

echo "=== HA 设备控制 ==="
echo "动作: $ACTION"
echo "目标: $TARGET"
echo "参数: ${PARAMS:-无}"
echo "时间: $(date "+%Y-%m-%d %H:%M:%S CST")"
echo ""

curl -s -H "Authorization: Bearer $HA_TOKEN" \
     "$HA_URL/api/states" 2>/dev/null | python3 -c "
import json, sys

data = json.load(sys.stdin)
target = '''$TARGET'''
action = '''$ACTION'''
params = '''$PARAMS'''

matches = []
for item in data:
    eid = item.get('entity_id', '')
    name = item.get('attributes', {}).get('friendly_name', eid)
    
    if target in eid or target in name:
        matches.append({
            'entity_id': eid,
            'name': name,
            'state': item.get('state', ''),
            'type': eid.split('.')[0]
        })

if not matches:
    print('未找到匹配的设备')
    sys.exit(1)

print('找到设备:')
for m in matches:
    print(f\"  - {m['name']} ({m['entity_id']}): {m['state']}\")

print('')
print('建议操作:')
for m in matches:
    etype = m['type']
    eid = m['entity_id']
    
    if action in ['打开', '开', 'on']:
        if etype in ['light', 'switch']:
            print(f\"  ✅ 执行: light.turn_on -> {eid}\")
        else:
            print(f\"  ⚠️  未知类型 {etype}\")
    elif action in ['关闭', '关', 'off']:
        if etype in ['light', 'switch']:
            print(f\"  ✅ 执行: light.turn_off -> {eid}\")
        else:
            print(f\"  ⚠️  未知类型 {etype}\")
    elif action in ['设置温度', '调温度']:
        if etype == 'climate':
            temp = params.replace('度', '').replace('℃', '').strip()
            if temp.isdigit():
                print(f\"  ✅ 执行: climate.set_temperature -> {eid}, temperature={temp}\")
            else:
                print(f\"  ⚠️  无效温度: {temp}\")
        else:
            print(f\"  ⚠️  {etype} 不支持温度设置\")
    elif action in ['查看', '状态']:
        print(f\"  📍 {m['name']}: {m['state']}\")
    else:
        print(f\"  ❓ 未知动作: {action}\")
"

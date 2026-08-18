#!/bin/bash
# ha-loop-prevention.sh — 防循环机制
# 防止 HA 状态变化 → Memory → Agent → HA 的无限循环

set -euo pipefail

STATE_FILE="/tmp/ha-last-trigger.txt"
COOLDOWN=300  # 5 分钟冷却期

# 检查是否在冷却期
if [ -f "$STATE_FILE" ]; then
    last_trigger=$(cat "$STATE_FILE")
    now=$(date +%s)
    elapsed=$((now - last_trigger))
    
    if [ $elapsed -lt $COOLDOWN ]; then
        remaining=$((COOLDOWN - elapsed))
        echo "⏱️  HA 操作冷却中，剩余 ${remaining} 秒"
        exit 0
    fi
fi

# 标记本次操作
date +%s > "$STATE_FILE"
echo "✅ 操作已记录，冷却期 $COOLDOWN 秒"

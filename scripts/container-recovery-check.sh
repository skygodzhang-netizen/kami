#!/bin/bash
# container-recovery-check.sh
# Phase 3.2 Docker 自动恢复策略判断模块
# 当前: observe模式，只判断，不执行

set -euo pipefail

CONFIG="/home/ubuntu/.openclaw/workspace/config/auto-restart-whitelist.json"

CONTAINER="$1"

if [ ! -f "$CONFIG" ]; then
    echo "❌ 自动恢复配置不存在"
    exit 1
fi

GLOBAL_ENABLED=$(jq -r '.enabled' "$CONFIG")
MODE=$(jq -r '.mode' "$CONFIG")

MATCH=$(jq -r --arg name "$CONTAINER" \
'.containers[] | select(.name==$name) | .enabled' \
"$CONFIG")

echo "=== Auto Recovery Check ==="

if [ "$MATCH" = "true" ]; then
    echo "白名单: ✅ $CONTAINER"
else
    echo "白名单: ❌ $CONTAINER"
    echo "动作: 仅通知"
    exit 0
fi

echo "全局开关: $GLOBAL_ENABLED"
echo "当前模式: $MODE"

if [ "$MODE" = "observe" ]; then
    echo "动作:"
    echo "🟡 建议恢复: docker restart $CONTAINER"
    echo "⛔ observe模式，不执行"
fi

if [ "$GLOBAL_ENABLED" = "true" ] && [ "$MODE" = "active" ]; then
    echo "动作:"
    echo "🟢 后续允许执行恢复"
fi

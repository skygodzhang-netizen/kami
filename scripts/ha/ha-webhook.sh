#!/bin/bash
# ha-webhook.sh — HA Webhook 处理

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
WEBHOOK_LOG="$MEM_BASE/ha-webhooks.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S CST")

EVENT_TYPE="${1:-unknown}"
ENTITY_ID="${2:-}"
OLD_STATE="${3:-}"
NEW_STATE="${4:-}"

echo "[$TIMESTAMP] Webhook: $EVENT_TYPE | $ENTITY_ID | $OLD_STATE → $NEW_STATE" >> "$WEBHOOK_LOG"

case "$EVENT_TYPE" in
    state_changed)
        echo "## $TIMESTAMP — HA 状态变化" >> "$MEM_BASE/episodes/ha-changes.log"
        echo "- $ENTITY_ID: $OLD_STATE → $NEW_STATE" >> "$MEM_BASE/episodes/ha-changes.log"
        
        if echo "$ENTITY_ID" | grep -qiE "motion|door|window|alarm|smoke"; then
            if [ "$NEW_STATE" = "on" ] || [ "$NEW_STATE" = "open" ] || [ "$NEW_STATE" = "triggered" ]; then
                echo "🔔 HA 事件: $ENTITY_ID 状态变化 -> $NEW_STATE"
            fi
        fi
        ;;
    automation_triggered)
        echo "🤖 HA 自动化触发: $ENTITY_ID"
        ;;
    *)
        echo "📥 未知事件: $EVENT_TYPE"
        ;;
esac

echo "Webhook processed"

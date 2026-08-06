#!/bin/bash
# container-health-check.sh — Docker 容器异常检测（观察模式）
# 检测容器状态，记录异常，Telegram 通知
# 暂不自动恢复，仅观察

set -euo pipefail

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S CST")
LOG_DIR="/home/ubuntu/.openclaw/workspace/memory"
mkdir -p "$LOG_DIR"

WHITELIST_CONFIG="/home/ubuntu/.openclaw/workspace/config/auto-restart-whitelist.json"

check_restart_policy() {
    local container="$1"

    if [ ! -f "$WHITELIST_CONFIG" ]; then
        echo "      自动恢复配置不存在"
        return
    fi

    MATCH=$(jq -r --arg name "$container" \
    '.containers[] | select(.name==$name) | .enabled' \
    "$WHITELIST_CONFIG" 2>/dev/null || echo "false")

    MODE=$(jq -r '.mode' "$WHITELIST_CONFIG" 2>/dev/null || echo "unknown")

    if [ "$MATCH" = "true" ]; then
        echo "      自动恢复白名单: 是"
        echo "      当前模式: $MODE"

        if [ "$MODE" = "observe" ]; then
            echo "      🟡 建议恢复: docker restart $container"
            echo "      ⛔ 观察模式，不执行恢复"
        fi

    else
        echo "      自动恢复白名单: 否"
        echo "      动作: 仅通知"
    fi
}

ANOMALIES=0
TOTAL_CONTAINERS=0

echo "=========================================="
echo "  Docker 容器健康检查 — $TIMESTAMP"
echo "=========================================="

# Ubuntu AI Server 容器检查
echo ""
echo "=== Ubuntu AI Server ==="
while IFS=$'\t' read -r name image status ports; do
    [ -z "$name" ] && continue
    TOTAL_CONTAINERS=$((TOTAL_CONTAINERS + 1))
    
    # 检查异常状态
    if echo "$status" | grep -qiE "unhealthy|dead|exited|restarting|removing"; then
        ANOMALIES=$((ANOMALIES + 1))
        echo "  🔴 异常: $name"
        echo "      镜像: $image"
        echo "      状态: $status"
        echo "      端口: $ports"

        check_restart_policy "$name"

        # 记录到日志
        echo "[$TIMESTAMP] 异常容器: $name ($status) - 镜像: $image" >> "$LOG_DIR/container-health-log.txt"
    elif echo "$status" | grep -qiE "up"; then
        echo "  🟢 正常: $name — $status"
    else
        echo "  🟡 未知: $name — $status"
    fi
done < <(docker ps -a --format "{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null)

# iStoreOS 容器检查
echo ""
echo "=== iStoreOS Router ==="
ISTOREOS_STATUS=$(ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@192.168.100.1 \
    "docker ps -a --format '{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null" 2>/dev/null || echo "")

if [ -n "$ISTOREOS_STATUS" ]; then
    while IFS=$'\t' read -r name image status ports; do
        [ -z "$name" ] && continue
        TOTAL_CONTAINERS=$((TOTAL_CONTAINERS + 1))
        
        if echo "$status" | grep -qiE "unhealthy|dead|exited|restarting|removing"; then
            ANOMALIES=$((ANOMALIES + 1))
            echo "  🔴 异常: $name"
            echo "      镜像: $image"
            echo "      状态: $status"
            echo "      端口: $ports"
            
            echo "[$TIMESTAMP] iStoreOS 异常容器: $name ($status)" >> "$LOG_DIR/container-health-log.txt"
        elif echo "$status" | grep -qiE "up"; then
            echo "  🟢 正常: $name — $status"
        else
            echo "  🟡 未知: $name — $status"
        fi
    done <<< "$ISTOREOS_STATUS"
else
    echo "  [SSH 连接失败或无 Docker]"
fi

# Home Assistant 应用层健康检测（Phase 3.2-A）
echo ""
echo "=== Application Health Check ==="

if docker ps --format '{{.Names}}' | grep -q "^homeassistant$"; then
    HA_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://127.0.0.1:8123 || echo "000")

    if [ "$HA_STATUS" = "000" ]; then
        echo "  🔴 homeassistant Web 服务异常: HTTP $HA_STATUS"
        echo "[$TIMESTAMP] homeassistant 应用层异常: HTTP $HA_STATUS" >> "$LOG_DIR/container-health-log.txt"
        ANOMALIES=$((ANOMALIES + 1))
    else
        echo "  🟢 homeassistant Web 服务正常: HTTP $HA_STATUS"
    fi
else
    echo "  🟡 未发现 homeassistant 容器"
fi

# 总结
echo ""
echo "=========================================="
echo "  检查结果: 共 $TOTAL_CONTAINERS 个容器, $ANOMALIES 个异常"
if [ "$ANOMALIES" -gt 0 ]; then
    echo "  ⚠️  发现 $ANOMALIES 个异常容器，需要关注"
else
    echo "  ✅ 所有容器运行正常"
fi
echo "=========================================="

# 返回退出码
if [ "$ANOMALIES" -gt 0 ]; then
    exit 1
fi
exit 0

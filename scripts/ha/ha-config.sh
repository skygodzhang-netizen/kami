#!/bin/bash
# ha-config.sh — Home Assistant 配置向导
# 引导用户配置 Token

set -euo pipefail

CONFIG_DIR="/home/ubuntu/.openclaw/workspace/config"
TOKEN_FILE="$CONFIG_DIR/ha-token"
BACKUP_DIR="/home/ubuntu/.openclaw/workspace/memory/backup"

mkdir -p "$CONFIG_DIR" "$BACKUP_DIR"

echo "=== Home Assistant 配置向导 ==="
echo ""

# 检查是否已有 Token
if [ -f "$TOKEN_FILE" ]; then
    echo "⚠️  已存在 Token 配置"
    echo "  文件: $TOKEN_FILE"
    echo ""
    echo "选项:"
    echo "  1. 使用现有 Token"
    echo "  2. 更新 Token"
    echo "  3. 删除并重新配置"
    echo ""
    read -p "请选择 (1-3): " choice 2>/dev/null || choice="1"
else
    choice="3"
fi

case "$choice" in
    1)
        echo "✅ 使用现有 Token"
        ;;
    2|3)
        if [ -f "$TOKEN_FILE" ]; then
            cp "$TOKEN_FILE" "$BACKUP_DIR/ha-token-$(date +%Y%m%d-%H%M%S).bak"
            echo "💾 已备份旧 Token"
        fi
        
        echo ""
        echo "请在 Home Assistant 中生成 Long-Lived Access Token:"
        echo "  1. 打开 HA 界面 → 用户资料 → 生成长效访问令牌"
        echo "  2. 复制生成的 Token"
        echo "  3. 粘贴到下方 (回车确认)"
        echo ""
        
        echo -n "Token: "
        read -r token 2>/dev/null || token=***
        
        if [ -z "$token" ]; then
            echo "❌ Token 不能为空"
            exit 1
        fi
        
        echo "$token" > "$TOKEN_FILE"
        chmod 600 "$TOKEN_FILE"
        echo "✅ Token 已保存"
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

# 测试连接
echo ""
echo "🔍 测试连接..."
TOKEN=$(cat "$TOKEN_FILE" | tr -d '[:space:]')
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    "http://192.168.100.108:8123/api/" 2>/dev/null || echo "000")

if [ "$RESPONSE" = "200" ]; then
    echo "✅ 连接成功! HA 可用"
    ENTITY_COUNT=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "http://192.168.100.108:8123/api/" 2>/dev/null | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(len(d.get('states', [])))
except:
    print('0')
" 2>/dev/null || echo "0")
    echo "   检测到 $ENTITY_COUNT 个实体"
else
    echo "⚠️  连接失败 (HTTP $RESPONSE)"
fi

echo ""
echo "✅ 配置完成! 测试命令:"
echo "  bash scripts/ha/ha-query.sh '所有传感器'"
echo "  bash scripts/ha/ha-control.sh '查看' '所有灯'"

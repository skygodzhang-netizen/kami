#!/bin/bash
# camera-vision.sh — Camera Vision 分析
# 拍摄快照 → 可选 Vision 分析 → 记录到 Memory

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
CAMERA_DIR="$MEM_BASE/camera"
VISION_DIR="$MEM_BASE/vision"
HA_TOKEN_FILE="/home/ubuntu/.openclaw/workspace/config/ha-token"

mkdir -p "$CAMERA_DIR" "$VISION_DIR"

HA_URL="http://192.168.100.108:8123"

# 加载 Token
if [ -f "$HA_TOKEN_FILE" ]; then
    HA_TOKEN=$(tr -d '[:space:]' < "$HA_TOKEN_FILE")
else
    echo "❌ HA Token 未配置" >&2
    exit 1
fi

# 命令分发
case "${1:-list}" in
    list)
        echo "=== 已配置的摄像头 ==="
        FOUND=0
        for f in "$CAMERA_DIR"/*.json; do
            [ -f "$f" ] || continue
            FOUND=1
            python3 -c "
import json
with open('$f') as fh:
    d = json.load(fh)
    print(f\"  - {d.get('name', 'unknown')}\")
    print(f\"    IP: {d.get('ip', 'N/A')}\")
    print(f\"    状态: {d.get('status', 'unknown')}\")
    print(f\"    快照: {d.get('snapshot_url', 'N/A')}\")
    print()
"
        done
        
        if [ "$FOUND" -eq 0 ]; then
            echo "  暂无摄像头配置"
            echo ""
            echo "添加摄像头:"
            echo "  bash scripts/ha/ha-camera-integration.sh <IP> <名称>"
        fi
        ;;
    
    snapshot)
        CAMERA_NAME="${2:-}"
        if [ -z "$CAMERA_NAME" ]; then
            echo "用法: $0 snapshot '<摄像头名称>'"
            exit 1
        fi
        
        echo "📸 拍摄快照: $CAMERA_NAME"
        
        # 获取快照 URL
        CAMERA_FILE="$CAMERA_DIR/${CAMERA_NAME}.json"
        if [ ! -f "$CAMERA_FILE" ]; then
            echo "❌ 未找到摄像头配置: $CAMERA_FILE"
            exit 1
        fi
        
        SNAPSHOT_URL=$(python3 -c "import json; print(json.load(open('$CAMERA_FILE')).get('snapshot_url', ''))" 2>/dev/null)
        
        if [ -z "$SNAPSHOT_URL" ]; then
            echo "❌ 未找到快照 URL"
            exit 1
        fi
        
        TIMESTAMP=$(date +%Y%m%d-%H%M%S)
        OUTPUT_FILE="$CAMERA_DIR/${CAMERA_NAME}-${TIMESTAMP}.jpg"
        
        # 尝试获取快照
        curl -s -L -o "$OUTPUT_FILE" "$SNAPSHOT_URL" 2>/dev/null
        
        # 检查是否是有效图片
        if [ -f "$OUTPUT_FILE" ] && file "$OUTPUT_FILE" | grep -q "JPEG"; then
            echo "✅ 快照已保存: $OUTPUT_FILE"
            echo "   大小: $(wc -c < "$OUTPUT_FILE") bytes"
        else
            echo "⚠️  快照获取失败 (可能需要认证)"
            echo "   原始 URL: $SNAPSHOT_URL"
            echo "   返回内容:"
            head -c 100 "$OUTPUT_FILE" 2>/dev/null || echo "  (空)"
            echo ""
            
            # 尝试 RTSP 流
            echo "   尝试 RTSP 流..."
            RTSP_URL=$(python3 -c "import json; print(json.load(open('$CAMERA_FILE')).get('rtsp_url', ''))" 2>/dev/null)
            if [ -n "$RTSP_URL" ]; then
                echo "   RTSP: $RTSP_URL"
                echo "   使用 ffmpeg 拍摄:"
                echo "   ffmpeg -i '$RTSP_URL' -frames:v 1 -q:v 2 $OUTPUT_FILE"
            fi
        fi
        ;;
    
    analyze)
        CAMERA_NAME="${2:-}"
        if [ -z "$CAMERA_NAME" ]; then
            echo "用法: $0 analyze '<摄像头名称>'"
            exit 1
        fi
        
        echo "👁️  Vision 分析: $CAMERA_NAME"
        
        # 获取最新快照
        LATEST=$(ls -t "$CAMERA_DIR/${CAMERA_NAME}-"*.jpg 2>/dev/null | head -1)
        
        if [ -z "$LATEST" ]; then
            echo "⚠️  没有找到快照，先拍摄..."
            bash "$0" snapshot "$CAMERA_NAME"
            LATEST=$(ls -t "$CAMERA_DIR/${CAMERA_NAME}-"*.jpg 2>/dev/null | head -1)
        fi
        
        if [ -n "$LATEST" ] && [ -f "$LATEST" ] && file "$LATEST" | grep -q "JPEG"; then
            echo "📷 分析图片: $LATEST"
            echo "⏳ Vision 分析需要配置图像识别模型"
        else
            echo "❌ 没有可用的图片"
        fi
        ;;
    
    *)
        echo "用法: $0 {list|snapshot|analyze}"
        echo ""
        echo "命令:"
        echo "  list                    - 列出所有摄像头"
        echo "  snapshot <名称>         - 拍摄快照"
        echo "  analyze <名称>          - 分析图片 (Vision 预留)"
        ;;
esac

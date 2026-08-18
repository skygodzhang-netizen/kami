#!/bin/bash
# u64g-camera.sh — u64G 摄像头控制脚本
# 支持快照拍摄、RTSP 流、对讲功能、录制

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
CAMERA_DIR="$MEM_BASE/camera"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S CST")

CAMERA_IP="192.168.100.152"
CAMERA_NAME="客厅"
CAMERA_FILE="$CAMERA_DIR/${CAMERA_NAME}.json"

ACTION="${1:-list}"

case "$ACTION" in
    status)
        echo "=== 摄像头状态 ==="
        if [ -f "$CAMERA_FILE" ]; then
            python3 -c "
import json
with open('$CAMERA_FILE') as f:
    d = json.load(f)
    print(f\"名称: {d.get('name', 'unknown')}\")
    print(f\"IP: {d.get('ip', 'N/A')}\")
    print(f\"型号: {d.get('model', 'N/A')}\")
    print(f\"状态: {d.get('status', 'unknown')}\")
    print(f\"设备 ID: {d.get('device_id', 'N/A')}\")
    print(f\"功能: {', '.join(d.get('features', []))}\")
"
        else
            echo "❌ 摄像头未配置"
        fi
        ;;
    
    snapshot)
        echo "📸 拍摄快照: $CAMERA_NAME"
        
        OUTPUT_FILE="$CAMERA_DIR/${CAMERA_NAME}-$(date +%Y%m%d-%H%M%S).jpg"
        
        # 尝试获取快照
        for path in "/cgi-bin/snapshot.cgi" "/cgi-bin/snapshot.cgi?channel=0&subtype=0"; do
            echo -n "  尝试 $path: "
            curl -s -L -o "$OUTPUT_FILE" "http://$CAMERA_IP$path" 2>/dev/null
            
            if [ -f "$OUTPUT_FILE" ] && file "$OUTPUT_FILE" | grep -q "JPEG"; then
                echo "✅"
                echo "   已保存: $OUTPUT_FILE"
                echo "   大小: $(wc -c < "$OUTPUT_FILE") bytes"
                exit 0
            else
                echo "❌ (需要认证)"
            fi
        done
        ;;
    
    talk)
        echo "🎤 启动对讲: $CAMERA_NAME"
        
        # 启动摄像头对讲
        echo "启动摄像头扬声器..."
        curl -s -X POST "http://$CAMERA_IP/cgi-bin/speaker.cgi?action=start" 2>/dev/null && \
            echo "✅ 扬声器已启动" || echo "⚠️ 扬声器启动失败"
        
        # 检查麦克风
        if command -v arecord >/dev/null 2>&1; then
            MIC_DEVICES=$(arecord -l 2>/dev/null | grep -c "card" || echo "0")
            if [ "$MIC_DEVICES" -gt 0 ]; then
                echo "✅ 麦克风已检测到"
                echo "🎤 请说话..."
                echo "   (录制中... 按 Ctrl+C 停止)"
                
                RECORD_FILE="/tmp/u64g_talk_$(date +%s).wav"
                arecord -f S16_LE -r 8000 -c 1 "$RECORD_FILE" 2>/dev/null &
                RECORD_PID=$!
                
                # 等待用户输入
                read -p "按 Enter 停止录制..." 2>/dev/null || true
                kill $RECORD_PID 2>/dev/null || true
                
                echo "✅ 录制完成: $RECORD_FILE"
                echo ""
                echo "下一步:"
                echo "  发送音频到摄像头: curl -X POST -d @$RECORD_FILE http://$CAMERA_IP/cgi-bin/audio.cgi"
            else
                echo "⚠️  未检测到麦克风"
                echo "   请连接麦克风后重试"
            fi
        else
            echo "⚠️  arecord 不可用"
            echo "   请安装 alsa-utils: sudo apt install alsa-utils"
        fi
        
        # 停止摄像头扬声器
        echo "停止扬声器..."
        curl -s -X POST "http://$CAMERA_IP/cgi-bin/speaker.cgi?action=stop" 2>/dev/null && \
            echo "✅ 扬声器已关闭" || echo "⚠️ 扬声器关闭失败"
        ;;
    
    speaker-test)
        echo "🔊 测试扬声器..."
        
        # 启动扬声器
        curl -s -X POST "http://$CAMERA_IP/cgi-bin/speaker.cgi?action=start" 2>/dev/null && \
            echo "✅ 扬声器已启动" || echo "❌ 扬声器启动失败"
        
        sleep 3
        
        # 停止扬声器
        curl -s -X POST "http://$CAMERA_IP/cgi-bin/speaker.cgi?action=stop" 2>/dev/null && \
            echo "✅ 扬声器已关闭" || echo "⚠️ 扬声器关闭失败"
        ;;
    
    record)
        echo "📹 录制控制: $CAMERA_NAME"
        
        case "${2:-list}" in
            list)
                echo "获取录制列表..."
                curl -s "http://$CAMERA_IP/cgi-bin/record.cgi?action=list" 2>/dev/null
                ;;
            start)
                echo "开始录制..."
                curl -s -X POST "http://$CAMERA_IP/cgi-bin/record.cgi?action=start" 2>/dev/null && \
                    echo "✅ 录制已启动" || echo "❌ 录制启动失败"
                ;;
            stop)
                echo "停止录制..."
                curl -s -X POST "http://$CAMERA_IP/cgi-bin/record.cgi?action=stop" 2>/dev/null && \
                    echo "✅ 录制已停止" || echo "❌ 录制停止失败"
                ;;
            *)
                echo "用法: $0 record {list|start|stop}"
                ;;
        esac
        ;;
    
    list)
        echo "=== 已配置的摄像头 ==="
        for f in "$CAMERA_DIR"/*.json; do
            [ -f "$f" ] || continue
            python3 -c "
import json
with open('$f') as fh:
    d = json.load(fh)
    print(f\"  - {d.get('name', 'unknown')}\")
    print(f\"    IP: {d.get('ip', 'N/A')}\")
    print(f\"    状态: {d.get('status', 'unknown')}\")
    print(f\"    型号: {d.get('model', 'N/A')}\")
    print(f\"    功能: {', '.join(d.get('features', []))}\")
    print()
"
        done
        
        if [ ! "$(ls -A "$CAMERA_DIR"/*.json 2>/dev/null)" ]; then
            echo "  暂无摄像头配置"
        fi
        ;;
    
    *)
        echo "用法: $0 {status|snapshot|talk|speaker-test|record|list}"
        echo ""
        echo "命令:"
        echo "  status              - 查看摄像头状态"
        echo "  snapshot            - 拍摄快照"
        echo "  talk                - 启动对讲 (需要麦克风)"
        echo "  speaker-test        - 测试扬声器"
        echo "  record {list|start|stop} - 录制控制"
        echo "  list                - 列出所有摄像头"
        ;;
esac

#!/bin/bash
# memory-dedup.sh — 记忆去重与冲突检测

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"

echo "=== 记忆去重与冲突检测 ==="
echo "时间: $(date "+%Y-%m-%d %H:%M:%S CST")"
echo ""

# 1. 重复检测 (基于内容相似度)
echo "🔍 检查重复..."
declare -A content_hashes

duplicate_count=0
find "$MEM_BASE" -name "*.md" -type f | grep -v backup | while read -r file; do
    # 提取内容哈希 (前100字符)
    hash=$(head -c 100 "$file" | md5sum | cut -d' ' -f1)
    
    if [ -n "${content_hashes[$hash]:-}" ]; then
        echo "  ⚠️  可能重复: $file"
        echo "      与: ${content_hashes[$hash]}"
        duplicate_count=$((duplicate_count + 1))
    else
        content_hashes[$hash]="$file"
    fi
done

echo ""
echo "🔍 检查状态冲突..."

# 2. 冲突检测 (服务状态)
services=("openclaw-gateway" "caddy" "docker" "homeassistant" "openclash")
for svc in "${services[@]}"; do
    current_state=$(systemctl is-active "$svc" 2>/dev/null || echo "unknown")
    
    # 检查记忆中的状态
    memory_state=$(grep -r "$svc" "$MEM_BASE" --include="*.md" 2>/dev/null | grep -oE "(active|inactive|running|stopped|enabled|disabled)" | tail -1 || echo "unknown")
    
    if [ "$current_state" != "$memory_state" ] && [ "$memory_state" != "unknown" ]; then
        echo "  🔴 冲突: $svc 当前状态=$current_state, 记忆状态=$memory_state"
    fi
done

echo ""
echo "✅ 检测完成"
echo "  重复项: $duplicate_count"

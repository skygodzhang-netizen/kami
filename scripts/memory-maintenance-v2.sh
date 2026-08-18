#!/bin/bash
# memory-maintenance-v2.sh — 记忆维护系统
# 功能: 过期清理、状态更新、统计报告

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S CST")
DAYS_TO_KEEP="${1:-90}"

echo "=== 记忆维护 ==="
echo "时间: $TIMESTAMP"
echo "保留天数: $DAYS_TO_KEEP"
echo ""

# 统计信息
total_files=$(find "$MEM_BASE" -name "*.md" -type f | grep -v backup | wc -l)
total_size=$(du -sh "$MEM_BASE" 2>/dev/null | cut -f1)

echo "📊 当前状态:"
echo "  - 记忆文件: $total_files"
echo "  - 总大小: $total_size"
echo ""

# 检查过期记忆
echo "🗓️  过期检查:"
expired_count=0
stale_count=0

find "$MEM_BASE/episodes" -name "*.md" -type f 2>/dev/null | while read -r file; do
    filename=$(basename "$file" .md)
    # 检查是否是日期格式
    if [[ "$filename" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        file_date=$(echo "$filename" | cut -d'-' -f1-3)
        file_epoch=$(date -d "$file_date" +%s 2>/dev/null || echo 0)
        now_epoch=$(date +%s)
        age_days=$(( (now_epoch - file_epoch) / 86400 ))
        
        if [ $age_days -gt $DAYS_TO_KEEP ]; then
            echo "  ⏰ $filename: $age_days 天前 (可归档)"
            expired_count=$((expired_count + 1))
        fi
        
        # 检查是否过期 (超过60天且无更新)
        if [ $age_days -gt 60 ]; then
            stale_count=$((stale_count + 1))
        fi
    fi
done

echo ""

# 检查置信度低的记忆
echo "⚠️  低置信度记忆:"
low_conf_count=0
find "$MEM_BASE" -name "*.md" -type f | grep -v backup | while read -r file; do
    if grep -qi "confidence: *low" "$file" 2>/dev/null; then
        echo "  🟡 $(basename "$file" .md)"
        low_conf_count=$((low_conf_count + 1))
    fi
done

echo ""

# 生成报告
echo "📈 维护报告:"
echo "  - 总文件数: $total_files"
echo "  - 过期 (>${DAYS_TO_KEEP}天): $expired_count"
echo "  - 陈旧 (>60天): $stale_count"
echo "  - 低置信度: $low_conf_count"
echo ""

echo "💡 建议:"
if [ $expired_count -gt 0 ]; then
    echo "  - 考虑归档 $expired_count 个过期记忆"
fi
if [ $low_conf_count -gt 0 ]; then
    echo "  - 验证 $low_conf_count 个低置信度记忆"
fi
if [ $expired_count -eq 0 ] && [ $low_conf_count -eq 0 ]; then
    echo "  - 记忆库状态良好"
fi

echo ""
echo "✅ 维护完成"

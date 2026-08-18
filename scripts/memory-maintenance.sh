#!/bin/bash
# memory-maintenance.sh — 记忆维护系统
# 功能: 过期清理、去重、冲突解决、统计报告

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S CST")
DAYS_TO_KEEP="${1:-90}"  # 默认保留90天

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

# 检查过期记忆 (临时 episode)
echo "🗓️  过期检查:"
expired_count=0
find "$MEM_BASE/episodes" -name "*.md" -type f 2>/dev/null | while read -r file; do
    file_date=$(basename "$file" .md)
    if [[ "$file_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        file_epoch=$(date -d "$file_date" +%s 2>/dev/null || echo 0)
        now_epoch=$(date +%s)
        age_days=$(( (now_epoch - file_epoch) / 86400 ))
        
        if [ $age_days -gt $DAYS_TO_KEEP ]; then
            echo "  ⏰ $file: $age_days 天前 (可归档)"
            expired_count=$((expired_count + 1))
        fi
    fi
done

echo ""
echo "✅ 维护完成"

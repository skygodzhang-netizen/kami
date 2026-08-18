#!/bin/bash
# memory-index.sh — 记忆检索索引构建器
# 构建全文索引，加速检索

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
INDEX_FILE="$MEM_BASE/.index"
TEMP_INDEX=$(mktemp)

echo "=== 构建记忆索引 ==="
echo "时间: $(date "+%Y-%m-%d %H:%M:%S CST")"
echo ""

# 清理旧索引
> "$TEMP_INDEX"

# 索引所有记忆文件
find "$MEM_BASE" -name "*.md" -type f | grep -v "backup" | while read -r file; do
    # 提取元数据
    memory_type=$(echo "$file" | sed "s|$MEM_BASE/||" | cut -d/ -f1)
    filename=$(basename "$file" .md)
    
    # 提取内容前200字符作为索引
    content=$(head -c 200 "$file" 2>/dev/null | tr '\n' ' ' | tr -s ' ' | head -c 100)
    
    # 写入索引
    echo "${memory_type}|${filename}|${content}" >> "$TEMP_INDEX"
done

# 替换索引文件
mv "$TEMP_INDEX" "$INDEX_FILE"
chmod 644 "$INDEX_FILE"

echo "✅ 索引已更新"
echo "  索引文件: $INDEX_FILE"
echo "  条目数: $(wc -l < "$INDEX_FILE")"

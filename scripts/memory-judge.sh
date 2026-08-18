#!/bin/bash
# memory-judge.sh — 记忆质量评估与冲突检测
# 输入: 新记忆内容
# 输出: 质量评分、冲突警告、建议

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S CST")

# 颜色输出
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "=== 记忆评估器 ==="
echo "时间: $TIMESTAMP"
echo ""

# 参数
MEMORY_TYPE="${1:-semantic}"  # semantic, episode, procedural, preference, environment
MEMORY_CONTENT="${2:-}"
MEMORY_ID="${3:-}"

# 质量评分
score=100
warnings=()

# 1. 检查重复 (简单关键词匹配)
check_duplication() {
    local keywords=$(echo "$MEMORY_CONTENT" | grep -oE '[a-zA-Z0-9]{4,}' | head -10)
    local duplicates=0
    
    for keyword in $keywords; do
        if grep -r "$keyword" "$MEM_BASE" --include="*.md" 2>/dev/null | grep -v "backup" | grep -q .; then
            duplicates=$((duplicates + 1))
        fi
    done
    
    if [ $duplicates -gt 3 ]; then
        echo -e "${YELLOW}⚠️  可能重复: 发现 $duplicates 个相似关键词${NC}"
        score=$((score - 20))
    fi
}

# 2. 检查时间戳格式
check_timestamp() {
    if echo "$MEMORY_CONTENT" | grep -qE '[0-9]{4}-[0-9]{2}-[0-9]{2}'; then
        : # 格式正确
    else
        echo -e "${YELLOW}⚠️  建议添加时间戳${NC}"
        score=$((score - 10))
    fi
}

# 3. 检查来源标记
check_source() {
    if echo "$MEMORY_CONTENT" | grep -qiE 'source:|from:|来自:'; then
        : # 有来源标记
    else
        echo -e "${YELLOW}⚠️  建议添加来源标记${NC}"
        score=$((score - 5))
    fi
}

# 4. 检查置信度标记
check_confidence() {
    if echo "$MEMORY_CONTENT" | grep -qiE 'confidence:|置信度:|确认:|疑似:|可能:'; then
        : # 有置信度标记
    else
        echo -e "${YELLOW}⚠️  建议添加置信度标记${NC}"
        score=$((score - 5))
    fi
}

# 5. 检查冲突 (简单的关键词冲突)
check_conflict() {
    local conflict_keywords=("enabled" "disabled" "running" "stopped" "active" "inactive")
    local conflicts=0
    
    for kw in "${conflict_keywords[@]}"; do
        if echo "$MEMORY_CONTENT" | grep -qi "$kw"; then
            # 检查是否有相反状态的记录
            if grep -r "$kw" "$MEM_BASE" --include="*.md" 2>/dev/null | grep -v "backup" | grep -qi "$(echo $kw | sed 's/^/not/')"; then
                conflicts=$((conflicts + 1))
            fi
        fi
    done
    
    if [ $conflicts -gt 0 ]; then
        echo -e "${RED}🔴 潜在冲突: 发现 $conflicts 个状态冲突${NC}"
        score=$((score - 30))
    fi
}

# 执行检查
check_duplication
check_timestamp
check_source
check_confidence
check_conflict

# 输出评分
echo ""
echo "=== 评估结果 ==="
if [ $score -ge 80 ]; then
    echo -e "${GREEN}✅ 质量评分: $score/100 (优秀)${NC}"
elif [ $score -ge 60 ]; then
    echo -e "${YELLOW}🟡 质量评分: $score/100 (良好)${NC}"
else
    echo -e "${RED}🔴 质量评分: $score/100 (需改进)${NC}"
fi

echo ""
echo "建议: $([ $score -ge 80 ] && echo '可直接存储' || echo '建议完善后存储')"

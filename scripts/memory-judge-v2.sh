#!/bin/bash
# memory-judge-v2.sh — Memory Intelligence Layer
# 决策：新信息是否值得长期记忆？

set -euo pipefail

MEM_BASE="$HOME/.openclaw/workspace/memory"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S CST")

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Memory Judge ===${NC}"
echo "时间: $TIMESTAMP"
echo ""

# 参数
INPUT="${1:-}"
TYPE="${2:-auto}"  # auto, semantic, episode, procedural, preference, environment
SOURCE="${3:-manual}"

if [ -z "$INPUT" ]; then
    echo "用法: $0 '<内容>' [类型] [来源]"
    echo ""
    echo "示例:"
    echo "  $0 '用户偏好台湾节点'"
    echo "  $0 'Gateway 重启后恢复正常' episode"
    echo "  $0 '用户喜欢简洁回答' preference"
    exit 1
fi

# 1. 判断记忆类型
if [ "$TYPE" = "auto" ]; then
    # 自动判断类型
    if echo "$INPUT" | grep -qiE "喜欢|偏好|倾向|风格|回答"; then
        TYPE="preference"
    elif echo "$INPUT" | grep -qiE "命令|操作|修复|重启|配置|脚本"; then
        TYPE="procedural"
    elif echo "$INPUT" | grep -qiE "服务器|VPS|路由器|OpenClaw|Docker|HA|Home Assistant"; then
        TYPE="semantic"
    elif echo "$INPUT" | grep -qiE "故障|异常|问题|错误|崩溃|重启"; then
        TYPE="environment"
    else
        TYPE="episode"
    fi
fi

echo -e "${GREEN}📋 输入分析${NC}"
echo "  类型: $TYPE"
echo "  来源: $SOURCE"
echo ""

# 2. 去重检测
echo -e "${GREEN}🔍 去重检测${NC}"
dup_score=0
keywords=$(echo "$INPUT" | grep -oE '[a-zA-Z0-9]{3,}' | head -5)
for kw in $keywords; do
    matches=$(grep -r "$kw" "$MEM_BASE" --include="*.md" 2>/dev/null | grep -v backup | wc -l)
    if [ "$matches" -gt 2 ]; then
        dup_score=$((dup_score + 10))
    fi
done

if [ "$dup_score" -gt 20 ]; then
    echo -e "  ${YELLOW}⚠️  高度重复: 可能需要更新而非新增${NC}"
else
    echo -e "  ✅ 独特性良好"
fi
echo ""

# 3. 价值评估
echo -e "${GREEN}💎 价值评估${NC}"
value_score=50

# 检查是否包含操作价值
if echo "$INPUT" | grep -qiE "修复|解决|方案|命令|配置|步骤"; then
    value_score=$((value_score + 20))
    echo "  ✅ 包含操作价值"
fi

# 检查是否包含偏好信息
if echo "$INPUT" | grep -qiE "用户|喜欢|偏好|倾向|习惯"; then
    value_score=$((value_score + 15))
    echo "  ✅ 包含用户偏好"
fi

# 检查是否包含故障信息
if echo "$INPUT" | grep -qiE "故障|异常|错误|崩溃|修复"; then
    value_score=$((value_score + 15))
    echo "  ✅ 包含故障经验"
fi

# 检查是否包含时间敏感信息
if echo "$INPUT" | grep -qiE "[0-9]{4}-[0-9]{2}-[0-9]{2}|今天|昨天|刚刚"; then
    value_score=$((value_score - 10))
    echo "  ⚠️  包含时间敏感信息 (可能临时)"
fi

echo ""

# 4. 置信度评估
echo -e "${GREEN}📊 置信度评估${NC}"
confidence="high"

if echo "$INPUT" | grep -qiE "可能|疑似|大概|也许|猜测"; then
    confidence="medium"
    echo "  🟡 包含不确定性词汇"
fi

if echo "$INPUT" | grep -qiE "确认|确定|已知|明确"; then
    confidence="high"
    echo "  🟢 包含确认性词汇"
fi

if echo "$INPUT" | grep -qiE "错误|失败|异常|问题"; then
    confidence="medium"
    echo "  🟡 涉及问题描述"
fi

echo ""

# 5. 存储决策
echo -e "${GREEN}🎯 存储决策${NC}"
echo "  建议存储类型: $TYPE"
echo "  置信度: $confidence"
echo "  价值评分: $value_score"
echo ""

if [ "$value_score" -ge 40 ]; then
    echo -e "  ${GREEN}✅ 建议存储为长期记忆${NC}"
else
    echo -e "  ${YELLOW}⚠️  建议仅记录为 Episode${NC}"
fi

echo ""
echo -e "${BLUE}=== 输出模板 ===${NC}"
cat << EOF
# 记忆记录

## 元数据
- **类型**: $TYPE
- **来源**: $SOURCE
- **置信度**: $confidence
- **创建时间**: $TIMESTAMP
- **最后更新**: $TIMESTAMP
- **价值评分**: $value_score/100

## 内容
$INPUT
EOF

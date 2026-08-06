#!/bin/bash
# security-mail-check.sh — 安全邮件监控脚本
# 扫描 Gmail 中指定发件人的安全/异常邮件，按风险等级分类
# 用法: bash /home/ubuntu/.openclaw/workspace/scripts/security-mail-check.sh [--notify|--digest]

set -euo pipefail

RULES_FILE="/home/ubuntu/.openclaw/workspace/config/security-rules.json"
LOG_DIR="/home/ubuntu/.openclaw/workspace/memory"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S CST")
MODE="${1:-full}"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# 风险等级关键词提取（从 JSON 读取）
extract_keywords() {
    local level=$1
    python3 -c "
import json
with open('$RULES_FILE') as f:
    rules = json.load(f)['rules']['$level']
    for k in rules.get('keywords_en', []) + rules.get('keywords_zh', []):
        print(k)
" 2>/dev/null
}

# 检查邮件并分类
check_email() {
    local from_filter=$1
    local severity=$2
    local subject=$3
    local sender=$4
    local date=$5

    case "$severity" in
        critical)
            LEVEL="🔴 高危"
            NOTIFY="IMMEDIATE"
            ;;
        warning)
            LEVEL="🟡 警告"
            NOTIFY="DIGEST"
            ;;
        info)
            LEVEL="🟢 普通"
            NOTIFY="LOG_ONLY"
            ;;
    esac

    echo "[$LEVEL] [$NOTIFY]"
    echo "  发件人: $sender"
    echo "  主题: $subject"
    echo "  日期: $date"
    echo ""
}

# 主扫描函数
scan_for_provider() {
    local provider=$1
    local email="skygod.zhang@gmail.com"

    # 对每个风险等级搜索
    for level in critical warning info; do
        local keywords
        keywords=$(extract_keywords "$level")

        if [ -z "$keywords" ]; then
            continue
        fi

        # 构建搜索查询（OR 连接关键词）
        local search_query=""
        while IFS= read -r kw; do
            [ -z "$kw" ] && continue
            if [ -z "$search_query" ]; then
                search_query="\"$kw\""
            else
                search_query="$search_query OR \"$kw\""
            fi
        done <<< "$keywords"

        [ -z "$search_query" ] && continue

        # 执行搜索（限制最新 5 条）
        local results
        results=$(gog gmail search -a "$email" "from:$provider $search_query" --limit 5 2>/dev/null || true)

        if [ -n "$results" ]; then
            echo "=== Provider: $provider (Level: $level) ==="
            echo "$results" | while IFS= read -r line; do
                [ -z "$line" ] && continue
                # 解析 gog 输出，提取关键信息
                echo "  $line"
            done
            echo ""
        fi
    done
}

# 输出摘要
output_summary() {
    local critical_count=$1
    local warning_count=$2
    local info_count=$3

    echo "=========================================="
    echo "  安全邮件扫描摘要 — $TIMESTAMP"
    echo "=========================================="
    echo "🔴 高危: $critical_count 封"
    echo "🟡 警告: $warning_count 封"
    echo "🟢 普通: $info_count 封"
    echo "=========================================="

    if [ "$critical_count" -gt 0 ]; then
        echo "⚠️  发现高危安全邮件，需要立即关注！"
    fi
}

# 主逻辑
echo "[$TIMESTAMP] 开始安全邮件扫描..."
echo ""

CRITICAL_TOTAL=0
WARNING_TOTAL=0
INFO_TOTAL=0

PROVIDERS=("google" "bybit" "paypal" "github" "cloudflare" "cloudcone" "openai" "anthropic")

for provider in "${PROVIDERS[@]}"; do
    scan_for_provider "$provider"
done

echo "扫描完成。"

# 日志记录
echo "[$TIMESTAMP] 安全邮件扫描完成" >> "$LOG_DIR/security-mail-log.txt"

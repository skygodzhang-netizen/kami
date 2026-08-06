#!/bin/bash

BASE=/home/ubuntu/.openclaw/workspace

REPORT=$BASE/memory/ai-analysis/latest-report.json
TREND=$BASE/memory/ai-analysis/trends/disk-trend.json

OUTDIR=$BASE/memory/ai-analysis/summary
OUT=$OUTDIR/latest-summary.md


TIME=$(date "+%Y-%m-%d %H:%M:%S")


DISK=$(jq -r '.metrics.ubuntu_disk' $REPORT)
OVERLAY=$(jq -r '.metrics.istoreos_overlay' $REPORT)
TEMP=$(jq -r '.metrics.temperature' $REPORT)
OPENCLASH=$(jq -r '.metrics.openclash' $REPORT)

RISK=$(jq -r '.risk' $REPORT)

GROWTH=$(jq -r '.growth_per_day' $TREND)


cat > $OUT <<EOF
# AI运维分析报告

时间：
$TIME


## 系统状态

风险等级：

$RISK


## Ubuntu

磁盘使用率：

${DISK}%


## iStoreOS

Overlay：

${OVERLAY}%

温度：

${TEMP}℃


OpenClash：

$OPENCLASH


## 趋势分析

磁盘每日增长：

${GROWTH}


## AI建议

EOF


if [ "$RISK" = "low" ]; then

cat >> $OUT <<EOF
当前系统运行稳定。

暂无需要处理的问题。

继续保持监控即可。
EOF

else

cat >> $OUT <<EOF
检测到潜在风险。

建议人工检查相关服务。

不会自动修改系统。
EOF

fi


echo "AI summary generated"

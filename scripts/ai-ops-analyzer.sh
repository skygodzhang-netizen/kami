#!/bin/bash

BASE=/home/ubuntu/.openclaw/workspace
DATA=$BASE/metrics/history/daily.jsonl
OUT=$BASE/memory/ai-analysis/latest-report.json


if [ ! -f "$DATA" ]; then
    echo "no metrics data"
    exit 1
fi


LAST=$(tail -n 7 "$DATA")


DISK=$(echo "$LAST" | tail -1 | jq -r '.ubuntu_disk')
OVERLAY=$(echo "$LAST" | tail -1 | jq -r '.istoreos_overlay')
MEM=$(echo "$LAST" | tail -1 | jq -r '.istoreos_memory')
TEMP=$(echo "$LAST" | tail -1 | jq -r '.temperature')
OPENCLASH=$(echo "$LAST" | tail -1 | jq -r '.openclash')


RISK=0
REASON=""


if [ "$DISK" -ge 70 ]; then
    RISK=$((RISK+2))
    REASON="${REASON}Ubuntu磁盘使用率较高;"
fi


if [ "$OVERLAY" -ge 70 ]; then
    RISK=$((RISK+2))
    REASON="${REASON}iStoreOS overlay空间较高;"
fi


if [ "$MEM" -ge 80 ]; then
    RISK=$((RISK+1))
    REASON="${REASON}内存使用率较高;"
fi


if [ "$TEMP" -ge 70 ]; then
    RISK=$((RISK+2))
    REASON="${REASON}温度较高;"
fi


if [ "$OPENCLASH" = "stopped" ]; then
    RISK=$((RISK+3))
    REASON="${REASON}OpenClash异常;"
fi


if [ "$RISK" -ge 4 ]; then
    LEVEL="high"
elif [ "$RISK" -ge 2 ]; then
    LEVEL="medium"
else
    LEVEL="low"
fi


REPORT_TIME=$(date '+%Y-%m-%d %H:%M:%S')
REPORT_DATE=$(date '+%Y-%m-%d')

cat > "$OUT" <<EOF
{
  "time":"$REPORT_TIME",
  "risk":"$LEVEL",
  "score":"$RISK",
  "reason":"$REASON",
  "metrics":{
    "ubuntu_disk":"$DISK",
    "istoreos_overlay":"$OVERLAY",
    "memory":"$MEM",
    "temperature":"$TEMP",
    "openclash":"$OPENCLASH"
  }
}
EOF


cp "$OUT" "$BASE/memory/ai-analysis/history/$REPORT_DATE.json"

echo "AI analysis complete"

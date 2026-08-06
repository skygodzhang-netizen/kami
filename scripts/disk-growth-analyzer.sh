#!/bin/bash

BASE=/home/ubuntu/.openclaw/workspace

DATA=$BASE/metrics/history/daily.jsonl
OUT=$BASE/memory/ai-analysis/trends/disk-trend.json


if [ ! -f "$DATA" ]; then
    echo "No history data"
    exit 1
fi


COUNT=$(wc -l < "$DATA")


if [ "$COUNT" -lt 2 ]; then

cat > "$OUT" <<EOF
{
  "status":"insufficient_data",
  "message":"需要更多历史数据进行趋势预测",
  "samples":"$COUNT",
  "risk":"unknown"
}
EOF

exit 0

fi


FIRST=$(head -n 1 "$DATA" | jq -r '.ubuntu_disk')
LAST=$(tail -n 1 "$DATA" | jq -r '.ubuntu_disk')


DAYS=$((COUNT-1))

GROWTH=$((LAST-FIRST))


if [ "$DAYS" -gt 0 ]; then
    DAILY=$(awk "BEGIN {printf \"%.2f\", $GROWTH/$DAYS}")
else
    DAILY=0
fi


if awk "BEGIN {exit !($DAILY > 0)}"; then
    FORECAST=$(awk "BEGIN {printf \"%.0f\", (85-$LAST)/$DAILY}")
else
    FORECAST="unknown"
fi


if [ "$LAST" -ge 85 ]; then
    RISK="critical"
elif [ "$LAST" -ge 70 ]; then
    RISK="medium"
else
    RISK="low"
fi


cat > "$OUT" <<EOF
{
  "status":"ok",
  "samples":"$COUNT",
  "current_disk":"$LAST%",
  "growth_total":"$GROWTH%",
  "growth_per_day":"$DAILY%",
  "forecast_to_85_percent":"$FORECAST days",
  "risk":"$RISK"
}
EOF

#!/bin/bash
# Phase 3.3.2 网络质量评分分析

set -euo pipefail

BASE="/home/ubuntu/.openclaw/workspace"
NETWORK_DIR="$BASE/metrics/network"

INPUT=$(ls -t "$NETWORK_DIR"/network-health-*.json 2>/dev/null | head -1)

OUTPUT="$NETWORK_DIR/network-score.json"

if [ -z "$INPUT" ]; then
    echo "没有网络数据"
    exit 1
fi


echo "=========================================="
echo " 网络质量评分分析"
echo " 数据: $INPUT"
echo "=========================================="


jq '
map(
{
 name:.name,
 host:.host,
 type:.type,

 status:.status,

 latency:
 (
  if (.latency|tonumber?) then
    (.latency|tonumber)
  else
    999
  end
 ),

 loss:
 (
  if (.loss|tonumber?) then
    (.loss|tonumber)
  else
    100
  end
 )
}
)
|
map(
 . +
 {
 score:
 (
   (
    (if .status=="online" then 40 else 0 end)
    +
    (if .latency < 1 then 30
     elif .latency < 200 then 25
     elif .latency < 500 then 15
     else 5 end)
    +
    (if .loss == 0 then 20 else 10 end)
    +
    10
   )
 )
}
)
|
sort_by(-.score)
' "$INPUT" > "$OUTPUT"


cat "$OUTPUT"

echo ""
echo "输出:"
echo "$OUTPUT"

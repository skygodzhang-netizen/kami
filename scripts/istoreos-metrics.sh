#!/bin/bash

BASE=/home/ubuntu/.openclaw/workspace/metrics
DATE=$(date +"%Y-%m-%dT%H:%M:%S")

HOST="192.168.100.1"


TEMP=$(ssh root@$HOST "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null" | awk '{print $1/1000}')

LOAD=$(ssh root@$HOST "cat /proc/loadavg | awk '{print \$1}'")

MEM=$(ssh root@$HOST "free | awk '/Mem/{printf \"%.0f\", \$3/\$2*100}'")

OVERLAY=$(ssh root@$HOST "df /overlay | awk 'NR==2 {print \$5}' | sed 's/%//'")

OPENCLASH=$(ssh root@$HOST "pgrep -f '/etc/openclash/clash' >/dev/null && echo running || echo stopped")

WAN=$(ssh root@$HOST "ip link | grep -E 'pppoe|eth' | grep UP >/dev/null && echo up || echo unknown")

TAILSCALE=$(ssh root@$HOST "tailscale status >/dev/null 2>&1 && echo running || echo stopped")


cat > $BASE/system/istoreos.json <<EOF
{
  "timestamp":"$DATE",
  "host":"istoreos",
  "temperature":"$TEMP",
  "load":"$LOAD",
  "memory_percent":"$MEM",
  "overlay_percent":"$OVERLAY",
  "openclash":"$OPENCLASH",
  "wan":"$WAN",
  "tailscale":"$TAILSCALE"
}
EOF

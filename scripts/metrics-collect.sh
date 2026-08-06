#!/bin/bash

BASE=/home/ubuntu/.openclaw/workspace/metrics
DATE=$(date +"%Y-%m-%dT%H:%M:%S")


MEM=$(free | awk '/Mem/{printf "%.0f", $3/$2*100}')
DISK=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
LOAD=$(uptime | awk -F'load average:' '{print $2}')
UPTIME=$(uptime -p)


DOCKER=$(docker ps --format "{{.Names}}" | tr '\n' ',')

if systemctl is-active --quiet openclaw-gateway; then
    GATEWAY="running"
else
    GATEWAY="stopped"
fi


if docker ps --format "{{.Names}}" | grep -q homeassistant; then
    HA="running"
else
    HA="stopped"
fi


cat > $BASE/system/ubuntu.json <<EOF
{
  "timestamp":"$DATE",
  "host":"ubuntu-ai",
  "uptime":"$UPTIME",
  "memory_percent":"$MEM",
  "disk_percent":"$DISK",
  "load":"$LOAD",
  "docker":"$DOCKER",
  "openclaw_gateway":"$GATEWAY",
  "homeassistant":"$HA"
}
EOF

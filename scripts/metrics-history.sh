#!/bin/bash

BASE=/home/ubuntu/.openclaw/workspace
DATE=$(date +"%Y-%m-%d %H:%M:%S")

UBUNTU=$BASE/metrics/system/ubuntu.json
ISTOREOS=$BASE/metrics/system/istoreos.json
OUT=$BASE/metrics/history/daily.jsonl


UBUNTU_DISK=$(jq -r '.disk_percent' $UBUNTU)
UBUNTU_MEMORY=$(jq -r '.memory_percent' $UBUNTU)

ISTOREOS_OVERLAY=$(jq -r '.overlay_percent' $ISTOREOS)
ISTOREOS_MEMORY=$(jq -r '.memory_percent' $ISTOREOS)

TEMPERATURE=$(jq -r '.temperature' $ISTOREOS)

OPENCLASH=$(jq -r '.openclash' $ISTOREOS)


cat >> $OUT <<EOF
{"time":"$DATE","ubuntu_disk":"$UBUNTU_DISK","ubuntu_memory":"$UBUNTU_MEMORY","istoreos_overlay":"$ISTOREOS_OVERLAY","istoreos_memory":"$ISTOREOS_MEMORY","temperature":"$TEMPERATURE","openclash":"$OPENCLASH"}
EOF

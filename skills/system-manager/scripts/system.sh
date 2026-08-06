#!/bin/bash

echo "===== Ubuntu AI Server ====="

echo "主机:"
hostname

echo
echo "CPU负载:"
uptime

echo
echo "内存:"
free -h

echo
echo "磁盘:"
df -h /

echo
echo "Docker:"
docker ps --format "table {{.Names}}\t{{.Status}}"

echo
echo "OpenClaw:"
systemctl is-active openclaw-gateway

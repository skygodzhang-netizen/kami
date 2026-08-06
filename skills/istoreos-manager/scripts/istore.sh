#!/bin/bash

echo "===== iStoreOS ====="

ssh root@192.168.100.1 "
echo 'CPU:'
uptime

echo
echo 'Memory:'
free -h

echo
echo 'Disk:'
df -h

echo
echo 'Docker:'
docker ps --format 'table {{.Names}}\t{{.Status}}'

echo
echo 'OpenClash:'
/etc/init.d/openclash status
"

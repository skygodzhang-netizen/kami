---
name: system-manager
description: Monitor Ubuntu AI Server, Home Assistant, Docker and iStoreOS router. Use this skill whenever the user asks for overall system status, health, CPU, memory, disk or service status.
---

# System Manager

Use this skill whenever the user asks:

- 查看系统状态
- 查看服务器状态
- 查看软路由状态
- 查看整体状态
- 查看资源占用
- 查看运行情况

## Ubuntu AI Server

Collect:

```bash
hostname
uptime
free -h
df -h
docker ps
systemctl status openclaw-gateway --no-pager
```

## Home Assistant

```bash
docker ps | grep homeassistant
```

## iStoreOS

Use SSH:

```bash
ssh root@192.168.100.1 "uptime"
ssh root@192.168.100.1 "free -h"
ssh root@192.168.100.1 "df -h"
ssh root@192.168.100.1 "docker ps"
ssh root@192.168.100.1 "/etc/init.d/openclash status"
```

Always summarize into one report.

---
name: ubuntu-manager
description: 管理 Ubuntu AI Server。用于查看系统状态、Docker、Home Assistant、OpenClaw Gateway、日志、磁盘和服务。
---

# Ubuntu AI Server 管理

当用户询问：

- 查看 Ubuntu 状态
- 查看 AI Server
- 查看服务器
- 查看 Docker
- 查看 Home Assistant
- 查看 Gateway
- 查看日志
- 更新系统

优先执行：

## 系统状态

```bash
hostname
uptime
free -h
df -h
```

## Docker

```bash
docker ps
docker stats --no-stream
```

## Home Assistant

```bash
docker ps | grep homeassistant
docker logs --tail 50 homeassistant
```

## OpenClaw Gateway

```bash
systemctl status openclaw-gateway --no-pager
```

## 最近日志

```bash
journalctl -u openclaw-gateway -n 50 --no-pager
```

输出时整理为：

- CPU
- 内存
- 磁盘
- Docker
- Home Assistant
- Gateway
- 异常

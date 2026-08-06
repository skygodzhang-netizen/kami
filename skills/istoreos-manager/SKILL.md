---
name: istoreos-manager
description: 通过 SSH 管理 iStoreOS 路由器，包括 OpenClash、Docker、系统状态、日志和网络。
---

# iStoreOS Router

所有命令通过：

```bash
ssh root@192.168.100.1
```

执行。

## 查看系统

```bash
ssh root@192.168.100.1 "uptime"
ssh root@192.168.100.1 "free"
ssh root@192.168.100.1 "df -h"
```

## Docker

```bash
ssh root@192.168.100.1 "docker ps"
```

## OpenClash

```bash
ssh root@192.168.100.1 "/etc/init.d/openclash status"
```

## 重启 OpenClash

```bash
ssh root@192.168.100.1 "/etc/init.d/openclash restart"
```

## 查看日志

```bash
ssh root@192.168.100.1 "logread | tail -100"
```

输出时整理为：

- CPU
- 内存
- 磁盘
- Docker
- OpenClash
- WAN
- LAN

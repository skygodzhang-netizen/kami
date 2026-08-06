# Infrastructure

更新时间：
2026-07-20


# Ubuntu AI Server

IP:
192.168.100.108

用途:
AI自动化服务器

系统:
Ubuntu 24.04

服务:

- OpenClaw Gateway
- Home Assistant
- Docker


端口:

OpenClaw Gateway:
18789


Docker:

当前主要容器:
- homeassistant


注意:

- Docker异常先检测，不自动删除
- 系统更新需确认


---


# iStoreOS

用途:
家庭网络核心软路由


服务:

- OpenClash
- Tailscale


网络:

LAN:
192.168.100.1


磁盘:

系统盘:
overlay

规则:
超过80%只通知
禁止自动清理


数据盘:

sdb4
sda1

规则:
超过85%提供清理建议
删除需要确认


特殊说明:

443端口:
由uhttpd占用

属于正常状态

不要检测443冲突


Tailscale:

用途:
远程组网

不要启用serve转发


---


# VPS

用途:

公网服务


服务:

- OpenClaw
- Docker


规则:

保持VPS作为公网能力节点

不要迁移软路由专用功能

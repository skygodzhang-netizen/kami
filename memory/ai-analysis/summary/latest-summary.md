# AI运维分析报告

时间：
2026-08-22 12:00 UTC

## 系统状态

风险等级：
high

## Ubuntu

磁盘：17%
内存：1.5G/3.8G
负载：0.24
运行时间：1天22小时

## iStoreOS

Overlay：72%
OpenClash：运行中

## Docker

homeassistant：运行中（47小时）

## 异常事件

OpenClaw Gateway 服务未运行
- 进程检查：未找到
- 健康检查：无法连接（000）

## 网络状态

Google DNS：196ms
Cloudflare DNS：216ms
OpenAI API：1.5s
Agnes API：2.0s

## AI建议

1. 检查 OpenClaw Gateway 服务状态
2. 重启服务或排查启动失败原因

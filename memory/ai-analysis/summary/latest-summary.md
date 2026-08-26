# AI运维分析报告

时间：
2026-08-26 12:00:08


## 系统状态

风险等级：

medium


## Ubuntu

磁盘使用率：

17%

内存使用：

1.1G/3.8G

CPU负载：

0.14

OpenClaw Gateway：

active


## iStoreOS

Overlay：

73%

温度：

47℃


OpenClash：

running


## Docker

homeassistant：

Up 5 days


## 网络质量

Cloudflare DNS：

193ms 在线

Google DNS：

223ms 丢包严重

OpenAI API：

2.8s 在线

Agnes API：

1.9s 在线


## 趋势分析

磁盘每日增长：

0.01%


## AI建议

Google DNS丢包严重，建议更换为Cloudflare DNS。

OpenClaw Gateway健康检查待排查（历史遗留问题）。

整体系统稳定。

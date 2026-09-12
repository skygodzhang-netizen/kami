# 日报 2026-09-12

## 健康总览
- Ubuntu AI Server: ⚠️ 内存紧张（编译进程导致）
- iStoreOS 路由器: 🟢 正常
- SSL 证书: 🟢 全部正常（最短 340 天）
- 安全邮件: 🟢 今日 13:04/13:07 扫描完成，无高危

## Ubuntu AI Server (192.168.100.108)
```
[负载] load 5.70/4.14/2.49（运行11天）
[内存] 总3.8G，可用仅137MB，swap已用1009MB
[磁盘] / : 17% (16G/98G, 可用78G)
[Docker] homeassistant: Up 11 days
[服务] openclaw-gateway: active
[占用Top] cc1 编译进程 ×4（约3.2G）+ node + dockerd
```
⚠️ 内存紧张原因：多个 cc1 编译进程在跑（RSS 各 400-900MB），非常态异常。建议关注编译是否结束，结束后内存应恢复。

## iStoreOS 路由器 (192.168.100.1)
```
[负载] load 3.31/2.86/2.29
[系统盘 overlay/sdb3] 73% (1.4G/1.9G, 可用525M) ← 监控中，未达80%阈值
[数据盘 sdb4] 8% (1.9G/26.5G, 可用23.2G)
[数据盘 sda1] 26% (27G/109.5G, 可用76.9G)
[OpenClash] running (mihomo PID 15171 + openclash_watch)
[Tailscale] 未安装（无 serve 配置）
```
- overlay 73% 接近 80% 告警线，需持续关注。

## SSL 证书
- gateway 证书: 340 天，正常
- 其余 8 张: 全部正常（最短 76 天 rubygem，非关键）

## 磁盘趋势
- 已采集并更新 config/disk-trend.json
- 各分区均在阈值内

## 待处理事项
1. ⚠️ iStoreOS overlay 分区 73%，接近 80% 告警线，持续监控
2. Ubuntu 服务器编译进程占用内存高，编译结束后复查内存恢复情况

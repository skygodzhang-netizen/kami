# 📊 每日巡检报告 — 2026-09-11

## Ubuntu AI Server (192.168.100.108)
- [系统] up 10d | 负载 0.01-0.95（正常）
- [磁盘] / : 17% (98G, 可用 78G)
- [内存] ~1.3-1.6Gi / 3.8Gi
- [Docker] homeassistant: Up 10 days
- [服务] Gateway: running

## iStoreOS 路由器 (192.168.100.1)
- [系统] up 10d | 负载 1.17-1.75（正常）
- [磁盘] overlay /dev/sdb3: 73% (1.9G, 可用 525.4M) ← 只监控
- [服务] OpenClash: running | Tailscale: running
- [Tailscale serve] 配置存在于 _serve/e416（仅记录）

## SSL 证书
- 🟢 gateway.pem/crt: 剩余 341 天
- 共 9 个证书全部正常

## 安全邮件扫描
- 无高危事件

## 磁盘趋势
- 已采集，/ 分区 17% 稳定

## 异常与处理
- 无

## 巡检记录
- 本日（CST 09-11）共 40 次巡检条目，全部正常
- 07:02 路由器负载偏高观察项 30 分钟后回落，已关闭

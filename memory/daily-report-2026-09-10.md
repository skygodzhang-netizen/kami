# 📊 每日巡检报告 — 2026-09-10

## Ubuntu AI Server (192.168.100.108)
- [系统] up 9d | 负载 0.01-0.95（正常）
- [磁盘] / : 17% (98G, 可用 78G)
- [内存] ~1.3-1.7Gi / 3.8Gi
- [Docker] homeassistant: Up 9 days
- [服务] Gateway: running
- [更新] base-files/byobu/console-setup/containerd/docker 等常规包可升级（非紧急）

## iStoreOS 路由器 (192.168.100.1)
- [系统] up 9d | 负载 1.18-2.00（12:01 瞬时 2.00 已回落，正常）
- [磁盘] overlay /dev/sdb3: 73% (1.9G, 可用 525.5M) ← 只监控
- [服务] OpenClash: running | Tailscale: running
- [Tailscale serve] 配置存在于 _serve/e416（仅记录）

## SSL 证书
- 🟢 gateway.pem/crt: 剩余 342 天
- 共 9 个证书全部正常

## 安全邮件扫描
- 无高危事件

## 磁盘趋势
- 已采集，/ 分区 17% 稳定

## 异常与处理
- 12:01 CST 路由器 1 分钟负载瞬时冲高 2.00，30 分钟后回落至 ~1.4，无需处理

## 巡检记录
- 本日（CST 09-10 起）共 44 次巡检条目，全部正常

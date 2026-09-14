# 📊 每日巡检报告 — 2026-09-14

## Ubuntu AI Server (192.168.100.108)
- [系统] up 13d | 负载 0.36-0.59（正常）
- [磁盘] / : 22% (98G, 已用 20G, 可用 74G)（与昨日一致）
- [内存] ~1.1-1.2Gi / 3.8Gi，Swap 311Mi
- [Docker] homeassistant: Up 13 days
- [服务] Gateway: OK（health 74ms）| HA: 200

## iStoreOS 路由器 (192.168.100.1)
- [系统] up 13d | 负载 1.52-1.86（正常区间，与昨日持平）
- [磁盘] overlay /dev/sdb3: 73%（只监控，30 分钟趋势稳定）| sdb4: 8% | sda1: 29%（均在阈值内）
- [服务] OpenClash: running | Tailscale: running
- [Tailscale serve] 无配置（上次检查 9/12 有记录 `_serve/e416`，本次 `tailscale serve status` 返回 "No serve config"，已清除）

## SSL 证书
- 🟢 gateway 本地证书: 剩余 338 天（2027-08）+ 364 天（2027-09）
- 过期证书仅来自 Go 包测试数据（testdata），非生产证书，忽略

## 安全邮件扫描
- 完成（13:00 CST），无新增高危/警告事件

## 可升级包（常规更新，非紧急）
- base-files、byobu、console-setup、containerd.io、docker 系列
- 建议下轮更新窗口统一处理

## 巡检记录
- 本日（CST 09-14）21:00 晚检 1 条：全部正常，无异常

# 2026-08-31 晚检日报

## Ubuntu AI Server (192.168.100.108)
- **运行时间**: 10d 23h
- **负载**: 0.16 / 0.20 / 0.23 — 正常
- **内存**: 1.8G / 3.8G 使用，2.1G 可用
- **磁盘 /**: 17% (16G / 98G) — 正常
- **Docker**: homeassistant (Up 11 days) — 正常
- **OpenClaw Gateway**: 正常运行（3d 10h）
- **系统更新**: 无待安装更新，unattended-upgrades 正常运行
- **SSL 证书**: 全部正常（gateway 证书剩余 352 天）
- **安全邮件**: 无异常

## iStoreOS 路由器 (192.168.100.1)
- **运行时间**: 17d 3h
- **负载**: 1.20 / 1.14 / 1.10 — 正常
- **overlay (sdb3)**: 73% (1.4G / 1.9G) — 正常（阈值 80%）
- **sdb4 (/mnt/sata2-4)**: 8% (1.9G / 26.5G) — 正常
- **sda1 (/mnt/data_sata1)**: 23% (24.1G / 109.5G) — 正常
- **OpenClash**: 运行中（config.yaml 存在）
- **Tailscale**: 运行中，istoreos-1 在线；无 serve 配置
- **Docker**: 无容器运行

## 异常汇总
无异常，全部正常。

---
生成时间: 2026-08-31 21:00 CST

# 日报 — 2026-09-10（晚检 21:00 CST）

## 总览
✅ 全部设备/服务正常，无高危事件。

## Ubuntu AI Server
- **负载**: 0.15/0.10/0.09，运行 9 天 12 小时
- **内存**: 已用 1.5Gi / 3.8Gi，可用 2.3Gi，swap 几乎未用
- **磁盘**: / 17%（16G/98G，可用 78G）— 正常
- **Docker**: homeassistant Up 9 天，无停止容器
- **Gateway**: 运行正常（uptime 1 天 1 小时）
- **Home Assistant**: 在线；日志有 metno 气象源 fetch 失败（外部天气源，非本地问题）；camera.bedroom_camera idle
- **系统更新**: 有若干包可升级（base-files、byobu、console-setup、docker-ce 全家桶、containerd 等），未自动执行，保持现状
- **安全**: fail2ban 正常（日志滚动 9/6，无新增封禁记录）
- **SSL 证书**: 9 个证书全部正常，gateway 剩余 342 天，无 <30 天告警
- **磁盘趋势**: 已采集 2026-09-10 数据（config/disk-trend.json 已更新）

## iStoreOS 路由器
- **负载**: 1.84/1.46/1.28（多核软路由，正常范围）
- **磁盘**:
  - overlay (sdb3): 73% — 低于 80% 告警线，持续观察
  - sdb4 /mnt/sata2-4: 8% — 正常
  - sda1 /mnt/data_sda1: 24% — 正常
- **OpenClash**: 运行中（clash 进程 + watchdog 正常）
- **Tailscale**: tailscaled 运行中，无 serve 配置（无需提醒）
- **Docker**: 无运行容器
- **WAN**: pppoe-wan 在线，IPv6 正常

## 安全邮件
- 扫描完成，无高危/警告事件，常规静默

## 待处理事项
- overlay 分区 73% 接近 80% 告警线，建议观察增长趋势；如持续上升可分析 /overlay 占用大头
- 系统有可升级包（含 docker-ce 29.8.0），需要时告知 kami 后执行

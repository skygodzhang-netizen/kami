# 每日巡检报告 — 2026-09-15（晚检 21:00 CST）

## 总览
✅ 正常。无告警阈值触发；Tailscale serve 无配置；OpenClash 运行中；安全邮件无告警。

## Ubuntu AI Server (192.168.100.108)
- 负载: 0.07/0.06/0.14（14天+uptime）
- 内存: 3915MB total / 1348MB used / 2567MB available；swap 311MB 使用
- 磁盘 /: 98G 总量，20G 已用 (22%)
- Docker: homeassistant 容器 Up 2 weeks
- OpenClaw Gateway: active
- Home Assistant: HTTP 200（8123 端口可达，systemd 单元非活跃但容器正常）
- 安全邮件扫描: 完成，无异常
- 待更新软件: docker-ce 29.8.0、containerd.io 2.3.5、linux-firmware 等常规更新（未自动执行）

## iStoreOS (192.168.100.1)
- 负载: 1.39/1.27/1.28
- 分区:
  - /overlay (sdb3): 73%（<80% 阈值，正常）
  - /mnt/data_sda1 (sda1): 29%（<85% 阈值，正常）
  - /mnt/sata2-4 (sdb4): 8%（正常）
- OpenClash: 进程运行中（PID 21600/21601）
- Tailscale: 3 台节点，istoreos-1 在线，istoreos/zhanglihua 离线；serve 无配置

## SSL 证书
- Gateway 本地证书: 337/363 天剩余 ✅
- 4 个"已过期"证书均为 Go 模块 testdata 测试证书，非生产证书，可忽略

## 磁盘趋势
- 已采集并更新 trend 数据（2026-09-15 21:01 CST）

## 操作记录
- 执行 ssh 巡检 iStoreOS
- 运行 ssl-cert-check.sh、disk-trend-analyze.sh、security-mail-check.sh
- 本报告 + memory/2026-09-15.md 巡检条目已写入并 git push

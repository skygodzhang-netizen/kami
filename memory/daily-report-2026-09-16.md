# 每日巡检报告 — 2026-09-16（晚检 21:00 CST）

## 总览
✅ 正常。无告警阈值触发；Tailscale serve 无配置；OpenClash 运行中；安全邮件无告警。

## Ubuntu AI Server (192.168.100.108)
- 负载: 0.32/0.12/0.08（uptime 15天12小时）
- 内存: 3915MB total / 1297MB used / 2618MB available；swap 299MB 使用
- 磁盘 /: 98G 总量，20G 已用 (22%)
- Docker: homeassistant 容器 Up 2 weeks
- OpenClaw Gateway: active（18789 端口监听正常，进程 PID 190008）
- Home Assistant: HTTP 200（8123 端口可达）
- 安全邮件扫描: 完成，无异常
- 待更新软件: base-files、byobu、console-setup 等常规更新（未自动执行）

## iStoreOS (192.168.100.1)
- 负载: 1.66/1.40/1.30
- 内存: 7.9GB total / 4.7GB used
- 分区:
  - /overlay (sdb3): 73%（<80% 阈值，正常）
  - /mnt/data_sda1 (sda1): 29%（<85% 阈值，正常）
  - /mnt/sata2-4 (sdb4): 8%（正常）
- OpenClash: 进程运行中（clash + watchdog）
- Tailscale: 3 台节点，istoreos-1 在线，istoreos/zhanglihua 离线；serve 无配置

## SSL 证书
- 检测 16 个证书，4 个"已过期"均为 Go 模块 testdata 测试证书，非生产证书，可忽略
- 其余证书均在有效期内（含 /etc/pki 系统证书）

## 磁盘趋势
- 已采集并更新 trend 数据（2026-09-16 21:01 CST），与昨日数据一致（overlay 73%、sda1 29%、sdb4 8%、/ 22%），无异常增长

## 操作记录
- 执行 ssh 巡检 iStoreOS
- 运行 ssl-cert-check.sh、disk-trend-analyze.sh、security-mail-check.sh
- 本报告 + memory/2026-09-16.md 巡检条目已写入并 git push

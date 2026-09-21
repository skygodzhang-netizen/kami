# 每日巡检日报 | 2026-09-21（周一）

生成时间：2026-09-21 21:10 CST（21:00 晚检 cron）

## 总体结论

✅ 正常。无磁盘超阈、无生产证书过期、无安全邮件异常。

## Ubuntu AI Server（192.168.100.108）

| 项目 | 状态 |
|---|---|
| 负载 | 0.70 / 0.40 / 0.21（正常） |
| 内存 | 1730/3915 MB，可用 2185 MB（正常） |
| 磁盘 / | 98G，使用 22%（正常） |
| Docker | homeassistant Up 2 weeks |
| Gateway | systemd active，pid 265183，wss://127.0.0.1:18789，auth token |
| Tailscale（Ubuntu） | off |
| 系统更新 | 29 个可升级包（未自动执行；1 个 not upgraded） |

## iStoreOS 路由器（192.168.100.1）

| 项目 | 状态 |
|---|---|
| 负载 | 1.93 / 1.61 / 1.41（正常） |
| /mnt/sata2-4 (sdb4) | 26.5G，使用 8%（阈值 85%） |
| /mnt/data_sda1 (sda1) | 109.5G，使用 30%（阈值 85%） |
| OpenClash | 运行中（/etc/openclash 配置完整） |
| Tailscale | istoreos-1 在线（100.123.106.24）；istoreos、zhanglihua offline |
| Tailscale serve | **SERVE_RUNNING 存在** → 提醒确认是否保留 serve 配置 |

## SSL 证书检查（ssl-cert-check.sh）

- 共检测 16 个证书，发现 4 个"问题证书"，**全部位于 `/home/ubuntu/go/pkg/mod/` 测试目录**（googleapis enterprise-certificate-proxy、letsencrypt pebble、quic-go testdata、certificate-transparency-go testdata/invalid/*）
- 无生产/服务证书过期，不影响系统

## 磁盘趋势（disk-trend-analyze.sh）

- 趋势数据已更新：2026-09-21 21:07:52 CST
- 无分区超阈

## 安全邮件（security-mail-check.sh）

- 扫描完成，无新增异常邮件

## fail2ban / SSH（security-report-2026-09-21.md）

- fail2ban not running，no bans
- 最近 24h SSH 登录全部来自 192.168.100.109 公钥（正常内网节点）

## 建议

1. apt 有 29 个可升级包，周末/低峰窗口安排一次升级（含 1 个 not upgraded 需手动确认）
2. iStoreOS Tailscale serve 配置存在，若非必要暴露端口建议移除或保留策略说明
3. istoreos、zhanglihua 两台 Tailscale 节点离线，如需可达性请检查

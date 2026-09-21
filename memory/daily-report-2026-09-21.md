# 每日巡检日报 | 2026-09-21（周一）

生成时间：2026-09-21 21:15 CST（21:00 晚检 cron）

## 总体结论

✅ 正常。无磁盘超阈、无生产证书过期、无安全邮件异常。

## Ubuntu AI Server（192.168.100.108）

| 项目 | 状态 |
|---|---|
| 负载 | 0.70 / 0.56 / 0.33（正常） |
| 内存 | 1.8Gi/3.8Gi，可用 2.0Gi（正常） |
| 磁盘 / | 98G，使用 22%（正常） |
| Docker | homeassistant Up 2 weeks |
| Gateway | 端口 18789 监听中（MainThread, pid 265183） |
| Home Assistant | :8123 返回 200 |
| 系统更新 | 29 个可升级包（未自动执行；1 个 not upgraded） |

## iStoreOS 路由器（192.168.100.1）

| 项目 | 状态 |
|---|---|
| 负载 | 1.85 / 1.78 / 1.54（正常） |
| /mnt/sata2-4 (sdb4) | 26.5G，使用 8%（阈值 85%） |
| /mnt/data_sda1 (sda1) | 109.5G，使用 30%（阈值 85%） |
| OpenClash | clash 运行中（pid 775） |
| Tailscale | istoreos-1 在线（100.123.106.24）；istoreos、zhanglihua offline |
| Tailscale serve | 配置存在（tailscale0 UP）→ 提醒确认是否保留 serve 配置 |

## SSL 证书检查（ssl-cert-check.sh）

- 共检测 16 个证书，发现 4 个"问题证书"，**全部位于 `/home/ubuntu/go/pkg/mod/` 测试目录**（chi testdata/cert.pem、certificate-transparency-go x509 testdata/invalid/*）
- 无生产/服务证书过期，不影响系统

## 磁盘趋势（disk-trend-analyze.sh）

- 趋势数据已更新：2026-09-21 21:12:01 CST
- 无分区超阈

## 安全邮件（security-mail-check.sh）

- 扫描完成，无新增异常邮件

## 建议

1. apt 有 29 个可升级包，周末/低峰窗口安排一次升级（含 1 个 not upgraded 需手动确认）
2. iStoreOS Tailscale serve 配置存在，若非必要暴露端口建议移除或保留策略说明
3. istoreos、zhanglihua 两台 Tailscale 节点离线，如需可达性请检查

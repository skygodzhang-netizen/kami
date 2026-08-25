# 日报 — 2026-08-24 (周一)

## Ubuntu AI Server (192.168.100.108)

| 项目 | 状态 | 详情 |
|------|------|------|
| 负载 | ✅ | 0.25/0.24/0.14 |
| 内存 | ✅ | 1.7G/3.8G (45%), 可用 2.1G |
| 磁盘 / | ✅ | 16G/98G (17%) |
| Docker | ✅ | homeassistant: Up 4 days |
| OpenClaw Gateway | ✅ | active (running), 端口 18789 |
| 系统更新 | ⚠️ | 6 个包可升级 (console-setup, open-vm-tools, snapd) |
| 安全日志 | ✅ | 无异常登录，无 fail2ban 记录 |
| SSL 证书 | ✅ | gateway 证书剩余 359 天 |
| systemd-analyze | ℹ️ | caddy.service EXPOSED (8.8), 其余正常 |

### 磁盘趋势
- `/` 保持稳定 17% (近7日: 16-17%)
- 无异常增长

### 安全邮件
- ✅ 无新安全警报
- 所有发现均为历史邮件 (2026年5-7月)
- GitHub 5条历史 warning，Bybit/Google 历史警告

---

## iStoreOS 路由器 (192.168.100.1)

| 项目 | 状态 | 详情 |
|------|------|------|
| 系统 | ✅ | iStoreOS 24.10.7, Pentium J4205 |
| 负载 | ✅ | 1.04/0.99/1.00 (4核满载正常) |
| 内存 | ✅ | 约 59% (4.7G/7.9G) |
| overlay | ✅ | 72% (1.4G/1.9G) — 低于 80% 阈值 |
| sdb4 | ✅ | 8% (1.9G/26.5G) |
| sda1 | ✅ | 23% (23.9G/109.5G) |
| OpenClash | ✅ | 运行中 (v0.47.156) |
| Tailscale | ✅ | 运行中 (v1.80.3-r1), 1 设备在线 |
| Tailscale serve | ✅ | 无 serve 配置 |
| WAN | ✅ | IPv4: 118.163.198.14 |
| 内网设备 | ✅ | 19 台设备在线 |
| 日志 | ⚠️ | logread/libubox 多次 segfault (已知问题，非关键) |

---

## 总体评估

- **整体状态**: 🟢 健康
- **告警**: 无
- **需关注**: 
  1. 6 个 Ubuntu 包可升级（非紧急）
  2. iStoreOS logread segfault（已知问题，不影响路由功能）
- **Tailscale serve**: 未检测到 serve 配置，无需提醒

---

_报告生成时间: 2026-08-24 21:02 CST_
